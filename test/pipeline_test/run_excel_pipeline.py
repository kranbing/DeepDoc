from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any, Dict

from ocr_pipeline.excel_adapter import OpenpyxlExcelAdapter
from ocr_pipeline.excel_postprocess import ExcelChunker, ExcelChunkerConfig, evaluate_excel_chunk_quality


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Excel parsing pipeline for QA-friendly chunks")
    parser.add_argument("--input", required=True, help="Input .xlsx file path")
    parser.add_argument("--output-dir", default="./output/pipeline_excel", help="Output directory")
    parser.add_argument("--doc-id", default=None, help="Optional document id")
    parser.add_argument("--max-rows-per-chunk", type=int, default=20, help="Maximum rows in each chunk")
    parser.add_argument("--header-search-rows", type=int, default=6, help="Rows used for header inference")
    return parser.parse_args()


def main() -> int:
    args = build_args()

    source = Path(args.input).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}")

    doc_id = args.doc_id or f"excel_{uuid.uuid4().hex[:10]}"
    out_dir = Path(args.output_dir).resolve() / doc_id
    out_dir.mkdir(parents=True, exist_ok=True)

    adapter = OpenpyxlExcelAdapter(data_only=True)
    sheet_payloads = adapter.parse_workbook(source)

    chunker = ExcelChunker(
        ExcelChunkerConfig(
            max_rows_per_chunk=max(1, args.max_rows_per_chunk),
            header_search_rows=max(1, args.header_search_rows),
        )
    )
    chunks = chunker.chunk_workbook(sheet_payloads, doc_id=doc_id)
    quality = evaluate_excel_chunk_quality(chunks)

    result: Dict[str, Any] = {
        "doc_id": doc_id,
        "source": str(source),
        "source_type": "xlsx",
        "sheet_count": len(sheet_payloads),
        "sheets": [
            {
                "sheet_name": sheet.get("sheet_name"),
                "sheet_index": sheet.get("sheet_index"),
                "n_rows": sheet.get("n_rows"),
                "n_cols": sheet.get("n_cols"),
                "merged_ranges": sheet.get("merged_ranges"),
            }
            for sheet in sheet_payloads
        ],
        "chunks": chunks,
        "quality": quality,
    }

    out_file = out_dir / "excel_pipeline_result.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
