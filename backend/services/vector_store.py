from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.services.chunk_store import flatten_document_chunks, read_document_chunks
from backend.services.lad_store import read_preferred_lad_chunks
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
        source_section_ids: List[str] = []
        source_section_paths: List[str] = []
        source_block_types: List[str] = []
        heading_texts: List[str] = []
        for item in selected:
            section_id = str(item.get("sectionId") or "").strip()
            if section_id and section_id not in source_section_ids:
                source_section_ids.append(section_id)
            section_path = str(item.get("sectionPathText") or "").strip()
            if section_path and section_path not in source_section_paths:
                source_section_paths.append(section_path)
            block_type = str(item.get("blockType") or item.get("label") or "").strip()
            if block_type and block_type not in source_block_types:
                source_block_types.append(block_type)
            heading_text = str(item.get("headingText") or "").strip()
            if heading_text and heading_text not in heading_texts:
                heading_texts.append(heading_text)
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
            "sourceSectionIds": source_section_ids,
            "sourceSectionPathTexts": source_section_paths,
            "sourceBlockTypes": source_block_types,
            "headingText": " | ".join(heading_texts[:5]),
            "sectionId": source_section_ids[0] if source_section_ids else "",
            "sectionPathText": source_section_paths[0] if source_section_paths else "",
            "blockType": ",".join(source_block_types[:5]),
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
        payload = read_preferred_lad_chunks(project_dir, child.name)
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
    section_path = str(chunk.get("sectionPathText") or "").strip()
    if not section_path:
        section_paths = chunk.get("sourceSectionPathTexts") if isinstance(chunk.get("sourceSectionPathTexts"), list) else []
        section_path = " | ".join(str(value).strip() for value in section_paths if str(value).strip())
    block_type = str(chunk.get("blockType") or "").strip()
    heading_text = str(chunk.get("headingText") or "").strip()
    return (
        f"文档:{doc_name}\n"
        f"页码:{page_no}\n"
        f"类型:{label} {block_type}\n"
        f"章节路径:{section_path}\n"
        f"标题:{heading_text}\n"
        f"内容:{content}"
    )


def _tokenize_for_lexical(text: str) -> List[str]:
    raw = str(text or "").lower()
    if not raw:
        return []
    out: List[str] = []
    for match in re.findall(r"[a-z0-9]+|[一-鿿]+", raw):
        if not match:
            continue
        if re.fullmatch(r"[a-z0-9]+", match):
            out.append(match)
            continue
        # Chinese tokenization fallback: bigrams + short full token
        if len(match) <= 6:
            out.append(match)
        if len(match) == 1:
            out.append(match)
            continue
        for i in range(len(match) - 1):
            out.append(match[i : i + 2])
    return out


def _bm25_scores(query: str, items: List[Dict[str, Any]]) -> List[float]:
    doc_lens: List[int] = []
    term_df: Dict[str, int] = {}
    tf_list: List[Counter[str]] = []
    for item in items:
        content = str(item.get("normalizedContent") or item.get("content") or "")
        tokens = _tokenize_for_lexical(content)
        doc_lens.append(len(tokens))
        tf = Counter(tokens)
        tf_list.append(tf)
        for term in tf.keys():
            term_df[term] = int(term_df.get(term, 0)) + 1
    query_terms = _tokenize_for_lexical(query)
    if not query_terms:
        return [0.0 for _ in items]

    n_docs = max(1, len(items))
    avgdl = max(1e-6, sum(doc_lens) / n_docs)
    k1 = 1.2
    b = 0.75
    scores = [0.0 for _ in items]
    for term in query_terms:
        df = int(term_df.get(term, 0))
        if df <= 0:
            continue
        idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
        for i, tf in enumerate(tf_list):
            freq = float(tf.get(term, 0))
            if freq <= 0:
                continue
            dl = float(doc_lens[i] or 1)
            denom = freq + k1 * (1 - b + b * (dl / avgdl))
            if denom <= 0:
                continue
            scores[i] += idf * ((freq * (k1 + 1)) / denom)
    return scores


def _normalize_score_map(values: Dict[str, float]) -> Dict[str, float]:
    if not values:
        return {}
    vmax = max(values.values())
    vmin = min(values.values())
    if vmax <= vmin:
        return {k: 0.0 for k in values}
    scale = vmax - vmin
    return {k: (v - vmin) / scale for k, v in values.items()}


def _structure_match_score(query_terms: set[str], item: Dict[str, Any]) -> float:
    if not query_terms:
        return 0.0
    fields: List[str] = [
        str(item.get("sectionPathText") or ""),
        str(item.get("headingText") or ""),
        str(item.get("blockType") or ""),
    ]
    for value in item.get("sourceSectionPathTexts") if isinstance(item.get("sourceSectionPathTexts"), list) else []:
        fields.append(str(value or ""))
    for value in item.get("sourceBlockTypes") if isinstance(item.get("sourceBlockTypes"), list) else []:
        fields.append(str(value or ""))
    tokens = set(_tokenize_for_lexical("\n".join(fields)))
    if not tokens:
        return 0.0
    score = len(query_terms & tokens) / max(1, len(query_terms))
    if str(item.get("headingText") or "").strip():
        score += 0.05
    if "title" in str(item.get("blockType") or "").lower():
        score += 0.04
    return max(0.0, min(score, 1.0))


def _hybrid_rerank(
    *,
    query: str,
    items: List[Dict[str, Any]],
    vector_rank: List[Tuple[int, float]],
    bm25_scores: List[float],
    top_k: int,
) -> List[Dict[str, Any]]:
    candidate_limit = max(20, min(len(items), max(int(top_k or 5) * 6, 30)))
    vector_rank_map: Dict[int, int] = {}
    vector_raw_map: Dict[str, float] = {}
    for rank, (idx, score) in enumerate(vector_rank, start=1):
        vector_rank_map[int(idx)] = rank
        cid = str(items[int(idx)].get("chunkId") or items[int(idx)].get("chunkKey") or f"idx_{idx}")
        vector_raw_map[cid] = float(score)
        if len(vector_rank_map) >= candidate_limit:
            break

    bm25_ranked = sorted(range(len(items)), key=lambda i: float(bm25_scores[i]), reverse=True)
    bm25_rank_map: Dict[int, int] = {}
    bm25_raw_map: Dict[str, float] = {}
    for rank, idx in enumerate(bm25_ranked, start=1):
        if float(bm25_scores[idx]) <= 0:
            break
        bm25_rank_map[int(idx)] = rank
        cid = str(items[int(idx)].get("chunkId") or items[int(idx)].get("chunkKey") or f"idx_{idx}")
        bm25_raw_map[cid] = float(bm25_scores[idx])
        if len(bm25_rank_map) >= candidate_limit:
            break

    query_terms = set(_tokenize_for_lexical(query))
    normalized_vec = _normalize_score_map(vector_raw_map)
    normalized_bm25 = _normalize_score_map(bm25_raw_map)
    rrf_k = 60.0
    fused: List[Tuple[float, Dict[str, Any]]] = []
    candidate_indices = sorted(set(vector_rank_map.keys()) | set(bm25_rank_map.keys()))
    for idx in candidate_indices:
        item = dict(items[idx])
        cid = str(item.get("chunkId") or item.get("chunkKey") or f"idx_{idx}")
        v_rank = vector_rank_map.get(idx)
        b_rank = bm25_rank_map.get(idx)
        v_rrf = (1.0 / (rrf_k + v_rank)) if v_rank else 0.0
        b_rrf = (1.0 / (rrf_k + b_rank)) if b_rank else 0.0
        vec = float(normalized_vec.get(cid, 0.0))
        lex = float(normalized_bm25.get(cid, 0.0))
        content_terms = set(_tokenize_for_lexical(str(item.get("normalizedContent") or item.get("content") or "")))
        coverage = (len(query_terms & content_terms) / max(1, len(query_terms))) if query_terms else 0.0
        structure_score = _structure_match_score(query_terms, item)

        # Keep semantic retrieval dominant while preserving keyword precision.
        hybrid_score = 0.6 * vec + 0.4 * lex
        final_score = (v_rrf + b_rrf) + 0.72 * hybrid_score + 0.18 * coverage + 0.1 * structure_score
        item["score"] = round(float(final_score), 6)
        item["vectorScore"] = round(float(vector_raw_map.get(cid, 0.0)), 6)
        item["lexicalScore"] = round(float(bm25_raw_map.get(cid, 0.0)), 6)
        item["hybridCoverage"] = round(float(coverage), 6)
        item["structureScore"] = round(float(structure_score), 6)
        fused.append((final_score, item))
    fused.sort(key=lambda x: x[0], reverse=True)
    k = max(1, min(int(top_k or 5), len(fused), 20))
    return [item for _, item in fused[:k]]


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

    requested_k = max(1, min(int(top_k or 5), 20))

    document_texts = prepare_document_texts(_EMBEDDER_SPEC.key, [_build_search_text(item) for item in items])
    vectors = _encode_texts(document_texts)
    index = faiss.IndexFlatIP(int(vectors.shape[1]))
    index.add(vectors)
    query_texts = prepare_query_texts(_EMBEDDER_SPEC.key, [query])
    query_vec = _encode_texts(query_texts)

    candidate_k = max(requested_k * 6, 30)
    candidate_k = max(requested_k, min(candidate_k, len(items), 80))
    scores, indices = index.search(query_vec, candidate_k)
    vector_rank: List[Tuple[int, float]] = []
    for score, idx in zip(scores[0], indices[0]):
        if int(idx) < 0 or int(idx) >= len(items):
            continue
        vector_rank.append((int(idx), float(score)))

    bm25_scores = _bm25_scores(query, items)
    results = _hybrid_rerank(
        query=query,
        items=items,
        vector_rank=vector_rank,
        bm25_scores=bm25_scores,
        top_k=requested_k,
    )
    return {
        "status": "ok",
        "query": query,
        "topK": len(results),
        "results": results,
        "filters": {"docId": doc_id} if doc_id else {},
    }
