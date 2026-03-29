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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DATA_PROJECTS = ROOT / "data" / "projects"
WEB_DIR = ROOT / "web"



def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_project_layout(project_id: str) -> Path:
    """创建项目目录：对话、上传 PDF/数据库、输出等。"""
    p = DATA_PROJECTS / project_id
    (p / "conversations").mkdir(parents=True, exist_ok=True)
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


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


def get_glm_ocr_parser() -> Any:
    """懒加载 GlmOcr。

    - 默认 ``GLMOCR_MODE=selfhosted``：连接本机 OCR 服务（常见为 Docker 内 vLLM，
      地址见 ``GLMOCR_OCR_API_HOST`` / ``GLMOCR_OCR_API_PORT``，默认 127.0.0.1:8080）。
    - ``GLMOCR_MODE=maas``：使用智谱云端，需 ``ZHIPU_API_KEY`` 或 ``GLMOCR_API_KEY``。
    """
    global _glm_ocr_parser, _glm_ocr_parser_mode
    use_maas = _glm_ocr_use_maas()
    if use_maas and not (
        os.environ.get("ZHIPU_API_KEY") or os.environ.get("GLMOCR_API_KEY")
    ):
        raise HTTPException(
            status_code=503,
            detail="已启用云端解析（GLMOCR_MODE=maas），请设置 ZHIPU_API_KEY 或 GLMOCR_API_KEY。",
        )
    try:
        _ensure_glmocr_importable()
        from glmocr import GlmOcr
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="未安装 GLM-OCR SDK：在仓库根目录执行 pip install -r backend/requirements.txt",
        ) from e

    mode_key = "maas" if use_maas else "selfhosted"
    if _glm_ocr_parser is None or _glm_ocr_parser_mode != mode_key:
        if _glm_ocr_parser is not None:
            try:
                _glm_ocr_parser.close()
            except Exception:
                pass
            _glm_ocr_parser = None
        _glm_ocr_parser = GlmOcr(mode="selfhosted" if not use_maas else "maas")
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

        if not done:
            img = Image.open(page_png_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            w, h = img.size
            regions: List[Dict[str, Any]] = []
            if page_idx < len(json_pages):
                jp = json_pages[page_idx]
                if isinstance(jp, list):
                    regions = [r for r in jp if isinstance(r, dict)]
            boxes = _json_regions_to_vis_boxes(regions, w, h)
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

        ocr_blocks_by_page.append({"pageNo": page_no, "files": [out_name]})

    if not ocr_blocks_by_page:
        raise RuntimeError("未生成任何版面可视化图。")
    return ocr_blocks_by_page


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


@app.get("/api/health")
def health() -> Dict[str, str]:
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
    (pdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    write_workspace(pdir, default_workspace_state())
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
    if doc.get("ocrParsed"):
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
        ocr_blocks_by_page = glm_ocr_parse_to_layout_vis_pages(
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
    for i, d in enumerate(docs):
        if isinstance(d, dict) and d.get("id") == doc_id:
            docs[i] = doc
            break
    ws["docs"] = docs
    write_workspace(pdir, ws)
    return {"status": "ok", "doc": doc}


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
