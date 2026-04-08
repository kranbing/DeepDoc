from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from backend.services.paths import DATA_PROJECTS


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def project_dir(project_id: str) -> Path:
    return DATA_PROJECTS / project_id


def ensure_project_layout(project_id: str) -> Path:
    p = project_dir(project_id)
    (p / "conversations").mkdir(parents=True, exist_ok=True)
    (p / "conversations" / "sessions").mkdir(parents=True, exist_ok=True)
    (p / "documents").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "pdfs").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "pdf_pages").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "ocr_blocks").mkdir(parents=True, exist_ok=True)
    (p / "uploads" / "databases").mkdir(parents=True, exist_ok=True)
    (p / "outputs").mkdir(parents=True, exist_ok=True)
    return p


def read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = annotate_json_payload(path, payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def annotate_json_payload(path: Path, payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    comment = structure_comment_for_path(path)
    if not comment:
        return payload
    data = {k: v for k, v in payload.items() if k != "_structureCommentZh"}
    annotated: Dict[str, Any] = {"_structureCommentZh": comment}
    annotated.update(data)
    return annotated


def structure_comment_for_path(path: Path) -> str:
    path_str = str(path).replace("\\", "/")
    name = path.name
    if name == "meta.json":
        return "项目元信息文件，记录项目ID、名称、创建时间等基础信息。"
    if name == "workspace_state.json":
        return "工作区状态文件，记录当前项目中的文档、数据库、交付物以及界面选择状态。"
    if name == "now_conversation.json":
        return "当前会话状态文件，记录当前激活的文档、会话以及当前选中的块。"
    if name == "session.json":
        return "单个对话文件，记录该会话的基础信息、历史问答轮次和建议问题。"
    if name == "summary.json":
        return "单个对话的上下文压缩摘要文件，用于长对话场景下保留重点信息。"
    if name == "index.json" and "/conversations/sessions/" in path_str:
        return "对话索引文件，记录项目下各会话的轻量信息，便于列出历史会话。"
    if name == "index.json" and "/documents/" in path_str:
        return "文档索引文件，记录项目内各文档的轻量概述信息，供多文档检索和RAG前置筛选使用。"
    if name == "overview.json":
        return "单文档概述文件，基于OCR结果抽样生成，用于文档整体认知和后续多文档RAG。"
    if name == "quality_report.json":
        return "单文档OCR黑盒质量报告文件，记录文档级与页级评分、问题项、版面指标和重试信息。"
    return ""


def documents_root(project_dir: Path) -> Path:
    return project_dir / "documents"


def document_dir(project_dir: Path, doc_id: str) -> Path:
    return documents_root(project_dir) / doc_id


def document_overview_path(project_dir: Path, doc_id: str) -> Path:
    return document_dir(project_dir, doc_id) / "overview.json"


def documents_index_path(project_dir: Path) -> Path:
    return documents_root(project_dir) / "index.json"


def document_quality_report_path(project_dir: Path, doc_id: str) -> Path:
    return document_dir(project_dir, doc_id) / "quality_report.json"


def default_documents_index() -> Dict[str, Any]:
    return {
        "_comment": "Project-level lightweight document index for future multi-document retrieval.",
        "generatedAt": utc_now(),
        "documents": [],
    }


def read_documents_index(project_dir: Path) -> Dict[str, Any]:
    data = read_json(documents_index_path(project_dir), default_documents_index())
    base = default_documents_index()
    if isinstance(data, dict):
        base.update(data)
    if not isinstance(base.get("documents"), list):
        base["documents"] = []
    return base


def write_documents_index(project_dir: Path, payload: Dict[str, Any]) -> None:
    data = dict(payload)
    data["generatedAt"] = utc_now()
    write_json(documents_index_path(project_dir), data)


def read_document_overview(project_dir: Path, doc_id: str) -> Optional[Dict[str, Any]]:
    data = read_json(document_overview_path(project_dir, doc_id), None)
    return data if isinstance(data, dict) else None


def write_document_overview(project_dir: Path, doc_id: str, payload: Dict[str, Any]) -> None:
    write_json(document_overview_path(project_dir, doc_id), payload)


def read_document_quality_report(project_dir: Path, doc_id: str) -> Optional[Dict[str, Any]]:
    data = read_json(document_quality_report_path(project_dir, doc_id), None)
    return data if isinstance(data, dict) else None


def write_document_quality_report(project_dir: Path, doc_id: str, payload: Dict[str, Any]) -> None:
    write_json(document_quality_report_path(project_dir, doc_id), payload)


def delete_document_directory(project_dir: Path, doc_id: str) -> None:
    doc_path = document_dir(project_dir, doc_id)
    if doc_path.exists():
        shutil.rmtree(doc_path, ignore_errors=True)


def remove_document_from_index(project_dir: Path, doc_id: str) -> None:
    index = read_documents_index(project_dir)
    docs = index.get("documents") if isinstance(index.get("documents"), list) else []
    index["documents"] = [
        item
        for item in docs
        if not (isinstance(item, dict) and str(item.get("docId") or "") == doc_id)
    ]
    write_documents_index(project_dir, index)
