#!/usr/bin/env python3
"""
Improved LAD-RAG Evaluation

This version uses more lenient evaluation metrics:
1. Top-k recall (evidence found within top-k results)
2. Text overlap (token-level overlap between retrieved and evidence)
3. Section-level accuracy (evidence sections found)
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[3]
LAD_DATA_DIR = ROOT / "test" / "8-lad_rag_test" / "data"
REPORT_PATH = Path(__file__).parent / "lad_rag_improved_eval_report.json"


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


def compute_improved_metrics(
    retrieved: List[Dict[str, Any]],
    evidence_chunk_ids: List[str],
    evidence_texts: List[str],
    evidence_section_ids: List[str],
    all_chunks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute improved evaluation metrics.

    1. Chunk-level recall (strict)
    2. Text overlap (lenient)
    3. Section-level recall
    4. Semantic similarity (token overlap)
    """
    retrieved_ids = {str(chunk.get("chunkId") or "") for chunk in retrieved}
    evidence_set = set(evidence_chunk_ids)

    # 1. Chunk-level recall (strict)
    chunk_hits = len(retrieved_ids & evidence_set)
    chunk_recall = chunk_hits / max(len(evidence_set), 1)

    # 2. Text overlap (lenient)
    # Combine all retrieved text
    retrieved_text = " ".join(
        str(chunk.get("normalizedContent") or chunk.get("content") or "")
        for chunk in retrieved
    )
    retrieved_tokens = set(extract_tokens(retrieved_text))

    # Combine all evidence text
    evidence_text = " ".join(evidence_texts)
    evidence_tokens = set(extract_tokens(evidence_text))

    # Token-level overlap
    token_overlap = len(retrieved_tokens & evidence_tokens)
    token_recall = token_overlap / max(len(evidence_tokens), 1)
    token_precision = token_overlap / max(len(retrieved_tokens), 1)
    token_f1 = 2 * token_precision * token_recall / max(token_precision + token_recall, 1e-6)

    # 3. Section-level recall
    retrieved_sections = set()
    for chunk in retrieved:
        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            retrieved_sections.add(section_id)

    evidence_sections = set(evidence_section_ids)
    section_hits = len(retrieved_sections & evidence_sections)
    section_recall = section_hits / max(len(evidence_sections), 1)

    # 4. MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for i, chunk in enumerate(retrieved):
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in evidence_set:
            mrr = 1.0 / (i + 1)
            break

    # 5. Top-k accuracy (any evidence in top-k)
    top_k_hit = 1.0 if chunk_hits > 0 else 0.0

    return {
        "chunk_recall": round(chunk_recall, 4),
        "token_recall": round(token_recall, 4),
        "token_precision": round(token_precision, 4),
        "token_f1": round(token_f1, 4),
        "section_recall": round(section_recall, 4),
        "mrr": round(mrr, 4),
        "top_k_hit": round(top_k_hit, 4),
        "chunk_hits": chunk_hits,
        "token_overlap": token_overlap,
        "section_hits": section_hits,
    }


def retrieve_bm25(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Retrieve using BM25."""
    import math

    query_tokens = extract_tokens(query)
    if not query_tokens:
        return chunks[:top_k]

    # Compute BM25 statistics
    k1 = 1.2
    b = 0.75

    doc_lens = []
    all_doc_tokens = []
    doc_freq: Dict[str, int] = {}

    for chunk in chunks:
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        tokens = extract_tokens(content)
        doc_lens.append(len(tokens))
        all_doc_tokens.append(tokens)

        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1

    avgdl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(chunks)

    # Score chunks
    scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

    for idx, chunk in enumerate(chunks):
        tokens = all_doc_tokens[idx]
        tf = Counter(tokens)
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

        if score > 0:
            item = dict(chunk)
            item["score"] = score
            scored_chunks.append((score, item))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_chunks[:top_k]]


def retrieve_hybrid(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    chunk_embeddings=None,
    model=None,
) -> List[Dict[str, Any]]:
    """Retrieve using hybrid (embedding + BM25)."""
    import math
    import numpy as np

    query_tokens = extract_tokens(query)
    if not query_tokens:
        return chunks[:top_k]

    # BM25 component
    k1 = 1.2
    b = 0.75

    doc_lens = []
    all_doc_tokens = []
    doc_freq: Dict[str, int] = {}

    for chunk in chunks:
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        tokens = extract_tokens(content)
        doc_lens.append(len(tokens))
        all_doc_tokens.append(tokens)

        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1

    avgdl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(chunks)

    # Compute query embedding
    query_embedding = None
    if model is not None and chunk_embeddings is not None:
        query_embedding = model.encode(query, normalize_embeddings=True)

    # Score chunks
    scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

    for idx, chunk in enumerate(chunks):
        tokens = all_doc_tokens[idx]
        tf = Counter(tokens)

        # BM25 score
        bm25_score = 0.0
        for term in set(query_tokens):
            if term not in tf:
                continue

            df = doc_freq.get(term, 0)
            if df <= 0:
                continue

            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
            freq = tf[term]
            tf_component = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (doc_lens[idx] / avgdl)))
            bm25_score += idf * tf_component

        # Embedding score
        embedding_score = 0.0
        if query_embedding is not None and chunk_embeddings is not None and idx < len(chunk_embeddings):
            embedding_score = float(np.dot(query_embedding, chunk_embeddings[idx]))

        # Combine scores
        if query_embedding is not None:
            final_score = 0.3 * bm25_score + 0.7 * embedding_score
        else:
            final_score = bm25_score

        if final_score > 0:
            item = dict(chunk)
            item["score"] = final_score
            item["bm25_score"] = bm25_score
            item["embedding_score"] = embedding_score
            scored_chunks.append((final_score, item))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_chunks[:top_k]]


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

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer

        log("Loading embedding model...")
        model_paths = [
            ROOT / "models" / "all-MiniLM-L6-v2",
            ROOT / "models" / "BAAI" / "bge-small-zh-v1.5",
        ]

        for model_path in model_paths:
            if model_path.exists():
                log(f"Loading from: {model_path}")
                model = SentenceTransformer(str(model_path))
                break

        if model is None:
            log("Loading all-MiniLM-L6-v2 from HuggingFace...")
            model = SentenceTransformer("all-MiniLM-L6-v2")

        log("Computing chunk embeddings...")
        chunk_texts = [
            str(chunk.get("normalizedContent") or chunk.get("content") or "")
            for chunk in all_chunks
        ]
        chunk_embeddings = model.encode(chunk_texts, normalize_embeddings=True, show_progress_bar=True)
        log(f"Computed embeddings for {len(chunk_texts)} chunks")

    except ImportError:
        log("WARNING: sentence-transformers not available, using BM25 only")
    except Exception as e:
        log(f"WARNING: Failed to load embedding model: {e}")

    # Test different top_k values
    top_k_values = [3, 5, 10, 15, 20]

    # Results storage
    all_results: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        "bm25": {},
        "hybrid": {},
    }

    for top_k in top_k_values:
        log(f"\n=== Testing top_k={top_k} ===")

        # BM25 results
        bm25_results: List[Dict[str, Any]] = []
        # Hybrid results
        hybrid_results: List[Dict[str, Any]] = []

        for case in test_cases:
            doc_id = str(case.get("doc_id") or "")
            question = str(case.get("question") or "")
            evidence_chunk_ids = case.get("evidence_chunk_ids", [])
            evidence_texts = case.get("evidence_texts", [])
            evidence_section_ids = case.get("evidence_section_ids", [])

            chunks = chunks_by_doc.get(doc_id, [])
            if not chunks:
                continue

            # Get embeddings for this document
            doc_chunk_embeddings = None
            if chunk_embeddings is not None:
                doc_indices = [i for i, c in enumerate(all_chunks) if str(c.get("docId") or "") == doc_id]
                if doc_indices:
                    doc_chunk_embeddings = chunk_embeddings[doc_indices]

            # BM25 retrieval
            bm25_retrieved = retrieve_bm25(question, chunks, top_k)
            bm25_metrics = compute_improved_metrics(
                bm25_retrieved, evidence_chunk_ids, evidence_texts, evidence_section_ids, chunks
            )

            bm25_results.append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "question": question,
                "top_k": top_k,
                "evidence_count": len(evidence_chunk_ids),
                **bm25_metrics,
            })

            # Hybrid retrieval
            hybrid_retrieved = retrieve_hybrid(
                question, chunks, top_k,
                chunk_embeddings=doc_chunk_embeddings,
                model=model,
            )
            hybrid_metrics = compute_improved_metrics(
                hybrid_retrieved, evidence_chunk_ids, evidence_texts, evidence_section_ids, chunks
            )

            hybrid_results.append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "question": question,
                "top_k": top_k,
                "evidence_count": len(evidence_chunk_ids),
                **hybrid_metrics,
            })

        all_results["bm25"][str(top_k)] = bm25_results
        all_results["hybrid"][str(top_k)] = hybrid_results

        # Print summary
        for method, results in [("BM25", bm25_results), ("Hybrid", hybrid_results)]:
            if results:
                avg_chunk_recall = sum(r["chunk_recall"] for r in results) / len(results)
                avg_token_recall = sum(r["token_recall"] for r in results) / len(results)
                avg_token_f1 = sum(r["token_f1"] for r in results) / len(results)
                avg_section_recall = sum(r["section_recall"] for r in results) / len(results)
                avg_mrr = sum(r["mrr"] for r in results) / len(results)
                avg_top_k_hit = sum(r["top_k_hit"] for r in results) / len(results)

                log(f"\n{method} (top_k={top_k}):")
                log(f"  Chunk Recall: {avg_chunk_recall:.4f}")
                log(f"  Token Recall: {avg_token_recall:.4f}")
                log(f"  Token F1: {avg_token_f1:.4f}")
                log(f"  Section Recall: {avg_section_recall:.4f}")
                log(f"  MRR: {avg_mrr:.4f}")
                log(f"  Top-K Hit Rate: {avg_top_k_hit:.4f}")

    # Save report
    report = {
        "generatedAt": datetime.now().isoformat(),
        "has_embeddings": model is not None,
        "results": all_results,
    }

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"\nReport saved to: {REPORT_PATH}")

    # Print comparison table
    log("\n=== Summary Comparison ===")
    log(f"{'Method':<10} {'Top-K':<8} {'Chunk R':<10} {'Token R':<10} {'Token F1':<10} {'Section R':<10} {'MRR':<10} {'Hit Rate':<10}")
    log("-" * 80)

    for method in ["bm25", "hybrid"]:
        for top_k in top_k_values:
            results = all_results[method].get(str(top_k), [])
            if results:
                avg_chunk_recall = sum(r["chunk_recall"] for r in results) / len(results)
                avg_token_recall = sum(r["token_recall"] for r in results) / len(results)
                avg_token_f1 = sum(r["token_f1"] for r in results) / len(results)
                avg_section_recall = sum(r["section_recall"] for r in results) / len(results)
                avg_mrr = sum(r["mrr"] for r in results) / len(results)
                avg_top_k_hit = sum(r["top_k_hit"] for r in results) / len(results)

                log(f"{method:<10} {top_k:<8} {avg_chunk_recall:<10.4f} {avg_token_recall:<10.4f} "
                    f"{avg_token_f1:<10.4f} {avg_section_recall:<10.4f} {avg_mrr:<10.4f} {avg_top_k_hit:<10.4f}")


if __name__ == "__main__":
    main()
