#!/usr/bin/env python3
"""
LAD-RAG vs Traditional RAG Comparison

Compare:
- LAD-RAG: vector top5 + LAD structure expansion to 15
- Traditional RAG: vector top15

Total chunks limited to 15 for fair comparison.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[3]
LAD_DATA_DIR = ROOT / "test" / "8-lad_rag_test" / "data"
REPORT_PATH = Path(__file__).parent / "lad_rag_vs_traditional_report.json"

# Try to import embedding dependencies
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def load_lad_data() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load LAD corpus and testset."""
    corpus_path = LAD_DATA_DIR / "qasper_lad_corpus.json"
    testset_path = LAD_DATA_DIR / "qasper_lad_testset.json"

    with corpus_path.open("r", encoding="utf-8") as f:
        corpus = json.load(f)
    with testset_path.open("r", encoding="utf-8") as f:
        testset = json.load(f)

    return corpus, testset


def extract_tokens(text: str) -> List[str]:
    """Extract tokens."""
    raw = str(text or "").lower()
    tokens = re.findall(r"[a-z0-9]+|[一-鿿]{2,}", raw)
    return [t for t in tokens if t.strip()]


def get_embedding_model():
    """Load embedding model."""
    if not HAS_EMBEDDINGS:
        return None

    model_paths = [
        ROOT / "models" / "all-MiniLM-L6-v2",
        ROOT / "models" / "BAAI" / "bge-small-zh-v1.5",
    ]

    for model_path in model_paths:
        if model_path.exists():
            log(f"Loading embedding model from: {model_path}")
            return SentenceTransformer(str(model_path))

    log("Loading all-MiniLM-L6-v2 from HuggingFace...")
    return SentenceTransformer("all-MiniLM-L6-v2")


def compute_bm25_scores(
    query_tokens: List[str],
    chunks: List[Dict[str, Any]],
) -> List[float]:
    """Compute BM25 scores for all chunks."""
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
    for idx, chunk in enumerate(chunks):
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


def retrieve_vector_topk(
    query_embedding,
    chunk_embeddings,
    chunks: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Retrieve using vector similarity only."""
    if query_embedding is None or chunk_embeddings is None:
        return []

    # Compute cosine similarities
    similarities = np.dot(chunk_embeddings, query_embedding)

    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        item = dict(chunks[idx])
        item["score"] = float(similarities[idx])
        item["retrieval_method"] = "vector"
        results.append(item)

    return results


def retrieve_hybrid_topk(
    query: str,
    query_embedding,
    chunk_embeddings,
    chunks: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Retrieve using hybrid (vector + BM25)."""
    query_tokens = extract_tokens(query)

    # BM25 scores
    bm25_scores = compute_bm25_scores(query_tokens, chunks)

    # Vector scores
    vector_scores = np.zeros(len(chunks))
    if query_embedding is not None and chunk_embeddings is not None:
        vector_scores = np.dot(chunk_embeddings, query_embedding)

    # Normalize scores
    bm25_max = max(bm25_scores) if bm25_scores else 1.0
    vec_max = max(vector_scores) if max(vector_scores) > 0 else 1.0

    # Combine scores (0.6 vector + 0.4 BM25)
    combined_scores = []
    for idx in range(len(chunks)):
        vec_norm = vector_scores[idx] / vec_max if vec_max > 0 else 0
        bm25_norm = bm25_scores[idx] / bm25_max if bm25_max > 0 else 0
        combined = 0.6 * vec_norm + 0.4 * bm25_norm
        combined_scores.append((combined, idx))

    # Sort and get top-k
    combined_scores.sort(reverse=True)

    results = []
    for score, idx in combined_scores[:top_k]:
        item = dict(chunks[idx])
        item["score"] = score
        item["vector_score"] = float(vector_scores[idx])
        item["bm25_score"] = bm25_scores[idx]
        item["retrieval_method"] = "hybrid"
        results.append(item)

    return results


def expand_with_lad_structure(
    seed_chunks: List[Dict[str, Any]],
    all_chunks: List[Dict[str, Any]],
    target_count: int,
) -> List[Dict[str, Any]]:
    """
    Expand using LAD structure.

    Strategy:
    1. Find seed chunk neighbors (prev, next, same page)
    2. Find chunks in same sections
    3. Until reaching target_count
    """
    if not seed_chunks:
        return []

    # Build lookup maps
    chunk_by_id = {}
    chunks_by_section = defaultdict(list)
    chunk_indices = {}

    for idx, chunk in enumerate(all_chunks):
        chunk_id = str(chunk.get("chunkId") or "")
        chunk_by_id[chunk_id] = chunk
        chunk_indices[chunk_id] = idx

        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            chunks_by_section[section_id].append(chunk)

    # Collect seed IDs and sections
    seed_ids = set()
    seed_sections = set()

    for chunk in seed_chunks:
        chunk_id = str(chunk.get("chunkId") or "")
        seed_ids.add(chunk_id)

        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            seed_sections.add(section_id)

    # Start with seed chunks
    expanded = list(seed_chunks)
    expanded_ids = set(seed_ids)

    def add_chunk(chunk: Dict[str, Any]) -> bool:
        """Add chunk if not already included. Returns True if target reached."""
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in expanded_ids:
            return False
        expanded_ids.add(chunk_id)
        item = dict(chunk)
        item["retrieval_method"] = "lad_expansion"
        expanded.append(item)
        return len(expanded) >= target_count

    # Phase 1: Add neighbors of seed chunks
    for chunk in seed_chunks:
        if len(expanded) >= target_count:
            break

        chunk_id = str(chunk.get("chunkId") or "")
        original_chunk = chunk_by_id.get(chunk_id)
        if not original_chunk:
            continue

        # Get neighbor IDs
        neighbors = [
            original_chunk.get("prevGlobalChunkId"),
            original_chunk.get("nextGlobalChunkId"),
            original_chunk.get("prevSamePageChunkId"),
            original_chunk.get("nextSamePageChunkId"),
        ]

        for neighbor_id in neighbors:
            if not neighbor_id:
                continue
            neighbor = chunk_by_id.get(str(neighbor_id))
            if neighbor:
                if add_chunk(neighbor):
                    return expanded

    # Phase 2: Add chunks from same sections
    for section_id in seed_sections:
        if len(expanded) >= target_count:
            break

        section_chunks = chunks_by_section.get(section_id, [])
        # Sort by globalIndex to maintain document order
        section_chunks.sort(key=lambda c: int(c.get("globalIndex") or 0))

        for chunk in section_chunks:
            if len(expanded) >= target_count:
                break
            # Skip heading blocks
            if chunk.get("isHeading"):
                continue
            add_chunk(chunk)

    # Phase 3: If still not enough, add from parent/child sections
    if len(expanded) < target_count:
        # Get all section IDs in the document
        all_sections = set(chunks_by_section.keys())
        remaining_sections = all_sections - seed_sections

        for section_id in remaining_sections:
            if len(expanded) >= target_count:
                break

            section_chunks = chunks_by_section.get(section_id, [])
            section_chunks.sort(key=lambda c: int(c.get("globalIndex") or 0))

            for chunk in section_chunks:
                if len(expanded) >= target_count:
                    break
                if chunk.get("isHeading"):
                    continue
                add_chunk(chunk)

    return expanded[:target_count]


def compute_metrics(
    retrieved: List[Dict[str, Any]],
    evidence_chunk_ids: List[str],
    evidence_texts: List[str],
    evidence_section_ids: List[str],
) -> Dict[str, Any]:
    """Compute retrieval metrics."""
    retrieved_ids = {str(chunk.get("chunkId") or "") for chunk in retrieved}
    evidence_set = set(evidence_chunk_ids)

    # Chunk-level recall
    chunk_hits = len(retrieved_ids & evidence_set)
    chunk_recall = chunk_hits / max(len(evidence_set), 1)

    # Token-level recall
    retrieved_text = " ".join(
        str(chunk.get("normalizedContent") or chunk.get("content") or "")
        for chunk in retrieved
    )
    retrieved_tokens = set(extract_tokens(retrieved_text))

    evidence_text = " ".join(evidence_texts)
    evidence_tokens = set(extract_tokens(evidence_text))

    token_overlap = len(retrieved_tokens & evidence_tokens)
    token_recall = token_overlap / max(len(evidence_tokens), 1)

    # Section-level recall
    retrieved_sections = set()
    for chunk in retrieved:
        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            retrieved_sections.add(section_id)

    evidence_sections = set(evidence_section_ids)
    section_hits = len(retrieved_sections & evidence_sections)
    section_recall = section_hits / max(len(evidence_sections), 1)

    # MRR
    mrr = 0.0
    for i, chunk in enumerate(retrieved):
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in evidence_set:
            mrr = 1.0 / (i + 1)
            break

    # Hit rate
    hit = 1.0 if chunk_hits > 0 else 0.0

    return {
        "chunk_recall": round(chunk_recall, 4),
        "token_recall": round(token_recall, 4),
        "section_recall": round(section_recall, 4),
        "mrr": round(mrr, 4),
        "hit": round(hit, 4),
        "chunk_hits": chunk_hits,
    }


def run_comparison(
    test_cases: List[Dict[str, Any]],
    chunks_by_doc: Dict[str, List[Dict[str, Any]]],
    embeddings_by_doc: Dict[str, Any],
    model,
    total_chunks: int,
    lad_seed_k: int,
    seed_method: str = "vector",  # "vector" or "hybrid"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Run comparison between LAD-RAG and Traditional RAG."""
    results_lad = []
    results_traditional = []

    for case in test_cases:
        doc_id = str(case.get("doc_id") or "")
        question = str(case.get("question") or "")
        evidence_chunk_ids = case.get("evidence_chunk_ids", [])
        evidence_texts = case.get("evidence_texts", [])
        evidence_section_ids = case.get("evidence_section_ids", [])

        chunks = chunks_by_doc.get(doc_id, [])
        if not chunks:
            continue

        # Get document embeddings
        doc_data = embeddings_by_doc.get(doc_id)
        doc_embeddings = doc_data["embeddings"] if doc_data else None

        # Compute query embedding
        query_embedding = None
        if model is not None:
            query_embedding = model.encode(question, normalize_embeddings=True)

        # Traditional RAG: hybrid top N
        traditional_results = retrieve_hybrid_topk(
            question, query_embedding, doc_embeddings, chunks, total_chunks
        )
        traditional_metrics = compute_metrics(
            traditional_results, evidence_chunk_ids, evidence_texts, evidence_section_ids
        )

        results_traditional.append({
            "case_id": case.get("id"),
            "doc_id": doc_id,
            "question": question,
            "method": "traditional_rag",
            "total_chunks": len(traditional_results),
            **traditional_metrics,
        })

        # LAD-RAG: seed + expansion
        if seed_method == "hybrid":
            seed_chunks = retrieve_hybrid_topk(
                question, query_embedding, doc_embeddings, chunks, lad_seed_k
            )
        else:
            seed_chunks = retrieve_vector_topk(
                query_embedding, doc_embeddings, chunks, lad_seed_k
            )

        # Expand using LAD structure
        lad_results = expand_with_lad_structure(seed_chunks, chunks, total_chunks)

        lad_metrics = compute_metrics(
            lad_results, evidence_chunk_ids, evidence_texts, evidence_section_ids
        )

        # Count expansion sources
        expansion_counts = Counter(c.get("retrieval_method") for c in lad_results)

        results_lad.append({
            "case_id": case.get("id"),
            "doc_id": doc_id,
            "question": question,
            "method": "lad_rag",
            "seed_count": len(seed_chunks),
            "total_chunks": len(lad_results),
            "vector_chunks": expansion_counts.get("vector", 0),
            "expanded_chunks": expansion_counts.get("lad_expansion", 0),
            **lad_metrics,
        })

    return results_traditional, results_lad


def avg_metric(results: List[Dict[str, Any]], metric: str) -> float:
    """Calculate average metric."""
    values = [r[metric] for r in results if metric in r]
    return sum(values) / len(values) if values else 0


def print_comparison(
    config_name: str,
    results_traditional: List[Dict[str, Any]],
    results_lad: List[Dict[str, Any]],
) -> None:
    """Print comparison results."""
    log(f"\n=== {config_name} ===")

    log(f"{'Method':<20} {'Chunk R':<10} {'Token R':<10} {'Section R':<10} {'MRR':<10} {'Hit Rate':<10}")
    log("-" * 70)

    for method, results in [("Traditional RAG", results_traditional), ("LAD-RAG", results_lad)]:
        chunk_r = avg_metric(results, "chunk_recall")
        token_r = avg_metric(results, "token_recall")
        section_r = avg_metric(results, "section_recall")
        mrr = avg_metric(results, "mrr")
        hit = avg_metric(results, "hit")

        log(f"{method:<20} {chunk_r:<10.4f} {token_r:<10.4f} {section_r:<10.4f} {mrr:<10.4f} {hit:<10.4f}")

    # Calculate improvement
    trad_chunk_r = avg_metric(results_traditional, "chunk_recall")
    lad_chunk_r = avg_metric(results_lad, "chunk_recall")
    trad_token_r = avg_metric(results_traditional, "token_recall")
    lad_token_r = avg_metric(results_lad, "token_recall")
    trad_section_r = avg_metric(results_traditional, "section_recall")
    lad_section_r = avg_metric(results_lad, "section_recall")

    log("\nLAD-RAG vs Traditional:")
    if trad_chunk_r > 0:
        chunk_imp = (lad_chunk_r - trad_chunk_r) / trad_chunk_r * 100
        log(f"  Chunk Recall: {chunk_imp:+.2f}%")
    if trad_token_r > 0:
        token_imp = (lad_token_r - trad_token_r) / trad_token_r * 100
        log(f"  Token Recall: {token_imp:+.2f}%")
    if trad_section_r > 0:
        section_imp = (lad_section_r - trad_section_r) / trad_section_r * 100
        log(f"  Section Recall: {section_imp:+.2f}%")


def main() -> None:
    """Main entry point."""
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
    model = None
    chunk_embeddings = None
    embeddings_by_doc: Dict[str, Any] = {}

    if HAS_EMBEDDINGS:
        log("Loading embedding model...")
        model = get_embedding_model()

        if model is not None:
            log("Computing chunk embeddings...")
            chunk_texts = [
                str(chunk.get("normalizedContent") or chunk.get("content") or "")
                for chunk in all_chunks
            ]
            chunk_embeddings = model.encode(chunk_texts, normalize_embeddings=True, show_progress_bar=True)
            log(f"Computed embeddings for {len(chunk_texts)} chunks")

            # Organize embeddings by document
            for idx, chunk in enumerate(all_chunks):
                doc_id = str(chunk.get("docId") or "")
                if doc_id not in embeddings_by_doc:
                    embeddings_by_doc[doc_id] = {"indices": [], "embeddings": []}
                embeddings_by_doc[doc_id]["indices"].append(idx)

            for doc_id, data in embeddings_by_doc.items():
                indices = data["indices"]
                data["embeddings"] = chunk_embeddings[indices]

    # Test multiple configurations
    all_results = {}

    # Config 1: LAD seed=5 (vector), total=15
    log("\n" + "="*60)
    log("Config 1: LAD seed=5 (vector) + expansion to 15 vs Traditional top-15")
    trad1, lad1 = run_comparison(
        test_cases, chunks_by_doc, embeddings_by_doc, model,
        total_chunks=15, lad_seed_k=5, seed_method="vector"
    )
    print_comparison("LAD seed=5 (vector) vs Traditional top-15", trad1, lad1)
    all_results["config1"] = {"traditional": trad1, "lad": lad1}

    # Config 2: LAD seed=5 (hybrid), total=15
    log("\n" + "="*60)
    log("Config 2: LAD seed=5 (hybrid) + expansion to 15 vs Traditional top-15")
    trad2, lad2 = run_comparison(
        test_cases, chunks_by_doc, embeddings_by_doc, model,
        total_chunks=15, lad_seed_k=5, seed_method="hybrid"
    )
    print_comparison("LAD seed=5 (hybrid) vs Traditional top-15", trad2, lad2)
    all_results["config2"] = {"traditional": trad2, "lad": lad2}

    # Config 3: LAD seed=8 (hybrid), total=15
    log("\n" + "="*60)
    log("Config 3: LAD seed=8 (hybrid) + expansion to 15 vs Traditional top-15")
    trad3, lad3 = run_comparison(
        test_cases, chunks_by_doc, embeddings_by_doc, model,
        total_chunks=15, lad_seed_k=8, seed_method="hybrid"
    )
    print_comparison("LAD seed=8 (hybrid) vs Traditional top-15", trad3, lad3)
    all_results["config3"] = {"traditional": trad3, "lad": lad3}

    # Config 4: LAD seed=5 (hybrid), total=20
    log("\n" + "="*60)
    log("Config 4: LAD seed=5 (hybrid) + expansion to 20 vs Traditional top-20")
    trad4, lad4 = run_comparison(
        test_cases, chunks_by_doc, embeddings_by_doc, model,
        total_chunks=20, lad_seed_k=5, seed_method="hybrid"
    )
    print_comparison("LAD seed=5 (hybrid) vs Traditional top-20", trad4, lad4)
    all_results["config4"] = {"traditional": trad4, "lad": lad4}

    # Save report
    report = {
        "generatedAt": datetime.now().isoformat(),
        "has_embeddings": HAS_EMBEDDINGS and model is not None,
        "results": all_results,
    }

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"\n\nReport saved to: {REPORT_PATH}")

    # Print summary table
    log("\n" + "="*80)
    log("SUMMARY: LAD-RAG vs Traditional RAG")
    log("="*80)
    log(f"{'Config':<35} {'Chunk R':<10} {'Token R':<10} {'Section R':<10}")
    log("-" * 65)

    for config_name, results in all_results.items():
        lad_results = results["lad"]
        chunk_r = avg_metric(lad_results, "chunk_recall")
        token_r = avg_metric(lad_results, "token_recall")
        section_r = avg_metric(lad_results, "section_recall")
        log(f"{'LAD ' + config_name:<35} {chunk_r:<10.4f} {token_r:<10.4f} {section_r:<10.4f}")

    # Traditional baseline
    trad_results = all_results["config1"]["traditional"]
    chunk_r = avg_metric(trad_results, "chunk_recall")
    token_r = avg_metric(trad_results, "token_recall")
    section_r = avg_metric(trad_results, "section_recall")
    log(f"{'Traditional (baseline)':<35} {chunk_r:<10.4f} {token_r:<10.4f} {section_r:<10.4f}")


if __name__ == "__main__":
    main()
