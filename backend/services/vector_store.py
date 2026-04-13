from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.services.chunk_store import flatten_document_chunks, read_document_chunks
from backend.services.project_store import documents_root, read_json, utc_now, write_json
from embedding_test.model_registry import (
    deepdoc_default_model_name,
    deepdoc_default_model_spec,
    prepare_document_texts,
    prepare_query_texts,
)

_EMBEDDER = None
_EMBEDDER_SPEC = deepdoc_default_model_spec()
_EMBEDDER_NAME = deepdoc_default_model_name()


def current_embedding_model_name() -> str:
    return _EMBEDDER_NAME


def _vector_root(project_dir: Path) -> Path:
    return documents_root(project_dir) / "_vector_index"


def vector_index_path(project_dir: Path) -> Path:
    return _vector_root(project_dir) / "faiss.index"


def vector_manifest_path(project_dir: Path) -> Path:
    return _vector_root(project_dir) / "manifest.json"


def _default_manifest() -> Dict[str, Any]:
    return {
        "status": "empty",
        "embeddingModel": _EMBEDDER_NAME,
        "dimension": 0,
        "docCount": 0,
        "chunkCount": 0,
        "documents": [],
        "updatedAt": utc_now(),
    }


def read_vector_manifest(project_dir: Path) -> Dict[str, Any]:
    data = read_json(vector_manifest_path(project_dir), _default_manifest())
    base = _default_manifest()
    if isinstance(data, dict):
        base.update(data)
    if not isinstance(base.get("documents"), list):
        base["documents"] = []
    return base


def _ensure_vector_deps():
    try:
        import faiss  # noqa: F401
        import numpy as np  # noqa: F401
        from sentence_transformers import SentenceTransformer  # noqa: F401
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "缺少向量检索依赖，请在 deepdoc 环境执行 "
                "`pip install faiss-cpu sentence-transformers`。"
            ),
        ) from exc


def _get_embedder():
    global _EMBEDDER
    _ensure_vector_deps()
    if _EMBEDDER is None:
        from huggingface_hub import snapshot_download
        from sentence_transformers import SentenceTransformer

        try:
            _EMBEDDER = SentenceTransformer(_EMBEDDER_NAME)
        except Exception:
            local_path = snapshot_download(_EMBEDDER_NAME, local_files_only=False)
            _EMBEDDER = SentenceTransformer(local_path)
    return _EMBEDDER


def _encode_texts(texts: List[str]):
    import numpy as np

    model = _get_embedder()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype="float32")


def _collect_project_chunks(project_dir: Path) -> List[Dict[str, Any]]:
    docs_root = documents_root(project_dir)
    if not docs_root.is_dir():
        return []
    items: List[Dict[str, Any]] = []
    for child in sorted(docs_root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        payload = read_document_chunks(project_dir, child.name)
        if not isinstance(payload, dict):
            continue
        items.extend(flatten_document_chunks(payload))
    return items


def _build_search_text(chunk: Dict[str, Any]) -> str:
    label = str(chunk.get("label") or "text").strip()
    content = str(chunk.get("normalizedContent") or chunk.get("content") or "").strip()
    page_no = int(chunk.get("pageNo") or 0)
    doc_name = str(chunk.get("docName") or chunk.get("docId") or "").strip()
    return f"文档:{doc_name}\n页码:{page_no}\n类型:{label}\n内容:{content}"


def rebuild_project_vector_index(project_dir: Path) -> Dict[str, Any]:
    import faiss

    chunks = _collect_project_chunks(project_dir)
    root = _vector_root(project_dir)
    root.mkdir(parents=True, exist_ok=True)
    if not chunks:
        if vector_index_path(project_dir).exists():
            vector_index_path(project_dir).unlink()
        manifest = _default_manifest()
        write_json(vector_manifest_path(project_dir), manifest)
        return manifest

    document_texts = prepare_document_texts(_EMBEDDER_SPEC.key, [_build_search_text(chunk) for chunk in chunks])
    vectors = _encode_texts(document_texts)
    index = faiss.IndexFlatIP(int(vectors.shape[1]))
    index.add(vectors)
    faiss.write_index(index, str(vector_index_path(project_dir)))

    docs = sorted({str(chunk.get("docId") or "") for chunk in chunks if str(chunk.get("docId") or "").strip()})
    manifest = {
        "status": "ready",
        "embeddingModel": _EMBEDDER_NAME,
        "dimension": int(vectors.shape[1]),
        "docCount": len(docs),
        "chunkCount": len(chunks),
        "documents": docs,
        "updatedAt": utc_now(),
    }
    write_json(vector_manifest_path(project_dir), {**manifest, "items": chunks})
    return manifest


def update_project_vector_index(project_dir: Path, doc_id: str) -> Dict[str, Any]:
    payload = read_document_chunks(project_dir, doc_id)
    if not isinstance(payload, dict) or str(payload.get("status") or "") != "ready":
        raise HTTPException(status_code=400, detail="文档块尚未准备好，无法更新向量索引。")
    return rebuild_project_vector_index(project_dir)


def delete_doc_from_vector_index(project_dir: Path, doc_id: str) -> Dict[str, Any]:
    manifest = read_vector_manifest(project_dir)
    docs = manifest.get("documents") if isinstance(manifest.get("documents"), list) else []
    if doc_id not in [str(item) for item in docs]:
        return {
            **manifest,
            "removedDocId": doc_id,
            "status": manifest.get("status") or "empty",
        }
    return rebuild_project_vector_index(project_dir)


def search_project_vector_index(project_dir: Path, query: str, *, top_k: int = 5, doc_id: Optional[str] = None) -> Dict[str, Any]:
    import faiss

    query = str(query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="检索 query 不能为空。")
    manifest = read_json(vector_manifest_path(project_dir), None)
    if not isinstance(manifest, dict) or str(manifest.get("status") or "") != "ready":
        raise HTTPException(status_code=400, detail="向量索引尚未建立，请先写入或重建索引。")
    items = manifest.get("items") if isinstance(manifest.get("items"), list) else []
    if doc_id:
        items = [item for item in items if isinstance(item, dict) and str(item.get("docId") or "") == str(doc_id)]
    if not items:
        return {
            "status": "ok",
            "query": query,
            "topK": int(top_k),
            "results": [],
            "filters": {"docId": doc_id} if doc_id else {},
        }

    document_texts = prepare_document_texts(_EMBEDDER_SPEC.key, [_build_search_text(item) for item in items])
    vectors = _encode_texts(document_texts)
    index = faiss.IndexFlatIP(int(vectors.shape[1]))
    index.add(vectors)
    query_texts = prepare_query_texts(_EMBEDDER_SPEC.key, [query])
    query_vec = _encode_texts(query_texts)
    k = max(1, min(int(top_k or 5), len(items), 20))
    scores, indices = index.search(query_vec, k)
    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if int(idx) < 0 or int(idx) >= len(items):
            continue
        item = dict(items[int(idx)])
        item["score"] = round(float(score), 6)
        results.append(item)
    return {
        "status": "ok",
        "query": query,
        "topK": k,
        "results": results,
        "filters": {"docId": doc_id} if doc_id else {},
    }
