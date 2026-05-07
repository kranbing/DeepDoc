#!/usr/bin/env python3
"""
Test script for the optimized LAD-RAG strategy.

This script compares the optimized strategy with the baseline strategies
from the structural retrieval test.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Import the optimized strategy
from optimized_lad_rag_strategy import retrieve_and_format, build_vocabulary

# Import baseline strategies from structural test
from lad_rag_structural_test import (
    load_lad_data,
    extract_tokens,
    compute_metrics,
    retrieve_baseline_vector,
    retrieve_hybrid_vector_bm25,
    retrieve_structure_aware_reranking,
    retrieve_section_constrained,
    retrieve_hierarchical_expansion,
    retrieve_multi_level_structure,
)

ROOT = Path(__file__).resolve().parents[3]
LAD_DATA_DIR = ROOT / "test" / "lad_rag_test" / "data"
REPORT_PATH = Path(__file__).parent / "optimized_strategy_comparison.json"


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def run_strategy_evaluation(
    strategy_name: str,
    retrieve_func,
    test_cases: List[Dict[str, Any]],
    chunks_by_doc: Dict[str, List[Dict[str, Any]]],
    vocabulary: Dict[str, int],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Run evaluation for a single strategy."""
    results: List[Dict[str, Any]] = []

    for case in test_cases:
        doc_id = str(case.get("doc_id") or "")
        question = str(case.get("question") or "")
        evidence_chunk_ids = case.get("evidence_chunk_ids", [])
        evidence_texts = case.get("evidence_texts", [])

        chunks = chunks_by_doc.get(doc_id, [])
        if not chunks:
            results.append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "question": question,
                "strategy": strategy_name,
                "top_k": top_k,
                "error": "No chunks found for document",
                **{metric: 0.0 for metric in ["precision", "recall", "f1", "text_overlap", "mrr"]},
            })
            continue

        try:
            retrieved = retrieve_func(question, chunks, top_k, vocabulary)
            metrics = compute_metrics(retrieved, evidence_chunk_ids, evidence_texts)

            results.append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "question": question,
                "strategy": strategy_name,
                "top_k": top_k,
                "retrieved_count": len(retrieved),
                "evidence_count": len(evidence_chunk_ids),
                **metrics,
            })
        except Exception as exc:
            results.append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "question": question,
                "strategy": strategy_name,
                "top_k": top_k,
                "error": str(exc),
                **{metric: 0.0 for metric in ["precision", "recall", "f1", "text_overlap", "mrr"]},
            })

    return results


def optimized_retrieve_wrapper(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Wrapper for the optimized strategy to match the expected interface."""
    result = retrieve_and_format(
        query,
        chunks,
        top_k,
        use_structure_reranking=True,
        use_context_expansion=True,
    )

    # Convert back to the format expected by compute_metrics
    retrieved = []
    for item in result.get("results", []):
        # Find the original chunk to get full content
        original_chunk = None
        for chunk in chunks:
            if str(chunk.get("chunkId") or "") == item.get("chunkId"):
                original_chunk = chunk
                break

        if original_chunk:
            retrieved.append(original_chunk)
        else:
            # Use the formatted result as fallback
            retrieved.append({
                "chunkId": item.get("chunkId"),
                "normalizedContent": item.get("content"),
            })

    return retrieved


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize results by strategy."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in results:
        strategy = str(item.get("strategy"))
        groups.setdefault(strategy, []).append(item)

    summary: Dict[str, Any] = {}
    for strategy, items in groups.items():
        valid_items = [item for item in items if "error" not in item]
        if not valid_items:
            summary[strategy] = {
                "total": len(items),
                "valid": 0,
                "precision_avg": 0.0,
                "recall_avg": 0.0,
                "f1_avg": 0.0,
                "text_overlap_avg": 0.0,
                "mrr_avg": 0.0,
            }
            continue

        summary[strategy] = {
            "total": len(items),
            "valid": len(valid_items),
            "precision_avg": round(sum(float(item.get("precision") or 0) for item in valid_items) / len(valid_items), 4),
            "recall_avg": round(sum(float(item.get("recall") or 0) for item in valid_items) / len(valid_items), 4),
            "f1_avg": round(sum(float(item.get("f1") or 0) for item in valid_items) / len(valid_items), 4),
            "text_overlap_avg": round(sum(float(item.get("text_overlap") or 0) for item in valid_items) / len(valid_items), 4),
            "mrr_avg": round(sum(float(item.get("mrr") or 0) for item in valid_items) / len(valid_items), 4),
        }

    return summary


def main() -> None:
    """Main entry point."""
    log("Loading LAD data...")
    corpus, testset = load_lad_data()

    # Extract test cases
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

    # Build vocabulary
    log("Building vocabulary...")
    vocabulary = build_vocabulary(all_chunks)
    log(f"Vocabulary size: {len(vocabulary)}")

    # Define strategies to compare
    strategies = [
        ("baseline_vector", retrieve_baseline_vector),
        ("hybrid_vector_bm25", retrieve_hybrid_vector_bm25),
        ("multi_level_structure", retrieve_multi_level_structure),
        ("optimized_lad_rag", optimized_retrieve_wrapper),
    ]

    # Test with top_k=5 (common use case)
    top_k = 5
    log(f"Testing strategies with top_k={top_k}")

    # Run evaluations
    all_results: List[Dict[str, Any]] = []

    for strategy_name, retrieve_func in strategies:
        log(f"Evaluating strategy: {strategy_name}")
        results = run_strategy_evaluation(
            strategy_name, retrieve_func, test_cases, chunks_by_doc, vocabulary, top_k
        )
        all_results.extend(results)

    # Summarize results
    log("Summarizing results...")
    summary = summarize_results(all_results)

    # Generate comparison report
    log("Generating comparison report...")
    report = {
        "generatedAt": datetime.now().isoformat(),
        "top_k": top_k,
        "summary": summary,
        "results": all_results,
    }

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"Comparison report saved to: {REPORT_PATH}")

    # Print summary table
    log("\n=== Strategy Comparison (top_k=5) ===")
    log(f"{'Strategy':<30} {'Precision':<10} {'Recall':<10} {'F1':<10} {'MRR':<10}")
    log("-" * 70)

    for strategy, metrics in sorted(summary.items()):
        log(f"{strategy:<30} {metrics['precision_avg']:<10.4f} {metrics['recall_avg']:<10.4f} "
            f"{metrics['f1_avg']:<10.4f} {metrics['mrr_avg']:<10.4f}")

    # Calculate improvement
    if "multi_level_structure" in summary and "optimized_lad_rag" in summary:
        baseline = summary["multi_level_structure"]
        optimized = summary["optimized_lad_rag"]

        log("\n=== Improvement over best baseline (multi_level_structure) ===")
        for metric in ["precision_avg", "recall_avg", "f1_avg", "mrr_avg"]:
            baseline_val = baseline[metric]
            optimized_val = optimized[metric]
            if baseline_val > 0:
                improvement = ((optimized_val - baseline_val) / baseline_val) * 100
                log(f"{metric}: {baseline_val:.4f} -> {optimized_val:.4f} ({improvement:+.2f}%)")


if __name__ == "__main__":
    main()
