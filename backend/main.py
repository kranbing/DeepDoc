"""
DeepDOC 本地后端：项目目录、工作区状态持久化、静态站点。

GLM-OCR 默认走本地自托管（连接 Docker 内 vLLM 等），环境变量示例：
  GLMOCR_MODE=selfhosted（可省略）
  GLMOCR_OCR_API_HOST=127.0.0.1
  GLMOCR_OCR_API_PORT=8080
使用智谱云端时：GLMOCR_MODE=maas，并设置 ZHIPU_API_KEY。

运行（仓库根目录）:
  pip install -r backend/requirements.txt
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.logging_config import logger
from backend.ocr_quality import evaluate_ocr_quality
from backend.rag.config import RAG_TOP_K
from backend.rag.service import ask_rag_with_selection, build_rag_context
from backend.services.chunk_store import (
    chunk_page_summary,
    flatten_document_chunks,
    get_chunk_detail,
    get_neighbor_chunks,
    get_page_chunks,
    save_document_chunks,
)
from backend.services.overview_service import ensure_document_overview, upsert_document_overview
from backend.services.project_store import (
    delete_document_directory,
    default_documents_index,
    documents_index_path,
    read_document_overview,
    remove_document_from_index,
    write_document_quality_report,
    write_json as write_data_json,
    write_documents_index,
)
from backend.services.qa_service import (
    dedupe_chunk_items,
    ensure_doc_chunks_ready,
    expand_selected_with_neighbors,
    normalize_chunk_context_items,
    serialize_chunk_context_payload,
    session_context_summary,
)
from backend.services.session_service import (
    append_qa_turn,
    compact_session_if_needed,
    create_session,
    default_qa_compactions_state,
    default_qa_sessions_state,
    ensure_active_session,
    get_session,
    list_doc_sessions,
    read_qa_compactions,
    read_qa_sessions,
    serialize_session,
    session_recent_turns,
    write_qa_compactions,
    write_qa_sessions,
)
from backend.services.vector_store import (
    delete_doc_from_vector_index,
    read_vector_manifest,
    rebuild_project_vector_index,
    search_project_vector_index,
    update_project_vector_index,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_PROJECTS = ROOT / "data" / "projects"
WEB_DIR = ROOT / "web"



def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_project_layout(project_id: str) -> Path:
    """创建项目目录：对话、上传 PDF/数据库、输出等。"""
    p = DATA_PROJECTS / project_id
    (p / "conversations").mkdir(parents=True, exist_ok=True)
    (p / "conversations" / "sessions").mkdir(parents=True, exist_ok=True)
    (p / "documents").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "pdfs").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "pdf_pages").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "ocr_blocks").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "databases").mkdir(parents=True, exist_ok=True)
    (p / "outputs").mkdir(parents=True, exist_ok=True)
    return p


def default_workspace_state() -> Dict[str, Any]:
    return {
        "threads": {},
        "dbThreads": {},
        "docs": [],
        "databases": [],
        "artifacts": [],
        "selectedDocId": None,
        "selectedDbId": None,
        "selectedArtifactId": None,
        "viewMode": "document",
    }


def default_now_conversation_state() -> Dict[str, Any]:
    return {
        "selectedItems": [],
        "activeDocId": None,
        "activeSessionId": None,
        "updatedAt": _utc_now(),
    }


def read_meta(project_dir: Path) -> Optional[Dict[str, Any]]:
    meta_path = project_dir / "meta.json"
    if not meta_path.is_file():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def read_workspace(project_dir: Path) -> Dict[str, Any]:
    path = project_dir / "conversations" / "workspace_state.json"
    if not path.is_file():
        return default_workspace_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        base = default_workspace_state()
        base.update(data)
        return base
    except json.JSONDecodeError:
        return default_workspace_state()


def write_workspace(project_dir: Path, state: Dict[str, Any]) -> None:
    path = project_dir / "conversations" / "workspace_state.json"
    write_data_json(path, state)


def read_now_conversation(project_dir: Path) -> Dict[str, Any]:
    path = project_dir / "conversations" / "now_conversation.json"
    if not path.is_file():
        return default_now_conversation_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        base = default_now_conversation_state()
        if isinstance(data, dict):
            if isinstance(data.get("selected"), dict) and not isinstance(data.get("selectedItems"), list):
                data["selectedItems"] = [data["selected"]]
            base.update(data)
        return base
    except json.JSONDecodeError:
        return default_now_conversation_state()


def write_now_conversation(project_dir: Path, state: Dict[str, Any]) -> None:
    path = project_dir / "conversations" / "now_conversation.json"
    state = dict(state)
    state["updatedAt"] = _utc_now()
    write_data_json(path, state)


def _workspace_doc_or_404(project_dir: Path, doc_id: str) -> Dict[str, Any]:
    ws = read_workspace(project_dir)
    docs = ws.get("docs") if isinstance(ws.get("docs"), list) else []
    doc = next((d for d in docs if isinstance(d, dict) and d.get("id") == doc_id), None)
    if not isinstance(doc, dict):
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


def _safe_pdf_doc_id(doc_id: str) -> bool:
    return bool(re.match(r"^pdf_[a-f0-9]{8}$", doc_id))


def _safe_page_png(filename: str) -> bool:
    return bool(re.match(r"^page_\d{4}\.png$", filename))


def _safe_ocr_parsed_image(filename: str) -> bool:
    """解析输出：版面可视化 ``page_0001.jpg``；兼容分块 ``p0001_b000.png`` 与 ``page_0001.png``。"""
    return bool(
        re.match(r"^page_\d{4}\.(png|jpg|jpeg)$", filename, re.IGNORECASE)
        or re.match(r"^p\d{4}_b\d{3}\.png$", filename)
    )


_glm_ocr_parser: Any = None
_glm_ocr_parser_mode: Optional[str] = None


def _glm_ocr_use_maas() -> bool:
    """默认本地自托管（Docker vLLM）；仅当 GLMOCR_MODE=maas 时使用智谱云端 API。"""
    m = (os.environ.get("GLMOCR_MODE") or "selfhosted").strip().lower()
    return m in ("maas", "cloud", "zhipu", "api")


def _ensure_glmocr_importable() -> None:
    try:
        import glmocr  # noqa: F401
        return
    except ImportError:
        pass
    glm_root = ROOT / "GLM-OCR-0.1.4"
    if glm_root.is_dir():
        p = str(glm_root.resolve())
        if p not in sys.path:
            sys.path.insert(0, p)
    import glmocr  # noqa: F401


def _glmocr_api_key() -> Optional[str]:
    key = (os.environ.get("ZHIPU_API_KEY") or os.environ.get("GLMOCR_API_KEY") or "").strip()
    if key:
        return key
    for filename in (".glmocr_api_key", ".zhipu_api_key"):
        local = ROOT / "backend" / filename
        if not local.is_file():
            continue
        try:
            txt = local.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if txt:
            return txt
    return None


def get_glm_ocr_parser() -> Any:
    """懒加载 GlmOcr。

    - 默认 ``GLMOCR_MODE=selfhosted``：连接本机 OCR 服务（常见为 Docker 内 vLLM，
      地址见 ``GLMOCR_OCR_API_HOST`` / ``GLMOCR_OCR_API_PORT``，默认 127.0.0.1:8080）。
    - ``GLMOCR_MODE=maas``：使用智谱云端，需 ``ZHIPU_API_KEY`` 或 ``GLMOCR_API_KEY``。
    """
    global _glm_ocr_parser, _glm_ocr_parser_mode
    api_key = _glmocr_api_key()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="缺少 GLM-OCR API Key，请设置 ZHIPU_API_KEY / GLMOCR_API_KEY，或写入 backend/.glmocr_api_key。",
        )
    try:
        _ensure_glmocr_importable()
        from glmocr import GlmOcr
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="未安装 GLM-OCR SDK：在仓库根目录执行 pip install -r backend/requirements.txt",
        ) from e

    mode_key = "maas"
    if _glm_ocr_parser is None or _glm_ocr_parser_mode != mode_key:
        if _glm_ocr_parser is not None:
            try:
                _glm_ocr_parser.close()
            except Exception:
                pass
            _glm_ocr_parser = None
        _glm_ocr_parser = GlmOcr(mode="maas", api_key=api_key)
        _glm_ocr_parser_mode = mode_key
    return _glm_ocr_parser


def _layout_page_sort_key(path: Path) -> int:
    m = re.search(r"layout_page(\d+)", path.name, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _json_regions_to_vis_boxes(
    regions: List[Dict[str, Any]], width: int, height: int
) -> List[Dict[str, Any]]:
    """将 ``json_result`` 单页 region（bbox_2d 为 0–1000）转为 ``draw_layout_boxes`` 所需格式。"""
    boxes: List[Dict[str, Any]] = []
    for r in regions:
        bb = r.get("bbox_2d")
        if not bb or len(bb) != 4:
            continue
        x1, y1, x2, y2 = (float(t) for t in bb)
        boxes.append(
            {
                "coordinate": [
                    int(x1 * width / 1000),
                    int(y1 * height / 1000),
                    int(x2 * width / 1000),
                    int(y2 * height / 1000),
                ],
                "label": str(r.get("label", "text")),
                "score": 1.0,
            }
        )
    return boxes


def _json_regions_to_chunks(
    regions: List[Dict[str, Any]], width: int, height: int, page_no: int
) -> List[Dict[str, Any]]:
    """将 ``json_result`` 单页 region 转成前端可直接叠加的 chunk 数据。"""
    chunks: List[Dict[str, Any]] = []
    for fallback_index, region in enumerate(regions):
        bb = region.get("bbox_2d")
        if not bb or len(bb) != 4:
            continue
        try:
            x1, y1, x2, y2 = (float(t) for t in bb)
        except (TypeError, ValueError):
            continue

        x1 = max(0.0, min(1000.0, x1))
        y1 = max(0.0, min(1000.0, y1))
        x2 = max(0.0, min(1000.0, x2))
        y2 = max(0.0, min(1000.0, y2))
        if x2 <= x1 or y2 <= y1:
            continue

        index = region.get("index")
        if not isinstance(index, int):
            index = fallback_index

        px_box = {
            "x1": int(round(x1 * width / 1000.0)),
            "y1": int(round(y1 * height / 1000.0)),
            "x2": int(round(x2 * width / 1000.0)),
            "y2": int(round(y2 * height / 1000.0)),
        }
        chunks.append(
            {
                "chunkId": f"p{page_no:04d}_c{index:03d}",
                "index": index,
                "pageNo": page_no,
                "label": str(region.get("label", "text")),
                "content": str(region.get("content") or "").strip(),
                "bboxNorm": {
                    "x1": round(x1 / 1000.0, 6),
                    "y1": round(y1 / 1000.0, 6),
                    "x2": round(x2 / 1000.0, 6),
                    "y2": round(y2 / 1000.0, 6),
                },
                "bboxPx": px_box,
            }
        )
    chunks.sort(key=lambda item: (int(item.get("pageNo", 0)), int(item.get("index", 0))))
    return chunks


def glm_ocr_parse_to_layout_vis_pages(
    pdf_path: Path,
    page_images_dir: Path,
    out_dir: Path,
    parser: Any,
) -> List[Dict[str, Any]]:
    """调用 GLM-OCR 解析 PDF；每页输出一张版面可视化图（与 SDK ``layout_vis`` 示例一致）。"""
    import numpy as np
    import requests
    from PIL import Image

    from glmocr.utils.visualization_utils import save_layout_visualization

    if out_dir.exists():
        shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    use_maas = bool(getattr(parser, "_use_maas", False))
    if use_maas:
        result = parser.parse(
            str(pdf_path.resolve()),
            save_layout_visualization=True,
            need_layout_visualization=True,
            return_crop_images=False,
        )
    else:
        result = parser.parse(
            str(pdf_path.resolve()),
            save_layout_visualization=True,
        )
    err = getattr(result, "_error", None)
    if err:
        raise RuntimeError(str(err))

    raw_json = getattr(result, "json_result", None)
    json_pages: List[Any] = raw_json if isinstance(raw_json, list) else []

    page_pngs = sorted(page_images_dir.glob("page_*.png"))
    if not page_pngs:
        raise RuntimeError("缺少 PDF 页面 PNG，请重新上传该文档。")

    vis_dir = getattr(result, "layout_vis_dir", None)
    layout_indices = getattr(result, "layout_image_indices", None)

    # 1) 自托管：从临时目录复制 layout_page{N}.jpg（与官方 layout_vis 同源）
    layout_sources: List[Optional[Path]] = []
    if vis_dir and Path(vis_dir).is_dir():
        if layout_indices is not None:
            for idx in layout_indices:
                found: Optional[Path] = None
                for ext in (".jpg", ".jpeg", ".png"):
                    cand = Path(vis_dir) / f"layout_page{idx}{ext}"
                    if cand.is_file():
                        found = cand
                        break
                layout_sources.append(found)
        else:
            layout_sources = [
                p
                for p in sorted(
                    Path(vis_dir).glob("layout_page*"),
                    key=_layout_page_sort_key,
                )
                if p.suffix.lower() in (".jpg", ".jpeg", ".png")
            ]

    # 2) 云端：若返回可视化 URL 列表，按页下载
    maas_vis = getattr(result, "_layout_visualization", None)
    maas_urls: List[str] = []
    if use_maas and isinstance(maas_vis, list):
        for item in maas_vis:
            if isinstance(item, str) and item.startswith(("http://", "https://")):
                maas_urls.append(item)
            elif isinstance(item, dict):
                u = item.get("url") or item.get("image_url")
                if isinstance(u, str) and u.startswith(("http://", "https://")):
                    maas_urls.append(u)

    ocr_blocks_by_page: List[Dict[str, Any]] = []
    for page_idx, page_png_path in enumerate(page_pngs):
        m = re.match(r"^page_(\d{4})\.png$", page_png_path.name)
        if not m:
            continue
        page_no = int(m.group(1))
        with Image.open(page_png_path) as page_img:
            w, h = page_img.size
        done = False
        out_name = f"page_{page_no:04d}.jpg"
        out_path = out_dir / out_name

        if page_idx < len(layout_sources) and layout_sources[page_idx] is not None:
            src = layout_sources[page_idx]
            ext = src.suffix.lower()
            if ext in (".jpg", ".jpeg"):
                out_name = f"page_{page_no:04d}.jpg"
            else:
                out_name = f"page_{page_no:04d}.png"
            out_path = out_dir / out_name
            shutil.copy2(src, out_path)
            done = True
        elif page_idx < len(maas_urls):
            try:
                r = requests.get(maas_urls[page_idx], timeout=120)
                r.raise_for_status()
                out_path.write_bytes(r.content)
                done = True
            except Exception:
                done = False
                out_name = f"page_{page_no:04d}.jpg"
                out_path = out_dir / out_name

        page_chunks: List[Dict[str, Any]] = []
        if page_idx < len(json_pages):
            jp = json_pages[page_idx]
            if isinstance(jp, list):
                page_chunks = _json_regions_to_chunks(
                    [r for r in jp if isinstance(r, dict)], w, h, page_no
                )

        if not done:
            img = Image.open(page_png_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            regions: List[Dict[str, Any]] = []
            if page_idx < len(json_pages):
                jp = json_pages[page_idx]
                if isinstance(jp, list):
                    regions = [r for r in jp if isinstance(r, dict)]
            boxes = _json_regions_to_vis_boxes(regions, w, h)
            page_chunks = _json_regions_to_chunks(regions, w, h, page_no)
            arr = np.array(img)
            if boxes:
                save_layout_visualization(
                    arr,
                    boxes,
                    str(out_path),
                    show_label=True,
                    show_score=True,
                    show_index=True,
                )
            else:
                img.save(out_path, quality=95)

        ocr_blocks_by_page.append(
            {
                "pageNo": page_no,
                "files": [out_name],
                "imageSize": {"width": w, "height": h},
                "chunks": page_chunks,
            }
        )

    if not ocr_blocks_by_page:
        raise RuntimeError("未生成任何版面可视化图。")
    return ocr_blocks_by_page


def attach_ocr_quality_report(doc: Dict[str, Any]) -> Dict[str, Any]:
    pages = doc.get("ocrBlocksByPage")
    if not isinstance(pages, list):
        raise HTTPException(status_code=400, detail="当前文档没有可评估的 OCR 页面数据")
    report = evaluate_ocr_quality(pages)
    doc["ocrQualityReport"] = report
    page_reports = {
        int(page.get("pageNo", 0)): page
        for page in report.get("pages", [])
        if isinstance(page, dict)
    }
    updated_pages: List[Dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_copy = dict(page)
        page_no = int(page_copy.get("pageNo", 0))
        if page_no in page_reports:
            page_copy["qualityReport"] = page_reports[page_no]
        updated_pages.append(page_copy)
    doc["ocrBlocksByPage"] = updated_pages
    return report


def persist_document_quality_report(project_id: str, project_dir: Path, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    report = doc.get("ocrQualityReport")
    doc_id = str(doc.get("id") or "").strip()
    if not isinstance(report, dict) or not doc_id:
        return None
    payload = {
        "docId": doc_id,
        "docName": doc.get("name"),
        "generatedAt": _utc_now(),
        "summary": {
            "avgQualityScore": float(report.get("avgQualityScore") or 0.0),
            "avgStructureScore": float(report.get("avgStructureScore") or 0.0),
            "avgLayoutScore": float(report.get("avgLayoutScore") or 0.0),
            "avgFinalScore": float(report.get("avgFinalScore") or 0.0),
            "pagesWithIssues": int(report.get("pagesWithIssues") or 0),
            "pagesWithLayoutIssues": int(report.get("pagesWithLayoutIssues") or 0),
        },
        "layoutSummary": report.get("layoutSummary") if isinstance(report.get("layoutSummary"), dict) else {},
        "retry": report.get("retry") if isinstance(report.get("retry"), dict) else {},
        "pages": report.get("pages") if isinstance(report.get("pages"), list) else [],
    }
    write_document_quality_report(project_dir, doc_id, payload)
    doc["qualityReportPath"] = f"data/projects/{project_id}/documents/{doc_id}/quality_report.json"
    return payload


def _parse_pdf_with_quality_retry(
    pdf_path: Path,
    page_dir: Path,
    out_dir: Path,
    parser: Any,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    pages = glm_ocr_parse_to_layout_vis_pages(pdf_path, page_dir, out_dir, parser)
    report = evaluate_ocr_quality(pages)
    retry_info = {
        "triggered": False,
        "attempts": 1,
        "threshold": 0.6,
        "initialScore": float(report.get("avgFinalScore") or 0.0),
        "finalScore": float(report.get("avgFinalScore") or 0.0),
    }
    if float(report.get("avgFinalScore") or 0.0) >= 0.6:
        report["retry"] = retry_info
        return pages, report

    retry_info["triggered"] = True
    retry_info["attempts"] = 2
    retry_pages = glm_ocr_parse_to_layout_vis_pages(pdf_path, page_dir, out_dir, parser)
    retry_report = evaluate_ocr_quality(retry_pages)
    initial_score = float(report.get("avgFinalScore") or 0.0)
    retry_score = float(retry_report.get("avgFinalScore") or 0.0)
    if retry_score >= initial_score:
        retry_info["finalScore"] = retry_score
        retry_info["selectedAttempt"] = 2
        retry_report["retry"] = retry_info
        return retry_pages, retry_report

    retry_info["finalScore"] = initial_score
    retry_info["selectedAttempt"] = 1
    report["retry"] = retry_info
    return pages, report


@asynccontextmanager
async def _app_lifespan(app: FastAPI):
    yield
    global _glm_ocr_parser, _glm_ocr_parser_mode
    if _glm_ocr_parser is not None:
        try:
            _glm_ocr_parser.close()
        except Exception:
            pass
        _glm_ocr_parser = None
        _glm_ocr_parser_mode = None


def render_pdf_to_page_images(pdf_path: Path, out_dir: Path, dpi: int = 144) -> List[str]:
    """将 PDF 每页渲染为 PNG，保存到 out_dir，返回文件名列表（page_0001.png …）。"""
    import fitz  # PyMuPDF

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    filenames: List[str] = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    try:
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            fname = f"page_{i + 1:04d}.png"
            pix.save(str(out_dir / fname))
            filenames.append(fname)
    finally:
        doc.close()
    return filenames


app = FastAPI(title="DeepDOC API", version="0.1.0", lifespan=_app_lifespan)

# 勿同时使用 allow_credentials=True 与 allow_origins=["*"]，浏览器会拒绝跨域。
# 本 API 不用 Cookie，故关闭 credentials，便于 file:// 或其它端口调试时访问。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateProjectBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class AskSelectionBody(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    chunkContext: Optional[Dict[str, Any]] = None


class VectorSearchBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    topK: int = Field(5, ge=1, le=20)
    docId: Optional[str] = None


class RagAskBody(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    topK: int = Field(3, ge=1, le=20)


@app.get("/api/health")
def health() -> Dict[str, str]:
    logger.info("health check requested")
    return {"status": "ok"}


@app.get("/api/projects", response_model=List[Dict[str, Any]])
def list_projects() -> List[Dict[str, Any]]:
    DATA_PROJECTS.mkdir(parents=True, exist_ok=True)
    out: List[Dict[str, Any]] = []
    for d in sorted(DATA_PROJECTS.iterdir()):
        if not d.is_dir():
            continue
        meta = read_meta(d)
        if not meta:
            continue
        out.append(
            {
                "id": meta.get("id", d.name),
                "name": meta.get("name", d.name),
                "summary": meta.get("summary", ""),
                "createdAt": meta.get("createdAt", ""),
                "storage": "disk",
            }
        )
    return out


@app.post("/api/projects", response_model=Dict[str, Any])
def create_project(body: CreateProjectBody) -> Dict[str, Any]:
    name = body.name.strip()
    if not name or len(name) > 200:
        raise HTTPException(status_code=400, detail="项目名称长度须在 1–200 字符。")
    if any(x in name for x in ("..", "/", "\\")):
        raise HTTPException(status_code=400, detail="项目名称不能包含路径分隔符。")
    pid = str(uuid.uuid4())
    pdir = ensure_project_layout(pid)
    meta = {
        "id": pid,
        "name": name,
        "createdAt": _utc_now(),
        "summary": "",
        "storage": "disk",
    }
    write_data_json(pdir / "meta.json", meta)
    write_workspace(pdir, default_workspace_state())
    write_now_conversation(pdir, default_now_conversation_state())
    write_qa_sessions(pdir, default_qa_sessions_state())
    write_qa_compactions(pdir, default_qa_compactions_state())
    write_documents_index(pdir, default_documents_index())
    return meta


@app.get("/api/projects/{project_id}/workspace")
def get_workspace(project_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    meta = read_meta(pdir) or {}
    state = read_workspace(pdir)
    return {"meta": meta, "workspace": state}


@app.put("/api/projects/{project_id}/workspace")
def put_workspace(project_id: str, body: Dict[str, Any] = Body(...)) -> Dict[str, str]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    write_workspace(pdir, body)
    return {"status": "saved"}


@app.get("/api/projects/{project_id}/now-conversation")
def get_now_conversation(project_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    return read_now_conversation(pdir)


@app.put("/api/projects/{project_id}/now-conversation")
def put_now_conversation(project_id: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    payload = read_now_conversation(pdir)
    selected_items = body.get("selectedItems")
    if isinstance(selected_items, list):
        payload["selectedItems"] = selected_items
    if "activeDocId" in body:
        payload["activeDocId"] = body.get("activeDocId")
    if "activeSessionId" in body:
        payload["activeSessionId"] = body.get("activeSessionId")
    write_now_conversation(pdir, payload)
    return payload


@app.get("/api/projects/{project_id}/docs/{doc_id}/conversations")
def list_doc_conversations(project_id: str, doc_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    sessions = list_doc_sessions(pdir, doc_id)
    now_state = read_now_conversation(pdir)
    active_session_id = str(now_state.get("activeSessionId") or "")
    if not active_session_id and sessions:
        active_session_id = str(sessions[0].get("id") or "")
    return {"sessions": sessions, "activeSessionId": active_session_id}


@app.post("/api/projects/{project_id}/docs/{doc_id}/conversations")
def create_doc_conversation(project_id: str, doc_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    ws = read_workspace(pdir)
    docs = ws.get("docs") if isinstance(ws.get("docs"), list) else []
    doc = next((d for d in docs if isinstance(d, dict) and d.get("id") == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    session = create_session(pdir, doc_id, str(doc.get("name") or doc_id))
    now_state = read_now_conversation(pdir)
    now_state["activeDocId"] = doc_id
    now_state["activeSessionId"] = session["id"]
    write_now_conversation(pdir, now_state)
    compaction_map = read_qa_compactions(pdir).get("sessions")
    compaction = compaction_map.get(session["id"]) if isinstance(compaction_map, dict) else None
    return {"session": serialize_session(session, compaction), "activeSessionId": session["id"]}


@app.put("/api/projects/{project_id}/docs/{doc_id}/conversations/{session_id}/activate")
def activate_doc_conversation(project_id: str, doc_id: str, session_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    session = get_session(pdir, session_id)
    if not isinstance(session, dict) or str(session.get("docId") or "") != doc_id:
        raise HTTPException(status_code=404, detail="对话不存在")
    now_state = read_now_conversation(pdir)
    now_state["activeDocId"] = doc_id
    now_state["activeSessionId"] = session_id
    write_now_conversation(pdir, now_state)
    compaction_map = read_qa_compactions(pdir).get("sessions")
    compaction = compaction_map.get(session_id) if isinstance(compaction_map, dict) else None
    return {"session": serialize_session(session, compaction), "activeSessionId": session_id}


@app.get("/api/projects/{project_id}/docs/{doc_id}/chunks")
def list_document_chunks(project_id: str, doc_id: str, page: Optional[int] = None) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    doc = _workspace_doc_or_404(pdir, doc_id)
    payload = ensure_doc_chunks_ready(pdir, doc)
    chunks = get_page_chunks(payload, int(page)) if page else flatten_document_chunks(payload)
    return {
        "status": "ok",
        "docId": doc_id,
        "docName": str(doc.get("name") or doc_id),
        "pageCount": int(payload.get("pageCount") or 0),
        "totalChunks": int(payload.get("totalChunks") or 0),
        "pages": chunk_page_summary(payload),
        "page": int(page) if page else None,
        "chunks": chunks,
    }


@app.get("/api/projects/{project_id}/docs/{doc_id}/chunks/by-page")
def list_document_chunks_by_page(project_id: str, doc_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    doc = _workspace_doc_or_404(pdir, doc_id)
    payload = ensure_doc_chunks_ready(pdir, doc)
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else []
    return {
        "status": "ok",
        "docId": doc_id,
        "docName": str(doc.get("name") or doc_id),
        "pageCount": int(payload.get("pageCount") or 0),
        "totalChunks": int(payload.get("totalChunks") or 0),
        "pages": [page for page in pages if isinstance(page, dict)],
    }


@app.get("/api/projects/{project_id}/docs/{doc_id}/chunks/{chunk_id}")
def get_document_chunk(project_id: str, doc_id: str, chunk_id: str, radius: int = 1) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    doc = _workspace_doc_or_404(pdir, doc_id)
    payload = ensure_doc_chunks_ready(pdir, doc)
    detail = get_chunk_detail(payload, chunk_id)
    if not detail:
        raise HTTPException(status_code=404, detail="块不存在")
    chunk, _ = detail
    neighbors = get_neighbor_chunks(payload, chunk_id, radius=radius)
    return {
        "status": "ok",
        "docId": doc_id,
        "docName": str(doc.get("name") or doc_id),
        "chunk": chunk,
        "neighbors": neighbors,
    }


@app.get("/api/projects/{project_id}/docs/{doc_id}/chunks/{chunk_id}/neighbors")
def get_document_chunk_neighbors(project_id: str, doc_id: str, chunk_id: str, radius: int = 1) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    doc = _workspace_doc_or_404(pdir, doc_id)
    payload = ensure_doc_chunks_ready(pdir, doc)
    neighbors = get_neighbor_chunks(payload, chunk_id, radius=radius)
    if not neighbors.get("current"):
        raise HTTPException(status_code=404, detail="块不存在")
    return {
        "status": "ok",
        "docId": doc_id,
        "docName": str(doc.get("name") or doc_id),
        "chunkId": chunk_id,
        "radius": max(1, min(int(radius or 1), 5)),
        "neighbors": neighbors,
    }


@app.get("/api/projects/{project_id}/vector-index")
def get_project_vector_index_status(project_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    manifest = read_vector_manifest(pdir)
    return {k: v for k, v in manifest.items() if k != "items"}


@app.post("/api/projects/{project_id}/vector-index/rebuild")
def rebuild_vector_index_api(project_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    return {k: v for k, v in rebuild_project_vector_index(pdir).items() if k != "items"}


@app.put("/api/projects/{project_id}/vector-index/docs/{doc_id}")
def update_vector_index_doc_api(project_id: str, doc_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    doc = _workspace_doc_or_404(pdir, doc_id)
    ensure_doc_chunks_ready(pdir, doc)
    result = {k: v for k, v in update_project_vector_index(pdir, doc_id).items() if k != "items"}
    result["updatedDocId"] = doc_id
    return result


@app.delete("/api/projects/{project_id}/vector-index/docs/{doc_id}")
def delete_vector_index_doc_api(project_id: str, doc_id: str) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    result = {k: v for k, v in delete_doc_from_vector_index(pdir, doc_id).items() if k != "items"}
    result["removedDocId"] = doc_id
    return result


@app.post("/api/projects/{project_id}/vector-index/search")
def search_vector_index_api(project_id: str, body: VectorSearchBody) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    start = datetime.now(timezone.utc)
    logger.info(
        "vector_search request | project_id=%s | doc_id=%s | top_k=%s | query=%s",
        project_id,
        str(body.docId or "").strip() or "<all>",
        body.topK,
        body.query.strip(),
    )
    result = search_project_vector_index(
        pdir,
        body.query.strip(),
        top_k=body.topK,
        doc_id=str(body.docId or "").strip() or None,
    )
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    logger.info(
        "vector_search done | project_id=%s | hits=%s | elapsed_ms=%s",
        project_id,
        len(result.get("results") or []),
        elapsed_ms,
    )
    return result


@app.post("/api/projects/{project_id}/docs/{doc_id}/rag-ask")
def rag_ask(project_id: str, doc_id: str, body: RagAskBody) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    start = datetime.now(timezone.utc)
    doc = _workspace_doc_or_404(pdir, doc_id)
    question = body.question.strip()
    top_k = int(body.topK or RAG_TOP_K)
    current_chunks, support_chunks, doc_overview, context_source = build_rag_context(
        ROOT,
        pdir,
        doc,
        question,
        top_k=top_k,
    )
    result = ask_rag_with_selection(
        ROOT,
        current_chunks,
        support_chunks,
        question,
        str(doc.get("name") or doc_id),
        doc_id=doc_id,
        doc_overview=doc_overview,
        compacted_context="",
        recent_turns=[],
        manual_selected=False,
        context_source=context_source,
    )
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    logger.info(
        "rag_ask api done | project_id=%s | doc_id=%s | top_k=%s | elapsed_ms=%s",
        project_id,
        doc_id,
        top_k,
        elapsed_ms,
    )
    return {
        **result,
        "rag_config": {
            "chunkSize": 500,
            "overlap": 100,
            "topK": top_k,
        },
        "chunk_context": serialize_chunk_context_payload(
            source=context_source,
            current_chunks=current_chunks,
            neighbor_chunks=support_chunks,
            retrieval_chunks=current_chunks,
        ),
    }


def _to_float_score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _rank_selected_and_retrieval_chunks(
    selected_chunks: List[Dict[str, Any]],
    retrieval_chunks: List[Dict[str, Any]],
    *,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    entries: Dict[str, Dict[str, Any]] = {}
    score_map: Dict[str, float] = {}

    for idx, item in enumerate(retrieval_chunks):
        cid = str(item.get("chunkId") or "").strip()
        if not cid:
            continue
        merged = dict(item)
        merged["sourceType"] = str(merged.get("sourceType") or "retrieval")
        entries[cid] = merged
        score_map[cid] = _to_float_score(item.get("score")) + max(0.0, 0.2 - idx * 0.01)

    for idx, item in enumerate(selected_chunks):
        cid = str(item.get("chunkId") or "").strip()
        if not cid:
            continue
        base = entries.get(cid, {})
        merged = {**base, **item}
        merged["sourceType"] = "selected"
        entries[cid] = merged
        score_map[cid] = score_map.get(cid, 0.0) + 10.0 + max(0.0, 0.5 - idx * 0.01)

    ranked = sorted(
        entries.values(),
        key=lambda item: (
            -score_map.get(str(item.get("chunkId") or ""), 0.0),
            int(item.get("pageNo") or 0),
            int(item.get("index") or 0),
        ),
    )
    return ranked[: max(1, int(limit or 5))]


@app.post("/api/projects/{project_id}/docs/{doc_id}/ask-selection")
def ask_selection(project_id: str, doc_id: str, body: AskSelectionBody) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    start = datetime.now(timezone.utc)
    logger.info(
        "rag_ask request | project_id=%s | doc_id=%s | question=%s",
        project_id,
        doc_id,
        body.question.strip(),
    )
    doc = _workspace_doc_or_404(pdir, doc_id)
    now_conv = read_now_conversation(pdir)
    selected_items = now_conv.get("selectedItems") if isinstance(now_conv.get("selectedItems"), list) else []
    selected_items = [item for item in selected_items if isinstance(item, dict) and item.get("docId") == doc_id]
    has_manual_selected = bool(selected_items)
    session = ensure_active_session(
        pdir,
        doc_id,
        str(doc.get("name") or doc_id),
        active_doc_id=str(now_conv.get("activeDocId") or ""),
        active_session_id=str(now_conv.get("activeSessionId") or ""),
    )
    compaction_map = read_qa_compactions(pdir).get("sessions")
    compaction = compaction_map.get(str(session.get("id") or "")) if isinstance(compaction_map, dict) else None
    question = body.question.strip()
    chunk_payload: Optional[Dict[str, Any]] = None
    if doc.get("ocrParsed"):
        try:
            chunk_payload = ensure_doc_chunks_ready(pdir, doc)
        except HTTPException:
            chunk_payload = None

    final_top_n = 5
    retrieval_fetch_k = 8
    selected_chunks: List[Dict[str, Any]] = []
    neighbor_chunks: List[Dict[str, Any]] = []
    retrieval_chunks: List[Dict[str, Any]] = []
    current_chunks: List[Dict[str, Any]] = []
    support_chunks: List[Dict[str, Any]] = []

    if has_manual_selected:
        selected_chunks = normalize_chunk_context_items(selected_items)
        if not selected_chunks:
            selected_chunks, _ = expand_selected_with_neighbors(doc, selected_items)
            selected_chunks = dedupe_chunk_items(selected_chunks)
        if chunk_payload:
            try:
                search_result = search_project_vector_index(pdir, question, top_k=retrieval_fetch_k, doc_id=doc_id)
                retrieval_chunks = normalize_chunk_context_items(search_result.get("results"))
            except HTTPException:
                retrieval_chunks = []
        current_chunks = _rank_selected_and_retrieval_chunks(
            selected_chunks,
            retrieval_chunks,
            limit=final_top_n,
        )
        context_source = "selection_rag_top5"
    else:
        if chunk_payload:
            try:
                search_result = search_project_vector_index(pdir, question, top_k=final_top_n, doc_id=doc_id)
                retrieval_chunks = normalize_chunk_context_items(search_result.get("results"))
            except HTTPException:
                retrieval_chunks = []
        current_chunks = retrieval_chunks[:final_top_n]
        context_source = "rag_only"
    doc_overview = read_document_overview(pdir, doc_id)
    if not isinstance(doc_overview, dict) or str(doc_overview.get("status") or "") != "ready":
        doc_overview = ensure_document_overview(ROOT, pdir, doc)
    logger.info(
        "rag_ask pipeline | project_id=%s | doc_id=%s | current=%s | support=%s | retrieval=%s | top_k=%s",
        project_id,
        doc_id,
        len(current_chunks),
        len(support_chunks),
        len(retrieval_chunks),
        final_top_n,
    )
    result = ask_rag_with_selection(
        ROOT,
        current_chunks,
        support_chunks,
        question,
        str(doc.get("name") or doc_id),
        doc_id=doc_id,
        doc_overview=doc_overview,
        compacted_context=session_context_summary(compaction),
        recent_turns=session_recent_turns(session),
        manual_selected=has_manual_selected,
        context_source=context_source,
    )
    result["chunk_context"] = serialize_chunk_context_payload(
        source=context_source,
        current_chunks=current_chunks,
        neighbor_chunks=neighbor_chunks,
        retrieval_chunks=retrieval_chunks,
    )
    logger.info(
        "rag_ask model_done | project_id=%s | doc_id=%s | context_source=%s | selected=%s | support=%s | answer_len=%s | cited=%s",
        project_id,
        doc_id,
        context_source,
        len(current_chunks),
        len(support_chunks),
        len(str(result.get("answer") or "")),
        len(result.get("cited_chunk_ids") or []),
    )
    session = append_qa_turn(
        pdir,
        str(session.get("id") or ""),
        doc_id,
        str(doc.get("name") or doc_id),
        question,
        result,
    )
    compacted = compact_session_if_needed(ROOT, pdir, session)
    now_conv["activeDocId"] = doc_id
    now_conv["activeSessionId"] = str(session.get("id") or "")
    write_now_conversation(pdir, now_conv)
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    logger.info(
        "rag_ask done | project_id=%s | doc_id=%s | session_id=%s | elapsed_ms=%s",
        project_id,
        doc_id,
        str(session.get("id") or ""),
        elapsed_ms,
    )
    return {
        **result,
        "selected_chunks": current_chunks,
        "neighbor_chunks": support_chunks,
        "chunk_context": result["chunk_context"],
        "session": serialize_session(session, compacted or compaction),
    }


def _safe_workspace_doc_id(doc_id: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_\-]+$", doc_id)) and ".." not in doc_id


@app.delete("/api/projects/{project_id}/docs/{doc_id}")
def delete_project_doc(project_id: str, doc_id: str) -> Dict[str, Any]:
    """删除工作区中的文档：移除磁盘上的 PDF/页面图，并更新 workspace_state。"""
    if not _safe_workspace_doc_id(doc_id):
        raise HTTPException(status_code=400, detail="非法文档 ID")
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    ws = read_workspace(pdir)
    docs = ws.get("docs") if isinstance(ws.get("docs"), list) else []
    doc = next((d for d in docs if isinstance(d, dict) and d.get("id") == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.get("isPdf"):
        fn = doc.get("pdfFileName")
        if isinstance(fn, str) and re.match(r"^[\w.\-]+$", fn):
            pdf_base = (pdir / "uploads" / "pdfs").resolve()
            pdf_path = (pdf_base / fn).resolve()
            try:
                pdf_path.relative_to(pdf_base)
            except ValueError:
                pass
            else:
                if pdf_path.is_file():
                    pdf_path.unlink()
        if _safe_pdf_doc_id(doc_id):
            page_dir = pdir / "uploads" / "pdf_pages" / doc_id
            if page_dir.exists():
                shutil.rmtree(page_dir, ignore_errors=True)
            ocr_dir = pdir / "uploads" / "ocr_blocks" / doc_id
            if ocr_dir.exists():
                shutil.rmtree(ocr_dir, ignore_errors=True)
    delete_document_directory(pdir, doc_id)
    remove_document_from_index(pdir, doc_id)
    try:
        delete_doc_from_vector_index(pdir, doc_id)
    except HTTPException:
        pass

    session_store = read_qa_sessions(pdir)
    sessions = session_store.get("sessions") if isinstance(session_store.get("sessions"), list) else []
    remaining_sessions = [
        session
        for session in sessions
        if not (isinstance(session, dict) and str(session.get("docId") or "") == doc_id)
    ]
    if len(remaining_sessions) != len(sessions):
        session_store["sessions"] = remaining_sessions
        write_qa_sessions(pdir, session_store)

    compaction_store = read_qa_compactions(pdir)
    compactions = compaction_store.get("sessions") if isinstance(compaction_store.get("sessions"), dict) else {}
    if isinstance(compactions, dict) and remaining_sessions is not sessions:
        active_ids = {str(session.get("id") or "") for session in remaining_sessions if isinstance(session, dict)}
        compaction_store["sessions"] = {
            sid: summary for sid, summary in compactions.items() if sid in active_ids
        }
        write_qa_compactions(pdir, compaction_store)

    new_docs = [d for d in docs if isinstance(d, dict) and d.get("id") != doc_id]
    threads = ws.get("threads")
    if isinstance(threads, dict) and doc_id in threads:
        threads = {k: v for k, v in threads.items() if k != doc_id}
        ws["threads"] = threads
    sel = ws.get("selectedDocId")
    if sel == doc_id:
        sel = new_docs[0].get("id") if new_docs else None
    ws["docs"] = new_docs
    ws["selectedDocId"] = sel
    nc = read_now_conversation(pdir)
    selected_items = nc.get("selectedItems") if isinstance(nc, dict) else []
    if isinstance(selected_items, list) and any(
        isinstance(item, dict) and item.get("docId") == doc_id for item in selected_items
    ):
        write_now_conversation(pdir, default_now_conversation_state())
    elif str(nc.get("activeDocId") or "") == doc_id:
        write_now_conversation(pdir, default_now_conversation_state())
    write_workspace(pdir, ws)
    return {"status": "deleted", "selectedDocId": sel}


@app.post("/api/projects/{project_id}/docs/{doc_id}/ocr-parse")
def ocr_parse_document(project_id: str, doc_id: str) -> Dict[str, Any]:
    """对 PDF 调用 GLM-OCR 解析，每页生成版面可视化图（layout_vis 样式）到 ocr_blocks，更新工作区（首次解析；已解析则直接返回）。"""
    if not _safe_workspace_doc_id(doc_id):
        raise HTTPException(status_code=400, detail="非法文档 ID")
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    ws = read_workspace(pdir)
    docs = ws.get("docs") if isinstance(ws.get("docs"), list) else []
    doc = next((d for d in docs if isinstance(d, dict) and d.get("id") == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not doc.get("isPdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文档")
    existing_pages = doc.get("ocrBlocksByPage")
    has_chunk_payload = (
        isinstance(existing_pages, list)
        and len(existing_pages) > 0
        and all(
            isinstance(page, dict) and isinstance(page.get("chunks"), list)
            for page in existing_pages
        )
    )
    if doc.get("ocrParsed") and has_chunk_payload:
        changed = False
        if not isinstance(doc.get("ocrQualityReport"), dict):
            attach_ocr_quality_report(doc)
            changed = True
        persist_document_quality_report(project_id, pdir, doc)
        overview = ensure_document_overview(ROOT, pdir, doc)
        save_document_chunks(pdir, doc)
        try:
            update_project_vector_index(pdir, doc_id)
        except HTTPException:
            pass
        doc["hasOverview"] = True
        doc["overviewGeneratedAt"] = overview.get("generatedAt")
        doc["overviewPath"] = f"data/projects/{project_id}/documents/{doc_id}/overview.json"
        changed = True
        if changed:
            save_document_chunks(pdir, doc)
            try:
                update_project_vector_index(pdir, doc_id)
            except HTTPException:
                pass
            for i, d in enumerate(docs):
                if isinstance(d, dict) and d.get("id") == doc_id:
                    docs[i] = doc
                    break
            ws["docs"] = docs
            write_workspace(pdir, ws)
        return {"status": "already_parsed", "doc": doc}

    fn = doc.get("pdfFileName")
    if not isinstance(fn, str) or not re.match(r"^[\w.\-]+$", fn):
        raise HTTPException(status_code=400, detail="缺少 PDF 文件信息")
    pdf_base = (pdir / "uploads" / "pdfs").resolve()
    pdf_path = (pdf_base / fn).resolve()
    try:
        pdf_path.relative_to(pdf_base)
    except ValueError:
        raise HTTPException(status_code=404, detail="PDF 文件不存在")
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF 文件不存在")

    page_dir = pdir / "uploads" / "pdf_pages" / doc_id
    if not page_dir.is_dir() or not any(page_dir.glob("page_*.png")):
        raise HTTPException(status_code=400, detail="缺少页面预览图，请重新上传该 PDF。")

    out_dir = pdir / "uploads" / "ocr_blocks" / doc_id
    try:
        parser = get_glm_ocr_parser()
        ocr_blocks_by_page, quality_report = _parse_pdf_with_quality_retry(
            pdf_path, page_dir, out_dir, parser
        )
    except HTTPException:
        raise
    except Exception as e:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"解析失败：{e!s}")
    if not ocr_blocks_by_page:
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="未生成任何版面可视化图")

    doc["ocrParsed"] = True
    doc["ocrBlocksByPage"] = ocr_blocks_by_page
    doc["pdfViewMode"] = "parsed"
    attach_ocr_quality_report(doc)
    doc["ocrQualityReport"]["retry"] = quality_report.get("retry", {})
    persist_document_quality_report(project_id, pdir, doc)
    overview = upsert_document_overview(ROOT, pdir, doc)
    save_document_chunks(pdir, doc)
    try:
        update_project_vector_index(pdir, doc_id)
    except HTTPException:
        pass
    doc["hasOverview"] = True
    doc["overviewGeneratedAt"] = overview.get("generatedAt")
    doc["overviewPath"] = f"data/projects/{project_id}/documents/{doc_id}/overview.json"
    for i, d in enumerate(docs):
        if isinstance(d, dict) and d.get("id") == doc_id:
            docs[i] = doc
            break
    ws["docs"] = docs
    write_workspace(pdir, ws)
    return {"status": "ok", "doc": doc}


@app.post("/api/projects/{project_id}/docs/{doc_id}/ocr-evaluate")
def evaluate_ocr_document(project_id: str, doc_id: str) -> Dict[str, Any]:
    if not _safe_workspace_doc_id(doc_id):
        raise HTTPException(status_code=400, detail="非法文档 ID")
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir() or not (pdir / "meta.json").is_file():
        raise HTTPException(status_code=404, detail="项目不存在")
    ws = read_workspace(pdir)
    docs = ws.get("docs") if isinstance(ws.get("docs"), list) else []
    doc = next((d for d in docs if isinstance(d, dict) and d.get("id") == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    report = attach_ocr_quality_report(doc)
    if float(report.get("avgFinalScore") or 0.0) < 0.6 and doc.get("isPdf"):
        fn = doc.get("pdfFileName")
        if isinstance(fn, str) and re.match(r"^[\w.\-]+$", fn):
            pdf_path = (pdir / "uploads" / "pdfs" / fn).resolve()
            page_dir = pdir / "uploads" / "pdf_pages" / doc_id
            out_dir = pdir / "uploads" / "ocr_blocks" / doc_id
            if pdf_path.is_file() and page_dir.is_dir():
                parser = get_glm_ocr_parser()
                retry_pages, retry_report = _parse_pdf_with_quality_retry(pdf_path, page_dir, out_dir, parser)
                doc["ocrBlocksByPage"] = retry_pages
                report = attach_ocr_quality_report(doc)
                doc["ocrQualityReport"]["retry"] = retry_report.get("retry", {})
    persist_document_quality_report(project_id, pdir, doc)
    overview = upsert_document_overview(ROOT, pdir, doc)
    save_document_chunks(pdir, doc)
    try:
        update_project_vector_index(pdir, doc_id)
    except HTTPException:
        pass
    doc["hasOverview"] = True
    doc["overviewGeneratedAt"] = overview.get("generatedAt")
    doc["overviewPath"] = f"data/projects/{project_id}/documents/{doc_id}/overview.json"
    for i, d in enumerate(docs):
        if isinstance(d, dict) and d.get("id") == doc_id:
            docs[i] = doc
            break
    ws["docs"] = docs
    write_workspace(pdir, ws)
    return {"status": "ok", "report": report, "doc": doc}


@app.post("/api/projects/{project_id}/upload/pdf")
async def upload_pdf(project_id: str, file: UploadFile = File(...)) -> Dict[str, Any]:
    pdir = DATA_PROJECTS / project_id
    if not pdir.is_dir():
        raise HTTPException(status_code=404, detail="项目不存在")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 .pdf 文件")
    dest_dir = pdir / "uploads" / "pdfs"
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]", "_", file.filename)
    uid = uuid.uuid4().hex[:8]
    dest = dest_dir / f"{uid}_{safe}"
    content = await file.read()
    dest.write_bytes(content)
    doc_id = f"pdf_{uid}"
    page_dir = pdir / "uploads" / "pdf_pages" / doc_id
    if page_dir.exists():
        shutil.rmtree(page_dir, ignore_errors=True)
    try:
        page_images = render_pdf_to_page_images(dest, page_dir)
    except Exception as e:
        if page_dir.exists():
            shutil.rmtree(page_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"PDF 转图片失败：{e!s}")
    if not page_images:
        if page_dir.exists():
            shutil.rmtree(page_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="PDF 无页面或无法解析。")
    return {
        "docId": doc_id,
        "name": file.filename,
        "savedFilename": dest.name,
        "savedPath": str(dest.relative_to(ROOT)),
        "size": len(content),
        "pageCount": len(page_images),
        "pageImages": page_images,
    }


@app.get("/api/projects/{project_id}/files/pdfs/{filename}")
def get_project_pdf(project_id: str, filename: str) -> FileResponse:
    """供前端 iframe 内联预览 PDF（仅允许项目目录下的文件名）。"""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    base = (DATA_PROJECTS / project_id / "uploads" / "pdfs").resolve()
    path = (base / filename).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="' + filename.replace('"', "") + '"'},
    )


@app.get("/api/projects/{project_id}/files/pdf-pages/{doc_id}/{filename}")
def get_pdf_page_image(project_id: str, doc_id: str, filename: str) -> FileResponse:
    """项目内已生成的 PDF 页面 PNG（上传时一次性生成）。"""
    if not _safe_pdf_doc_id(doc_id) or not _safe_page_png(filename):
        raise HTTPException(status_code=400, detail="非法路径")
    base = (DATA_PROJECTS / project_id / "uploads" / "pdf_pages" / doc_id).resolve()
    path = (base / filename).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path, media_type="image/png")


@app.get("/api/projects/{project_id}/files/ocr-blocks/{doc_id}/{filename}")
def get_ocr_block_image(project_id: str, doc_id: str, filename: str) -> FileResponse:
    """解析后的版面可视化图（JPEG/PNG），兼容历史分块文件名。"""
    if not _safe_pdf_doc_id(doc_id) or not _safe_ocr_parsed_image(filename):
        raise HTTPException(status_code=400, detail="非法路径")
    base = (DATA_PROJECTS / project_id / "uploads" / "ocr_blocks" / doc_id).resolve()
    path = (base / filename).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404, detail="文件不存在")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    lower = filename.lower()
    media = "image/jpeg" if lower.endswith((".jpg", ".jpeg")) else "image/png"
    return FileResponse(path, media_type=media)


# 静态前端（须最后挂载，且 /api 路由已注册）
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
