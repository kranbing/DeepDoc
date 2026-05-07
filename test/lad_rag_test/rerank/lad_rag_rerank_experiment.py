#!/usr/bin/env python3
"""
Cross-Encoder Rerank Experiment

Compares formula-based rerank vs cross-encoder rerank,
both with LAD section_first expansion.

Test matrix:
- Baseline (formula rerank) + LAD: total=10, 15, 20
- Cross-encoder rerank + LAD: total=10, 15, 20
"""

from __future__ import annotations

import json
import math
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Model cache on D drive
CACHE_DIR = Path(r"D:\AI\ceate_design\DeepDoc-main\models\hf_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(CACHE_DIR)
os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(CACHE_DIR)

ROOT = Path(__file__).resolve().parents[3]
LAD_DATA_DIR = ROOT / "test" / "lad_rag_test" / "data"
REPORT_PATH = Path(__file__).parent / "lad_rag_rerank_report.json"

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_lad_data() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    corpus_path = LAD_DATA_DIR / "qasper_lad_corpus.json"
    testset_path = LAD_DATA_DIR / "qasper_lad_testset.json"

    with corpus_path.open("r", encoding="utf-8") as f:
        corpus = json.load(f)
    with testset_path.open("r", encoding="utf-8") as f:
        testset = json.load(f)

    return corpus, testset


def extract_tokens(text: str) -> List[str]:
    raw = str(text or "").lower()
    tokens = re.findall(r"[a-z0-9]+|[一-鿿]{2,}", raw)
    return [t for t in tokens if t.strip()]


# ---------------------------------------------------------------------------
# Embedding & BM25
# ---------------------------------------------------------------------------

def get_embedding_model() -> SentenceTransformer:
    model_paths = [
        ROOT / "models" / "all-MiniLM-L6-v2",
        ROOT / "models" / "BAAI" / "bge-small-zh-v1.5",
    ]
    for model_path in model_paths:
        if model_path.exists():
            log(f"Loading embedding model from: {model_path}")
            return SentenceTransformer(str(model_path))
    return SentenceTransformer("all-MiniLM-L6-v2")


def get_cross_encoder() -> CrossEncoder:
    local_path = CACHE_DIR / "BAAI" / "bge-reranker-base"
    if local_path.exists():
        log(f"Loading cross-encoder from: {local_path}")
        return CrossEncoder(str(local_path))
    # Also check models dir
    alt_path = ROOT / "models" / "BAAI" / "bge-reranker-base"
    if alt_path.exists():
        log(f"Loading cross-encoder from: {alt_path}")
        return CrossEncoder(str(alt_path))
    log("Downloading BAAI/bge-reranker-base (cached via HF_HOME)...")
    return CrossEncoder("BAAI/bge-reranker-base")


def compute_bm25_scores(
    query_tokens: List[str],
    chunks: List[Dict[str, Any]],
) -> List[float]:
    k1, b = 1.2, 0.75

    doc_lens = []
    all_doc_tokens = []
    doc_freq: Dict[str, int] = defaultdict(int)

    for chunk in chunks:
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        tokens = extract_tokens(content)
        doc_lens.append(len(tokens))
        all_doc_tokens.append(tokens)
        for token in set(tokens):
            doc_freq[token] += 1

    avgdl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(chunks)

    scores = []
    for idx in range(len(chunks)):
        tf = Counter(all_doc_tokens[idx])
        score = 0.0

        for term in set(query_tokens):
            if term not in tf:
                continue
            df = doc_freq.get(term, 0)
            if df <= 0:
                continue
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            freq = tf[term]
            tf_component = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (doc_lens[idx] / avgdl)))
            score += idf * tf_component

        scores.append(score)

    return scores


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_hybrid_seed(
    query: str,
    query_embedding,
    chunk_embeddings,
    chunks: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Retrieve seed chunks using hybrid (vector + BM25)."""
    query_tokens = extract_tokens(query)
    bm25_scores = compute_bm25_scores(query_tokens, chunks)

    vector_scores = np.zeros(len(chunks))
    if query_embedding is not None and chunk_embeddings is not None:
        vector_scores = np.dot(chunk_embeddings, query_embedding)

    bm25_max = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
    vec_max = max(vector_scores) if max(vector_scores) > 0 else 1.0

    combined_scores = []
    for idx in range(len(chunks)):
        vec_norm = vector_scores[idx] / vec_max
        bm25_norm = bm25_scores[idx] / bm25_max
        combined = 0.6 * vec_norm + 0.4 * bm25_norm
        combined_scores.append((combined, idx))

    combined_scores.sort(reverse=True)

    results = []
    for score, idx in combined_scores[:top_k]:
        item = dict(chunks[idx])
        item["score"] = score
        item["vector_score"] = float(vector_scores[idx])
        item["bm25_score"] = bm25_scores[idx]
        results.append(item)

    return results


# ---------------------------------------------------------------------------
# Rerank strategies
# ---------------------------------------------------------------------------

def formula_rerank(
    candidates: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Current production formula-based rerank (simplified)."""
    for item in candidates:
        vec = float(item.get("vector_score", 0))
        bm25 = float(item.get("bm25_score", 0))
        # Normalize
        vec_norm = vec  # already from dot product, roughly [0,1]
        bm25_norm = bm25
        hybrid = 0.6 * vec_norm + 0.4 * bm25_norm
        item["rerank_score"] = hybrid

    candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    return candidates[:top_k]


def cross_encoder_rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    ce_model: CrossEncoder,
    top_k: int,
) -> List[Dict[str, Any]]:
    """Cross-encoder rerank using query-document pair scoring."""
    if not candidates:
        return []

    pairs = []
    for item in candidates:
        content = str(item.get("normalizedContent") or item.get("content") or "")
        pairs.append((query, content))

    scores = ce_model.predict(pairs, show_progress_bar=False)

    for idx, item in enumerate(candidates):
        item["ce_score"] = float(scores[idx])

    candidates.sort(key=lambda x: x.get("ce_score", 0), reverse=True)
    return candidates[:top_k]


# ---------------------------------------------------------------------------
# LAD expansion (section_first)
# ---------------------------------------------------------------------------

def expand_section_first(
    seed_chunks: List[Dict[str, Any]],
    all_chunks: List[Dict[str, Any]],
    target_count: int,
) -> List[Dict[str, Any]]:
    """Expand using section_first strategy."""
    chunk_by_id = {}
    chunks_by_section = defaultdict(list)

    for chunk in all_chunks:
        chunk_id = str(chunk.get("chunkId") or "")
        chunk_by_id[chunk_id] = chunk
        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            chunks_by_section[section_id].append(chunk)

    seed_ids = set()
    seed_sections = set()

    for chunk in seed_chunks:
        chunk_id = str(chunk.get("chunkId") or "")
        seed_ids.add(chunk_id)
        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            seed_sections.add(section_id)

    expanded = list(seed_chunks)
    expanded_ids = set(seed_ids)

    def add_chunk(chunk: Dict[str, Any]) -> bool:
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in expanded_ids:
            return False
        expanded_ids.add(chunk_id)
        expanded.append(dict(chunk))
        return len(expanded) >= target_count

    # Phase 1: Same section
    for section_id in seed_sections:
        if len(expanded) >= target_count:
            break
        section_chunks = sorted(
            chunks_by_section.get(section_id, []),
            key=lambda c: int(c.get("globalIndex") or 0),
        )
        for chunk in section_chunks:
            if len(expanded) >= target_count:
                break
            if chunk.get("isHeading"):
                continue
            add_chunk(chunk)

    # Phase 2: Neighbors
    for chunk in list(expanded):
        if len(expanded) >= target_count:
            break
        chunk_id = str(chunk.get("chunkId") or "")
        original = chunk_by_id.get(chunk_id)
        if not original:
            continue
        for neighbor_id in [
            original.get("prevGlobalChunkId"),
            original.get("nextGlobalChunkId"),
        ]:
            if not neighbor_id:
                continue
            neighbor = chunk_by_id.get(str(neighbor_id))
            if neighbor:
                if add_chunk(neighbor):
                    return expanded

    # Phase 3: Other sections
    if len(expanded) < target_count:
        for section_id in set(chunks_by_section.keys()) - seed_sections:
            if len(expanded) >= target_count:
                break
            section_chunks = sorted(
                chunks_by_section.get(section_id, []),
                key=lambda c: int(c.get("globalIndex") or 0),
            )
            for chunk in section_chunks:
                if len(expanded) >= target_count:
                    break
                if chunk.get("isHeading"):
                    continue
                add_chunk(chunk)

    return expanded[:target_count]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def compute_metrics(
    retrieved: List[Dict[str, Any]],
    evidence_chunk_ids: List[str],
    evidence_texts: List[str],
    evidence_section_ids: List[str],
) -> Dict[str, Any]:
    retrieved_ids = {str(chunk.get("chunkId") or "") for chunk in retrieved}
    evidence_set = set(evidence_chunk_ids)

    chunk_hits = len(retrieved_ids & evidence_set)
    chunk_recall = chunk_hits / max(len(evidence_set), 1)

    retrieved_text = " ".join(
        str(chunk.get("normalizedContent") or chunk.get("content") or "")
        for chunk in retrieved
    )
    retrieved_tokens = set(extract_tokens(retrieved_text))

    evidence_text = " ".join(evidence_texts)
    evidence_tokens = set(extract_tokens(evidence_text))

    token_overlap = len(retrieved_tokens & evidence_tokens)
    token_recall = token_overlap / max(len(evidence_tokens), 1)

    retrieved_sections = set()
    for chunk in retrieved:
        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            retrieved_sections.add(section_id)

    evidence_sections = set(evidence_section_ids)
    section_hits = len(retrieved_sections & evidence_sections)
    section_recall = section_hits / max(len(evidence_sections), 1)

    mrr = 0.0
    for i, chunk in enumerate(retrieved):
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in evidence_set:
            mrr = 1.0 / (i + 1)
            break

    hit = 1.0 if chunk_hits > 0 else 0.0

    return {
        "chunk_recall": round(chunk_recall, 4),
        "token_recall": round(token_recall, 4),
        "section_recall": round(section_recall, 4),
        "mrr": round(mrr, 4),
        "hit": round(hit, 4),
    }


def avg_metric(results: List[Dict[str, Any]], metric: str) -> float:
    values = [r[metric] for r in results if metric in r]
    return sum(values) / len(values) if values else 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log("Loading LAD data...")
    corpus, testset = load_lad_data()
    test_cases = testset.get("items", [])
    log(f"Loaded {len(test_cases)} test cases")

    # Organize chunks by document
    chunks_by_doc: Dict[str, List[Dict[str, Any]]] = {}
    all_chunks: List[Dict[str, Any]] = []

    for doc in corpus.get("docs", []):
        doc_id = str(doc.get("docId") or "")
        doc_chunks = []
        for page in doc.get("pages", []):
            for chunk in page.get("chunks", []):
                chunk["docId"] = doc_id
                doc_chunks.append(chunk)
                all_chunks.append(chunk)
        chunks_by_doc[doc_id] = doc_chunks

    log(f"Loaded {len(all_chunks)} chunks from {len(chunks_by_doc)} documents")

    # Load embedding model
    log("Loading embedding model...")
    model = get_embedding_model()

    embeddings_by_doc: Dict[str, Any] = {}
    log("Computing chunk embeddings...")
    chunk_texts = [
        str(c.get("normalizedContent") or c.get("content") or "") for c in all_chunks
    ]
    chunk_embeddings = model.encode(
        chunk_texts, normalize_embeddings=True, show_progress_bar=True
    )

    for idx, chunk in enumerate(all_chunks):
        doc_id = str(chunk.get("docId") or "")
        if doc_id not in embeddings_by_doc:
            embeddings_by_doc[doc_id] = {"indices": [], "embeddings": []}
        embeddings_by_doc[doc_id]["indices"].append(idx)

    for doc_id, data in embeddings_by_doc.items():
        data["embeddings"] = chunk_embeddings[data["indices"]]

    log(f"Computed embeddings for {len(chunk_texts)} chunks")

    # Load cross-encoder
    log("Loading cross-encoder model...")
    ce_model = get_cross_encoder()
    log("Cross-encoder loaded")

    # Configuration
    SEED_COUNT = 8
    CANDIDATE_COUNT = 30
    TOTAL_CHUNKS_LIST = [10, 15, 20]

    log(f"\n=== Configuration ===")
    log(f"Seed retrieval: hybrid (vector 0.6 + BM25 0.4), top-{CANDIDATE_COUNT}")
    log(f"LAD expansion: section_first, seed={SEED_COUNT}")
    log(f"Total chunks: {TOTAL_CHUNKS_LIST}")
    log(f"Methods: formula_rerank, cross_encoder_rerank")

    # Run experiments
    all_results: Dict[str, Dict[int, List[Dict[str, Any]]]] = {
        "formula_rerank": {tc: [] for tc in TOTAL_CHUNKS_LIST},
        "cross_encoder": {tc: [] for tc in TOTAL_CHUNKS_LIST},
    }

    ce_total_time = 0.0
    ce_call_count = 0

    for case_idx, case in enumerate(test_cases):
        doc_id = str(case.get("doc_id") or "")
        question = str(case.get("question") or "")
        evidence_chunk_ids = case.get("evidence_chunk_ids", [])
        evidence_texts = case.get("evidence_texts", [])
        evidence_section_ids = case.get("evidence_section_ids", [])
        category = str(case.get("category") or "unknown")
        difficulty = str(case.get("difficulty") or "unknown")

        chunks = chunks_by_doc.get(doc_id, [])
        if not chunks:
            continue

        doc_data = embeddings_by_doc.get(doc_id)
        doc_embeddings = doc_data["embeddings"] if doc_data else None

        query_embedding = model.encode(question, normalize_embeddings=True)

        # Step 1: Retrieve top-30 candidates with hybrid
        candidates = retrieve_hybrid_seed(
            question, query_embedding, doc_embeddings, chunks, CANDIDATE_COUNT
        )

        for total_chunks in TOTAL_CHUNKS_LIST:
            # --- Formula rerank pipeline ---
            formula_top = formula_rerank(list(candidates), SEED_COUNT)
            formula_expanded = expand_section_first(formula_top, chunks, total_chunks)
            formula_metrics = compute_metrics(
                formula_expanded, evidence_chunk_ids, evidence_texts, evidence_section_ids
            )

            all_results["formula_rerank"][total_chunks].append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "category": category,
                "difficulty": difficulty,
                **formula_metrics,
            })

            # --- Cross-encoder rerank pipeline ---
            t0 = time.time()
            ce_top = cross_encoder_rerank(question, list(candidates), ce_model, SEED_COUNT)
            ce_total_time += time.time() - t0
            ce_call_count += 1

            ce_expanded = expand_section_first(ce_top, chunks, total_chunks)
            ce_metrics = compute_metrics(
                ce_expanded, evidence_chunk_ids, evidence_texts, evidence_section_ids
            )

            all_results["cross_encoder"][total_chunks].append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "category": category,
                "difficulty": difficulty,
                **ce_metrics,
            })

        if (case_idx + 1) % 10 == 0:
            log(f"Processed {case_idx + 1}/{len(test_cases)} cases")

    # Save report
    report = {
        "generatedAt": datetime.now().isoformat(),
        "config": {
            "seed_count": SEED_COUNT,
            "candidate_count": CANDIDATE_COUNT,
            "total_chunks": TOTAL_CHUNKS_LIST,
            "lad_strategy": "section_first",
            "test_cases": len(test_cases),
            "cross_encoder_model": "BAAI/bge-reranker-base",
        },
        "timing": {
            "cross_encoder_total_seconds": round(ce_total_time, 2),
            "cross_encoder_calls": ce_call_count,
            "cross_encoder_avg_ms": round(ce_total_time / max(ce_call_count, 1) * 1000, 1),
        },
        "results": all_results,
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"\nReport saved to: {REPORT_PATH}")

    # Print summary
    log("\n" + "=" * 90)
    log("RERANK EXPERIMENT: Formula vs Cross-Encoder (both with LAD section_first)")
    log("=" * 90)

    header = f"{'Method':<20} {'Total':<7} {'Chunk R':<10} {'Token R':<10} {'Section R':<10} {'MRR':<8} {'Hit':<8}"
    log(f"\n{header}")
    log("-" * 73)

    for tc in TOTAL_CHUNKS_LIST:
        for method in ["formula_rerank", "cross_encoder"]:
            results = all_results[method][tc]
            label = method.replace("_", " ").title()
            log(
                f"{label:<20} {tc:<7} "
                f"{avg_metric(results, 'chunk_recall'):<10.4f} "
                f"{avg_metric(results, 'token_recall'):<10.4f} "
                f"{avg_metric(results, 'section_recall'):<10.4f} "
                f"{avg_metric(results, 'mrr'):<8.4f} "
                f"{avg_metric(results, 'hit'):<8.4f}"
            )

        # Improvement
        formula_c = avg_metric(all_results["formula_rerank"][tc], "chunk_recall")
        ce_c = avg_metric(all_results["cross_encoder"][tc], "chunk_recall")
        if formula_c > 0:
            imp = (ce_c - formula_c) / formula_c * 100
            log(f"{'CE Improvement':<20} {tc:<7} {imp:+.2f}%")
        log("")

    # By difficulty (total=15)
    log("\n" + "=" * 90)
    log("BY DIFFICULTY (total=15)")
    log("=" * 90)

    tc = 15
    for difficulty in ["single_section", "cross_section"]:
        log(f"\n  {difficulty}:")
        for method in ["formula_rerank", "cross_encoder"]:
            results = [r for r in all_results[method][tc] if r.get("difficulty") == difficulty]
            label = method.replace("_", " ").title()
            if results:
                log(
                    f"    {label:<25} Chunk R={avg_metric(results, 'chunk_recall'):.4f}  "
                    f"Token R={avg_metric(results, 'token_recall'):.4f}  "
                    f"n={len(results)}"
                )
        formula_d = [r for r in all_results["formula_rerank"][tc] if r.get("difficulty") == difficulty]
        ce_d = [r for r in all_results["cross_encoder"][tc] if r.get("difficulty") == difficulty]
        if formula_d and ce_d:
            fc = avg_metric(formula_d, "chunk_recall")
            cc = avg_metric(ce_d, "chunk_recall")
            if fc > 0:
                log(f"    {'CE Improvement':<25} {(cc - fc) / fc * 100:+.2f}%")

    # By category (total=15)
    log("\n" + "=" * 90)
    log("BY CATEGORY (total=15)")
    log("=" * 90)

    categories = sorted(set(r.get("category") for r in all_results["formula_rerank"][15]))
    log(f"\n{'Category':<18} {'Formula C':<12} {'CE C':<12} {'Improvement':<12} {'Count':<6}")
    log("-" * 60)

    for category in categories:
        formula_cat = [r for r in all_results["formula_rerank"][15] if r.get("category") == category]
        ce_cat = [r for r in all_results["cross_encoder"][15] if r.get("category") == category]
        fc = avg_metric(formula_cat, "chunk_recall") if formula_cat else 0
        cc = avg_metric(ce_cat, "chunk_recall") if ce_cat else 0
        imp = ((cc - fc) / fc * 100) if fc > 0 else 0
        log(f"{category:<18} {fc:<12.4f} {cc:<12.4f} {imp:+.2f}% {len(formula_cat):<6}")

    # Timing
    log(f"\nCross-encoder timing:")
    log(f"  Total: {ce_total_time:.2f}s for {ce_call_count} calls")
    log(f"  Average: {ce_total_time / max(ce_call_count, 1) * 1000:.1f}ms per call")


if __name__ == "__main__":
    main()
