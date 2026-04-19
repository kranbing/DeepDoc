from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from backend.services.chunk_store import flatten_document_chunks, read_document_chunks
from backend.services.project_store import documents_root, read_json, utc_now, write_json
from backend.embedding_model_registry import (
    deepdoc_default_model_name,
    deepdoc_default_model_spec,
    local_model_candidate_paths,
    prepare_document_texts,
    prepare_query_texts,
)

_EMBEDDER = None
_EMBEDDER_SPEC = deepdoc_default_model_spec()
_EMBEDDER_NAME = deepdoc_default_model_name()

# The best effect chunk strategy is rag_500_100
RAG_CHUNK_SIZE = 500
RAG_OVERLAP = 100

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
        import os
        from sentence_transformers import SentenceTransformer

        local_only = str(os.getenv("DEEPDOC_LOCAL_MODEL_ONLY", "1")).strip().lower() not in {"0", "false", "no", "off"}
        candidate_paths = local_model_candidate_paths()
        old_endpoint = os.environ.get("HF_ENDPOINT")
        mirror_endpoint = os.getenv("DEEPDOC_HF_ENDPOINT", "https://hf-mirror.com").strip()
        need_mirror = (not local_only) and bool(mirror_endpoint)

        last_error: Exception | None = None
        try:
            for model_source in candidate_paths:
                try:
                    if model_source.startswith("models/"):
                        local_path = Path(__file__).resolve().parents[2] / model_source
                        if local_path.is_dir():
                            _EMBEDDER = SentenceTransformer(str(local_path))
                            return _EMBEDDER
                    if model_source == _EMBEDDER_NAME and local_only:
                        continue
                except Exception as exc:
                    last_error = exc
                    continue

            if need_mirror:
                os.environ["HF_ENDPOINT"] = mirror_endpoint
            model_kwargs = {"local_files_only": local_only}
            _EMBEDDER = SentenceTransformer(_EMBEDDER_NAME, model_kwargs=model_kwargs)
        except TypeError:
            if need_mirror:
                os.environ["HF_ENDPOINT"] = mirror_endpoint
            _EMBEDDER = SentenceTransformer(_EMBEDDER_NAME)
        except Exception as exc:
            last_error = exc
            if local_only:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "未找到项目内本地模型目录，且本地优先加载失败。"
                        "请将模型下载到 backend/../models/BAAI/bge-small-zh-v1.5，"
                        "或将 DEEPDOC_LOCAL_MODEL_ONLY 设为 0 允许联网下载。"
                    ),
                ) from exc
            raise
        finally:
            if need_mirror:
                if old_endpoint is None:
                    os.environ.pop("HF_ENDPOINT", None)
                else:
                    os.environ["HF_ENDPOINT"] = old_endpoint
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


def _build_rag_chunks_from_payload(payload: Dict[str, Any], chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
    blocks = flatten_document_chunks(payload)
    # Filter out empty or image blocks
    blocks = [
        b for b in blocks 
        if str(b.get("label") or "").strip().lower() != "image" 
        and str(b.get("normalizedContent") or b.get("content") or "").strip()
    ]
    if not blocks:
        return []
    
    doc_id = str(payload.get("docId") or "").strip()
    doc_name = str(payload.get("docName") or doc_id).strip() or doc_id
    
    rag_chunks: List[Dict[str, Any]] = []
    start = 0
    while start < len(blocks):
        end = start
        char_count = 0
        selected: List[Dict[str, Any]] = []
        while end < len(blocks):
            block = blocks[end]
            text = str(block.get("normalizedContent") or block.get("content") or "").strip()
            addition = len(text) + (2 if selected else 0)
            if selected and char_count + addition > chunk_size:
                break
            selected.append(block)
            char_count += addition
            end += 1
        
        if not selected:
            selected = [blocks[start]]
            end = start + 1

        source_chunk_ids = [str(item.get("chunkId") or item.get("chunkKey") or "") for item in selected]
        source_page_nos = sorted({int(item.get("pageNo") or 0) for item in selected})
        content = "\n\n".join(str(item.get("normalizedContent") or item.get("content") or "").strip() for item in selected).strip()
        
        rag_chunks.append({
            "chunkId": f"rag_{chunk_size}_{overlap}_{len(rag_chunks):04d}",
            "docId": doc_id,
            "docName": doc_name,
            "pageNo": source_page_nos[0] if source_page_nos else 0,
            "index": len(rag_chunks),
            "label": "text",
            "content": content,
            "normalizedContent": content,
            "charCount": len(content),
            "sourceChunkIds": source_chunk_ids,
            "sourcePageNos": source_page_nos,
            "sourceChunkCount": len(selected),
        })

        if end >= len(blocks):
            break

        if overlap <= 0:
            start = end
            continue

        overlap_chars = 0
        next_start = end
        while next_start > start:
            candidate = blocks[next_start - 1]
            text = str(candidate.get("normalizedContent") or candidate.get("content") or "").strip()
            addition = len(text) + (2 if overlap_chars else 0)
            if overlap_chars + addition > overlap and next_start < end:
                break
            next_start -= 1
            overlap_chars += addition
            if overlap_chars >= overlap:
                break
        start = next_start if next_start > start else min(end, start + 1)
        
    return rag_chunks

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
        # Use the best effect chunk strategy (rag_500_100) instead of flat layout chunks
        rag_chunks = _build_rag_chunks_from_payload(payload, RAG_CHUNK_SIZE, RAG_OVERLAP)
        items.extend(rag_chunks)
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
