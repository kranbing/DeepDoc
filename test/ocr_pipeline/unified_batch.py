from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .excel_adapter import OpenpyxlExcelAdapter
from .excel_postprocess import ExcelChunker, ExcelChunkerConfig, evaluate_excel_chunk_quality
from .input_loader import IMAGE_EXTENSIONS
from .logger import setup_logger, setup_status_event_logger
from .runner import run_pipeline
from .types import PipelineResult


EXCEL_EXTENSIONS = {".xlsx"}
DOC_EXTENSIONS = {".doc", ".docx"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | EXCEL_EXTENSIONS | DOC_EXTENSIONS | PDF_EXTENSIONS

STATUS_QUEUED = "queued"
STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_FAILED = "failed"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_rel_path(path: Path, base_dir: Path) -> str:
    try:
        rel = path.resolve().relative_to(base_dir.resolve())
        return str(rel).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def detect_source_format(path: Path) -> Optional[str]:
    suffix = path.suffix.lower()
    if suffix in PDF_EXTENSIONS:
        return "pdf"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in EXCEL_EXTENSIONS:
        return "xlsx"
    if suffix in DOC_EXTENSIONS:
        return "docx"
    return None


def list_all_files(input_path: Path, recurse: bool) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.is_dir():
        return []
    iterator = input_path.rglob("*") if recurse else input_path.glob("*")
    return sorted([item for item in iterator if item.is_file()])


def is_transient_file(path: Path) -> bool:
    name = path.name
    return name.startswith("~$") or name.endswith(".tmp")


def list_supported_files(input_path: Path, recurse: bool) -> List[Path]:
    all_files = list_all_files(input_path, recurse)
    return [
        item
        for item in all_files
        if item.suffix.lower() in SUPPORTED_EXTENSIONS and not is_transient_file(item)
    ]


def build_doc_id(source_path: Path, source_format: str) -> str:
    stem = re.sub(r"[^0-9A-Za-z_]+", "_", source_path.stem).strip("_")
    stem = stem or "doc"
    return f"{source_format}_{stem[:40]}_{uuid.uuid4().hex[:8]}"


def find_office_binary() -> Optional[str]:
    for name in ("soffice", "libreoffice"):
        binary = shutil.which(name)
        if binary:
            return binary
    return None


def convert_doc_to_pdf(source_path: Path, output_dir: Path) -> Path:
    office_binary = find_office_binary()
    if not office_binary:
        raise RuntimeError("LibreOffice is required for DOC/DOCX conversion (missing soffice/libreoffice)")

    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        office_binary,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(source_path),
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=240)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"DOCX conversion failed: {detail[:500]}")

    expected = output_dir / f"{source_path.stem}.pdf"
    if expected.is_file():
        return expected

    generated = sorted(output_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if generated:
        return generated[0]
    raise RuntimeError("DOCX conversion failed: no PDF generated")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def ocr_chunks_to_unified(result: PipelineResult, source_format: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for page in result.pages:
        for block in page.blocks:
            content = str(block.content or "").strip()
            if not content:
                continue
            chunk_id = f"{result.doc_id}_p{int(page.page):04d}_b{int(block.index):04d}"
            out.append(
                {
                    "chunkId": chunk_id,
                    "docId": result.doc_id,
                    "sourceFormat": source_format,
                    "label": str(block.label or "text"),
                    "content": content,
                    "pageNo": int(page.page),
                    "bbox2d": block.bbox_2d,
                    "meta": {
                        "blockIndex": int(block.index),
                        "qualityScore": round(float(page.quality_score), 4),
                        "structureScore": round(float(page.structure_score), 4),
                        "finalScore": round(float(page.final_score), 4),
                    },
                }
            )
    return out


def excel_chunks_to_unified(doc_id: str, source_format: str, chunks: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            continue
        content = str(chunk.get("content") or chunk.get("text") or "").strip()
        if not content:
            continue
        chunk_id = str(chunk.get("chunk_id") or f"{doc_id}_excel_{idx:04d}")
        out.append(
            {
                "chunkId": chunk_id,
                "docId": doc_id,
                "sourceFormat": source_format,
                "label": str(chunk.get("label") or "excel_table"),
                "content": content,
                "sheet": str(chunk.get("sheet") or ""),
                "range": str(chunk.get("range") or ""),
                "bbox2d": chunk.get("bbox_2d"),
                "meta": {
                    "sheetIndex": int(chunk.get("sheet_index") or 0),
                    "headerRow": int(chunk.get("header_row") or 0),
                    "rowCount": int((chunk.get("structure") or {}).get("row_count") or 0),
                    "colCount": int((chunk.get("structure") or {}).get("col_count") or 0),
                },
            }
        )
    return out


@dataclass
class UnifiedBatchConfig:
    input_path: str
    output_dir: str = "./output/pipeline_unified"
    batch_id: Optional[str] = None
    recurse: bool = False
    continue_on_error: bool = False

    mode: str = "maas"
    api_key: Optional[str] = None
    config_path: Optional[str] = None
    env_file: Optional[str] = None
    enable_mock_fallback: bool = False
    mock_noisy: bool = False

    score_threshold: float = 0.7
    final_score_threshold: float = 0.85
    structure_score_threshold: float = 0.8
    quality_weight: float = 0.7
    structure_weight: float = 0.3
    max_retries: int = 3
    pdf_dpi: int = 200
    retry_pdf_dpi: int = 280
    no_viz: bool = False

    max_rows_per_chunk: int = 20
    header_search_rows: int = 6


def process_single_document(
    *,
    source_path: Path,
    source_format: str,
    doc_id: str,
    run_dir: Path,
    config: UnifiedBatchConfig,
    logger_name: str,
) -> Dict[str, Any]:
    log_dir = run_dir / "logs"
    logger = setup_logger(log_dir, name=logger_name, file_name="batch.log")
    status_logger = setup_status_event_logger(log_dir)
    start_ts = utc_now()
    start_perf = time.perf_counter()

    entry: Dict[str, Any] = {
        "docId": doc_id,
        "sourcePath": str(source_path.resolve()),
        "sourceFormat": source_format,
        "status": STATUS_QUEUED,
        "startedAt": start_ts,
        "endedAt": None,
        "durationSec": 0.0,
        "chunkCount": 0,
        "qualitySummary": {},
        "artifacts": {},
        "error": None,
    }
    status_logger.log_event(
        doc_id=doc_id,
        status=STATUS_QUEUED,
        stage="dispatch",
        source_format=source_format,
        message="document queued",
    )
    entry["status"] = STATUS_PROCESSING
    status_logger.log_event(
        doc_id=doc_id,
        status=STATUS_PROCESSING,
        stage="dispatch",
        source_format=source_format,
        message="document processing started",
    )

    try:
        unified_chunks: List[Dict[str, Any]]

        if source_format in {"pdf", "image"}:
            status_logger.log_event(
                doc_id=doc_id,
                status=STATUS_PROCESSING,
                stage="ocr",
                source_format=source_format,
                message="starting OCR pipeline",
            )
            ocr_output_dir = run_dir / "ocr"
            result = run_pipeline(
                input_path=str(source_path),
                output_dir=str(ocr_output_dir),
                doc_id=doc_id,
                mode=config.mode,
                api_key=config.api_key,
                config_path=config.config_path,
                env_file=config.env_file,
                enable_mock_fallback=config.enable_mock_fallback,
                mock_noisy=config.mock_noisy,
                score_threshold=config.score_threshold,
                final_score_threshold=config.final_score_threshold,
                structure_score_threshold=config.structure_score_threshold,
                quality_weight=config.quality_weight,
                structure_weight=config.structure_weight,
                max_retries=config.max_retries,
                pdf_dpi=config.pdf_dpi,
                retry_pdf_dpi=config.retry_pdf_dpi,
                no_viz=config.no_viz,
            )
            result_file = ocr_output_dir / doc_id / "pipeline_result.json"
            unified_chunks = ocr_chunks_to_unified(result, source_format)
            entry["qualitySummary"] = {
                "avgFinalScore": float(result.stats.get("avg_score") or 0.0),
                "avgQualityScore": float(result.stats.get("avg_quality_score") or 0.0),
                "avgStructureScore": float(result.stats.get("avg_structure_score") or 0.0),
                "retryTimes": int(result.stats.get("retry_times") or 0),
                "pageCount": int(result.stats.get("pages") or 0),
            }
            entry["artifacts"]["rawResult"] = to_rel_path(result_file, run_dir)

        elif source_format == "xlsx":
            status_logger.log_event(
                doc_id=doc_id,
                status=STATUS_PROCESSING,
                stage="excel",
                source_format=source_format,
                message="starting Excel chunk pipeline",
            )
            excel_output_dir = run_dir / "excel" / doc_id
            excel_output_dir.mkdir(parents=True, exist_ok=True)
            adapter = OpenpyxlExcelAdapter(data_only=True)
            sheet_payloads = adapter.parse_workbook(source_path)
            chunker = ExcelChunker(
                ExcelChunkerConfig(
                    max_rows_per_chunk=max(1, int(config.max_rows_per_chunk)),
                    header_search_rows=max(1, int(config.header_search_rows)),
                )
            )
            chunks = chunker.chunk_workbook(sheet_payloads, doc_id=doc_id)
            quality = evaluate_excel_chunk_quality(chunks)

            result_payload = {
                "doc_id": doc_id,
                "source": str(source_path.resolve()),
                "source_type": "xlsx",
                "sheet_count": len(sheet_payloads),
                "chunks": chunks,
                "quality": quality,
            }
            result_file = excel_output_dir / "excel_pipeline_result.json"
            write_json(result_file, result_payload)

            unified_chunks = excel_chunks_to_unified(doc_id, source_format, chunks)
            entry["qualitySummary"] = {
                "avgFinalScore": float(quality.get("score") or 0.0),
                "sheetCount": int(len(sheet_payloads)),
                "issues": quality.get("issues") if isinstance(quality.get("issues"), list) else [],
            }
            entry["artifacts"]["rawResult"] = to_rel_path(result_file, run_dir)

        elif source_format == "docx":
            status_logger.log_event(
                doc_id=doc_id,
                status=STATUS_PROCESSING,
                stage="docx_convert",
                source_format=source_format,
                message="starting DOCX to PDF conversion",
            )
            converted_dir = run_dir / "converted" / doc_id
            converted_pdf = convert_doc_to_pdf(source_path, converted_dir)
            entry["artifacts"]["convertedPdf"] = to_rel_path(converted_pdf, run_dir)

            status_logger.log_event(
                doc_id=doc_id,
                status=STATUS_PROCESSING,
                stage="ocr",
                source_format=source_format,
                message="DOCX conversion complete, starting OCR pipeline",
            )
            ocr_output_dir = run_dir / "ocr"
            result = run_pipeline(
                input_path=str(converted_pdf),
                output_dir=str(ocr_output_dir),
                doc_id=doc_id,
                mode=config.mode,
                api_key=config.api_key,
                config_path=config.config_path,
                env_file=config.env_file,
                enable_mock_fallback=config.enable_mock_fallback,
                mock_noisy=config.mock_noisy,
                score_threshold=config.score_threshold,
                final_score_threshold=config.final_score_threshold,
                structure_score_threshold=config.structure_score_threshold,
                quality_weight=config.quality_weight,
                structure_weight=config.structure_weight,
                max_retries=config.max_retries,
                pdf_dpi=config.pdf_dpi,
                retry_pdf_dpi=config.retry_pdf_dpi,
                no_viz=config.no_viz,
            )
            result_file = ocr_output_dir / doc_id / "pipeline_result.json"
            unified_chunks = ocr_chunks_to_unified(result, source_format)
            entry["qualitySummary"] = {
                "avgFinalScore": float(result.stats.get("avg_score") or 0.0),
                "avgQualityScore": float(result.stats.get("avg_quality_score") or 0.0),
                "avgStructureScore": float(result.stats.get("avg_structure_score") or 0.0),
                "retryTimes": int(result.stats.get("retry_times") or 0),
                "pageCount": int(result.stats.get("pages") or 0),
            }
            entry["artifacts"]["rawResult"] = to_rel_path(result_file, run_dir)

        else:
            raise ValueError(f"unsupported source format: {source_format}")

        chunks_file = run_dir / "unified_chunks.jsonl"
        append_jsonl(chunks_file, unified_chunks)
        entry["artifacts"]["unifiedChunks"] = to_rel_path(chunks_file, run_dir)
        entry["chunkCount"] = len(unified_chunks)
        entry["status"] = STATUS_DONE
        status_logger.log_event(
            doc_id=doc_id,
            status=STATUS_DONE,
            stage="index",
            source_format=source_format,
            message="document indexed",
            payload={"chunkCount": len(unified_chunks)},
        )
    except Exception as exc:
        logger.exception("process document failed: doc_id=%s source=%s", doc_id, source_path)
        entry["status"] = STATUS_FAILED
        entry["error"] = str(exc)
        status_logger.log_event(
            doc_id=doc_id,
            status=STATUS_FAILED,
            stage="error",
            source_format=source_format,
            message="document processing failed",
            payload={"error": str(exc)},
        )

    entry["endedAt"] = utc_now()
    entry["durationSec"] = round(time.perf_counter() - start_perf, 4)
    return entry


def run_unified_batch(config: UnifiedBatchConfig) -> Dict[str, Any]:
    input_path = Path(config.input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"input path not found: {input_path}")

    run_id = config.batch_id or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    run_dir = (Path(config.output_dir).resolve() / run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    log_dir = run_dir / "logs"
    logger_name = f"unified_batch_{run_id}"
    logger = setup_logger(log_dir, name=logger_name, file_name="batch.log")

    all_files = list_all_files(input_path, config.recurse)
    source_files = list_supported_files(input_path, config.recurse)
    unsupported_files = [
        str(path.resolve())
        for path in all_files
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS or is_transient_file(path)
    ]

    if not source_files:
        raise RuntimeError("no supported files found in input path")

    logger.info("batch start run_id=%s input=%s files=%s", run_id, input_path, len(source_files))

    documents: List[Dict[str, Any]] = []
    aborted = False
    for source_path in source_files:
        source_format = detect_source_format(source_path)
        if not source_format:
            continue
        doc_id = build_doc_id(source_path, source_format)
        entry = process_single_document(
            source_path=source_path,
            source_format=source_format,
            doc_id=doc_id,
            run_dir=run_dir,
            config=config,
            logger_name=logger_name,
        )
        documents.append(entry)
        if entry.get("status") == STATUS_FAILED and not config.continue_on_error:
            aborted = True
            logger.warning("batch aborted due to first failure: doc_id=%s", doc_id)
            break

    done_count = sum(1 for item in documents if item.get("status") == STATUS_DONE)
    failed_count = sum(1 for item in documents if item.get("status") == STATUS_FAILED)
    summary = {
        "totalScannedFiles": len(all_files),
        "totalSupportedFiles": len(source_files),
        "processed": len(documents),
        "done": done_count,
        "failed": failed_count,
        "aborted": aborted,
        "unsupportedCount": len(unsupported_files),
    }

    payload = {
        "_comment": "Unified multi-format indexing result for offline batch processing.",
        "generatedAt": utc_now(),
        "runId": run_id,
        "inputPath": str(input_path),
        "statusModel": [STATUS_QUEUED, STATUS_PROCESSING, STATUS_DONE, STATUS_FAILED],
        "summary": summary,
        "artifacts": {
            "batchLog": "logs/batch.log",
            "statusEvents": "logs/status_events.jsonl",
            "unifiedChunks": "unified_chunks.jsonl",
        },
        "unsupportedFiles": unsupported_files,
        "documents": documents,
    }

    out_file = run_dir / "unified_index.json"
    write_json(out_file, payload)
    logger.info("batch end run_id=%s done=%s failed=%s output=%s", run_id, done_count, failed_count, out_file)
    return payload
