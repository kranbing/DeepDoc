#!/usr/bin/env python3
"""
LAD-RAG with Real Embeddings

This version uses sentence-transformers for semantic embedding,
which should significantly improve retrieval quality.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[3]
LAD_DATA_DIR = ROOT / "test" / "lad_rag_test" / "data"
REPORT_PATH = Path(__file__).parent / "lad_rag_embeddings_report.json"

# Try to import embedding dependencies
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("WARNING: sentence-transformers not installed. Using TF-IDF fallback.")


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
    """Extract tokens for lexical matching."""
    raw = str(text or "").lower()
    tokens = re.findall(r"[a-z0-9]+|[一-鿿]{2,}", raw)
    return [t for t in tokens if t.strip()]


def get_embedding_model():
    """Load embedding model."""
    if not HAS_EMBEDDINGS:
        return None

    # Try to load a local model first
    model_paths = [
        ROOT / "models" / "BAAI" / "bge-small-zh-v1.5",
        ROOT / "models" / "all-MiniLM-L6-v2",
    ]

    for model_path in model_paths:
        if model_path.exists():
            log(f"Loading embedding model from: {model_path}")
            return SentenceTransformer(str(model_path))

    # Fallback to downloading
    log("Loading embedding model: all-MiniLM-L6-v2")
    return SentenceTransformer("all-MiniLM-L6-v2")


def compute_cosine_similarity(vec1, vec2) -> float:
    """Compute cosine similarity between two vectors."""
    if vec1 is None or vec2 is None:
        return 0.0

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def compute_bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    doc_len: int,
    avgdl: float,
    n_docs: int,
    doc_freq: Dict[str, int],
) -> float:
    """Compute BM25 score."""
    k1 = 1.2
    b = 0.75

    tf = Counter(doc_tokens)
    score = 0.0

    for term in set(query_tokens):
        if term not in tf:
            continue

        df = doc_freq.get(term, 0)
        if df <= 0:
            continue

        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
        freq = tf[term]
        tf_component = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (doc_len / avgdl)))
        score += idf * tf_component

    return score


def compute_structure_score(query_tokens: set, chunk: Dict[str, Any]) -> float:
    """Compute structure matching score."""
    if not query_tokens:
        return 0.0

    # Heading match (most important for academic papers)
    heading_text = str(chunk.get("headingText") or "")
    heading_tokens = set(extract_tokens(heading_text))
    heading_match = len(query_tokens & heading_tokens) / max(len(query_tokens), 1)

    # Section path match
    section_path = str(chunk.get("sectionPathText") or "")
    section_tokens = set(extract_tokens(section_path))
    section_match = len(query_tokens & section_tokens) / max(len(query_tokens), 1)

    # Weighted combination
    score = 0.5 * heading_match + 0.3 * section_match

    # Bonus for having heading
    if heading_text.strip():
        score += 0.1

    return min(1.0, score)


def retrieve_with_embeddings(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    model=None,
    chunk_embeddings=None,
    *,
    use_bm25: bool = True,
    use_structure: bool = True,
    bm25_weight: float = 0.3,
    embedding_weight: float = 0.7,
    structure_weight: float = 0.15,
) -> List[Dict[str, Any]]:
    """
    Retrieve using embeddings + BM25 + structure scoring.
    """
    if not chunks:
        return []

    query_tokens = extract_tokens(query)
    query_set = set(query_tokens)

    # Compute BM25 statistics
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

    # Compute query embedding
    query_embedding = None
    if model is not None:
        query_embedding = model.encode(query, normalize_embeddings=True)

    # Score all chunks
    scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

    for idx, chunk in enumerate(chunks):
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        chunk_tokens = all_doc_tokens[idx]

        # Embedding similarity
        embedding_sim = 0.0
        if query_embedding is not None and chunk_embeddings is not None:
            embedding_sim = compute_cosine_similarity(query_embedding, chunk_embeddings[idx])

        # BM25 score
        bm25_score = 0.0
        if use_bm25:
            bm25_score = compute_bm25_score(
                query_tokens, chunk_tokens, doc_lens[idx], avgdl, n_docs, doc_freq
            )
            bm25_score = min(1.0, bm25_score / max(1, len(query_tokens)))

        # Structure score
        structure_score = 0.0
        if use_structure:
            structure_score = compute_structure_score(query_set, chunk)

        # Combine scores
        if model is not None:
            # With embeddings: use embedding as primary signal
            final_score = embedding_weight * embedding_sim + bm25_weight * bm25_score + structure_weight * structure_score
        else:
            # Without embeddings: use BM25 as primary signal
            final_score = 0.6 * bm25_score + 0.4 * structure_score

        if final_score > 0:
            item = dict(chunk)
            item["score"] = round(final_score, 6)
            item["embedding_score"] = round(embedding_sim, 6)
            item["bm25_score"] = round(bm25_score, 6)
            item["structure_score"] = round(structure_score, 6)
            scored_chunks.append((final_score, item))

    # Sort and return top_k
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_chunks[:top_k]]


def compute_metrics(
    retrieved: List[Dict[str, Any]],
    evidence_chunk_ids: List[str],
) -> Dict[str, Any]:
    """Compute retrieval metrics."""
    retrieved_ids = {str(chunk.get("chunkId") or "") for chunk in retrieved}
    evidence_set = set(evidence_chunk_ids)

    # Chunk-level metrics
    hits = len(retrieved_ids & evidence_set)
    precision = hits / max(len(retrieved), 1)
    recall = hits / max(len(evidence_set), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-6)

    # MRR (Mean Reciprocal Rank)
    mrr = 0.0
    for i, chunk in enumerate(retrieved):
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in evidence_set:
            mrr = 1.0 / (i + 1)
            break

    return {
        "hits": hits,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "mrr": round(mrr, 4),
    }


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

    # Test different configurations
    configs = [
        {"name": "bm25_only", "use_bm25": True, "use_structure": False, "bm25_weight": 1.0, "embedding_weight": 0.0, "structure_weight": 0.0},
        {"name": "embedding_only", "use_bm25": False, "use_structure": False, "bm25_weight": 0.0, "embedding_weight": 1.0, "structure_weight": 0.0},
        {"name": "hybrid_no_structure", "use_bm25": True, "use_structure": False, "bm25_weight": 0.3, "embedding_weight": 0.7, "structure_weight": 0.0},
        {"name": "hybrid_with_structure", "use_bm25": True, "use_structure": True, "bm25_weight": 0.25, "embedding_weight": 0.6, "structure_weight": 0.15},
    ]

    top_k = 5
    all_results: Dict[str, List[Dict[str, Any]]] = {}

    for config in configs:
        config_name = config["name"]
        log(f"\n=== Testing configuration: {config_name} ===")

        results: List[Dict[str, Any]] = []

        for case in test_cases:
            doc_id = str(case.get("doc_id") or "")
            question = str(case.get("question") or "")
            evidence_chunk_ids = case.get("evidence_chunk_ids", [])

            chunks = chunks_by_doc.get(doc_id, [])
            if not chunks:
                continue

            # Get embeddings for this document's chunks
            doc_chunk_embeddings = None
            if chunk_embeddings is not None:
                # Find indices of chunks for this document
                doc_indices = []
                for i, chunk in enumerate(all_chunks):
                    if str(chunk.get("docId") or "") == doc_id:
                        doc_indices.append(i)

                if doc_indices:
                    doc_chunk_embeddings = chunk_embeddings[doc_indices]

            # Retrieve
            retrieved = retrieve_with_embeddings(
                question,
                chunks,
                top_k,
                model=model,
                chunk_embeddings=doc_chunk_embeddings,
                use_bm25=config["use_bm25"],
                use_structure=config["use_structure"],
                bm25_weight=config["bm25_weight"],
                embedding_weight=config["embedding_weight"],
                structure_weight=config["structure_weight"],
            )

            # Compute metrics
            metrics = compute_metrics(retrieved, evidence_chunk_ids)

            results.append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "question": question,
                "config": config_name,
                "top_k": top_k,
                "evidence_count": len(evidence_chunk_ids),
                **metrics,
            })

        all_results[config_name] = results

        # Print summary for this config
        valid_results = [r for r in results if "error" not in r]
        if valid_results:
            avg_precision = sum(r["precision"] for r in valid_results) / len(valid_results)
            avg_recall = sum(r["recall"] for r in valid_results) / len(valid_results)
            avg_f1 = sum(r["f1"] for r in valid_results) / len(valid_results)
            avg_mrr = sum(r["mrr"] for r in valid_results) / len(valid_results)

            log(f"  Precision: {avg_precision:.4f}")
            log(f"  Recall: {avg_recall:.4f}")
            log(f"  F1: {avg_f1:.4f}")
            log(f"  MRR: {avg_mrr:.4f}")

    # Save report
    report = {
        "generatedAt": datetime.now().isoformat(),
        "top_k": top_k,
        "has_embeddings": HAS_EMBEDDINGS and model is not None,
        "results": all_results,
    }

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"\nReport saved to: {REPORT_PATH}")

    # Print comparison table
    log("\n=== Configuration Comparison ===")
    log(f"{'Configuration':<25} {'Precision':<10} {'Recall':<10} {'F1':<10} {'MRR':<10}")
    log("-" * 65)

    for config_name, results in all_results.items():
        valid_results = [r for r in results if "error" not in r]
        if valid_results:
            avg_precision = sum(r["precision"] for r in valid_results) / len(valid_results)
            avg_recall = sum(r["recall"] for r in valid_results) / len(valid_results)
            avg_f1 = sum(r["f1"] for r in valid_results) / len(valid_results)
            avg_mrr = sum(r["mrr"] for r in valid_results) / len(valid_results)

            log(f"{config_name:<25} {avg_precision:<10.4f} {avg_recall:<10.4f} {avg_f1:<10.4f} {avg_mrr:<10.4f}")


if __name__ == "__main__":
    main()
