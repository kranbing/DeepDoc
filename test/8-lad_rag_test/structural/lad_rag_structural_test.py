#!/usr/bin/env python3
"""
LAD-RAG Structural Retrieval Test Framework

This script evaluates different structural retrieval strategies using LAD (Layout-Aware Document)
structure indices from the Qasper dataset. It compares various approaches to leverage document
structure for improved retrieval accuracy.

Strategies tested:
1. baseline_vector: Pure vector similarity (no structure)
2. hybrid_vector_bm25: Vector + BM25 lexical matching
3. structure_aware_reranking: Use section path matching for reranking
4. section_constrained: Only retrieve from relevant sections
5. hierarchical_expansion: Use section hierarchy for context expansion
6. multi_level_structure: Match at different structural levels (section, heading, block type)
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
REPORT_JSON_PATH = Path(__file__).parent / "lad_rag_structural_report.json"
REPORT_MD_PATH = Path(__file__).parent / "lad_rag_structural_report.md"


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def load_lad_data() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load LAD corpus and testset."""
    corpus_path = LAD_DATA_DIR / "qasper_lad_corpus.json"
    testset_path = LAD_DATA_DIR / "qasper_lad_testset.json"

    if not corpus_path.exists() or not testset_path.exists():
        raise FileNotFoundError(
            f"LAD data not found. Run prepare_qasper_lad.py first.\n"
            f"Expected: {corpus_path}\n"
            f"Expected: {testset_path}"
        )

    with corpus_path.open("r", encoding="utf-8") as f:
        corpus = json.load(f)
    with testset_path.open("r", encoding="utf-8") as f:
        testset = json.load(f)

    return corpus, testset


def extract_tokens(text: str) -> List[str]:
    """Extract tokens from text for lexical matching."""
    raw = str(text or "")
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[一-鿿]{2,}|\d+(?:\.\d+)?%?", raw)
    return [t.lower() for t in tokens if str(t).strip()]


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    text = str(text or "").lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w一-鿿]", "", text)
    return text


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def simple_tfidf_vector(tokens: List[str], vocabulary: Dict[str, int]) -> List[float]:
    """Create a simple TF-IDF vector."""
    tf = Counter(tokens)
    total = len(tokens) if tokens else 1

    vector = [0.0] * len(vocabulary)
    for token, count in tf.items():
        if token in vocabulary:
            # Simple TF-IDF: tf * idf (using log of inverse document frequency approximation)
            tf_score = count / total
            idf_score = math.log(1 + 1 / (1 + count))  # Simplified IDF
            vector[vocabulary[token]] = tf_score * idf_score

    return vector


def build_vocabulary(chunks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Build vocabulary from chunks."""
    vocab: Dict[str, int] = {}
    for chunk in chunks:
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        tokens = extract_tokens(content)
        for token in tokens:
            if token not in vocab:
                vocab[token] = len(vocab)
    return vocab


def retrieve_baseline_vector(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Strategy 1: Pure vector similarity (TF-IDF based)."""
    query_tokens = extract_tokens(query)
    query_vec = simple_tfidf_vector(query_tokens, vocabulary)

    scored_chunks: List[Tuple[float, Dict[str, Any]]] = []
    for chunk in chunks:
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        chunk_tokens = extract_tokens(content)
        chunk_vec = simple_tfidf_vector(chunk_tokens, vocabulary)

        similarity = compute_cosine_similarity(query_vec, chunk_vec)
        if similarity > 0:
            item = dict(chunk)
            item["score"] = similarity
            scored_chunks.append((similarity, item))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_chunks[:top_k]]


def retrieve_hybrid_vector_bm25(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Strategy 2: Vector + BM25 lexical matching."""
    query_tokens = extract_tokens(query)
    query_vec = simple_tfidf_vector(query_tokens, vocabulary)
    query_set = set(query_tokens)

    # BM25 parameters
    k1 = 1.2
    b = 0.75

    # Calculate document lengths and average
    doc_lens = []
    for chunk in chunks:
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        tokens = extract_tokens(content)
        doc_lens.append(len(tokens))

    avgdl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(chunks)

    # Calculate IDF for query terms
    idf_scores: Dict[str, float] = {}
    for term in query_set:
        df = sum(1 for chunk in chunks
                if term in extract_tokens(str(chunk.get("normalizedContent") or chunk.get("content") or "")))
        idf_scores[term] = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))

    scored_chunks: List[Tuple[float, Dict[str, Any]]] = []
    for idx, chunk in enumerate(chunks):
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        chunk_tokens = extract_tokens(content)
        chunk_vec = simple_tfidf_vector(chunk_tokens, vocabulary)

        # Vector similarity
        vector_sim = compute_cosine_similarity(query_vec, chunk_vec)

        # BM25 score
        tf = Counter(chunk_tokens)
        dl = doc_lens[idx]
        bm25_score = 0.0
        for term in query_set:
            if term in tf:
                freq = tf[term]
                idf = idf_scores.get(term, 0)
                tf_component = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (dl / avgdl)))
                bm25_score += idf * tf_component

        # Normalize BM25 score to [0, 1] range
        bm25_normalized = min(1.0, bm25_score / max(1, len(query_tokens)))

        # Hybrid score: 0.6 vector + 0.4 BM25
        hybrid_score = 0.6 * vector_sim + 0.4 * bm25_normalized

        if hybrid_score > 0:
            item = dict(chunk)
            item["score"] = hybrid_score
            item["vector_score"] = vector_sim
            item["bm25_score"] = bm25_normalized
            scored_chunks.append((hybrid_score, item))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_chunks[:top_k]]


def retrieve_structure_aware_reranking(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Strategy 3: Use section path matching for reranking."""
    # First get initial candidates using hybrid approach
    initial_k = min(top_k * 3, len(chunks))
    candidates = retrieve_hybrid_vector_bm25(query, chunks, initial_k, vocabulary)

    query_tokens = set(extract_tokens(query))

    # Rerank based on structure matching
    reranked: List[Tuple[float, Dict[str, Any]]] = []
    for item in candidates:
        base_score = float(item.get("score") or 0)

        # Get structure information
        section_path = str(item.get("sectionPathText") or "")
        heading_text = str(item.get("headingText") or "")
        block_type = str(item.get("blockType") or "")

        # Extract structure tokens
        structure_text = f"{section_path} {heading_text} {block_type}"
        structure_tokens = set(extract_tokens(structure_text))

        # Calculate structure match score
        structure_overlap = len(query_tokens & structure_tokens)
        structure_score = structure_overlap / max(len(query_tokens), 1)

        # Bonus for heading matches
        heading_bonus = 0.0
        if heading_text:
            heading_tokens = set(extract_tokens(heading_text))
            if query_tokens & heading_tokens:
                heading_bonus = 0.1

        # Bonus for section path matches
        section_bonus = 0.0
        if section_path:
            section_tokens = set(extract_tokens(section_path))
            if query_tokens & section_tokens:
                section_bonus = 0.05

        # Final score: base + structure components
        final_score = base_score + 0.2 * structure_score + heading_bonus + section_bonus

        item = dict(item)
        item["score"] = final_score
        item["structure_score"] = structure_score
        reranked.append((final_score, item))

    reranked.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in reranked[:top_k]]


def retrieve_section_constrained(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Strategy 4: Only retrieve from relevant sections."""
    query_tokens = set(extract_tokens(query))

    # First, identify relevant sections based on query
    section_relevance: Dict[str, float] = defaultdict(float)
    for chunk in chunks:
        section_path = str(chunk.get("sectionPathText") or "")
        heading_text = str(chunk.get("headingText") or "")

        if not section_path and not heading_text:
            continue

        structure_text = f"{section_path} {heading_text}"
        structure_tokens = set(extract_tokens(structure_text))

        overlap = len(query_tokens & structure_tokens)
        if overlap > 0:
            section_id = str(chunk.get("sectionId") or "")
            if section_id:
                section_relevance[section_id] = max(section_relevance[section_id],
                                                    overlap / max(len(query_tokens), 1))

    # If no sections match, fall back to hybrid approach
    if not section_relevance:
        return retrieve_hybrid_vector_bm25(query, chunks, top_k, vocabulary)

    # Get top relevant sections
    relevant_sections = sorted(section_relevance.items(), key=lambda x: x[1], reverse=True)[:5]
    relevant_section_ids = {section_id for section_id, _ in relevant_sections}

    # Filter chunks to relevant sections
    filtered_chunks = [
        chunk for chunk in chunks
        if str(chunk.get("sectionId") or "") in relevant_section_ids
    ]

    # If too few chunks, expand to include more
    if len(filtered_chunks) < top_k:
        # Add chunks from adjacent sections
        all_section_ids = list(set(str(chunk.get("sectionId") or "") for chunk in chunks))
        for section_id in all_section_ids:
            if section_id not in relevant_section_ids:
                filtered_chunks.extend([
                    chunk for chunk in chunks
                    if str(chunk.get("sectionId") or "") == section_id
                ])
                if len(filtered_chunks) >= top_k * 2:
                    break

    # Apply hybrid retrieval on filtered chunks
    return retrieve_hybrid_vector_bm25(query, filtered_chunks, top_k, vocabulary)


def retrieve_hierarchical_expansion(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Strategy 5: Use section hierarchy for context expansion."""
    # First get initial results
    initial_k = max(1, top_k // 2)
    initial_results = retrieve_hybrid_vector_bm25(query, chunks, initial_k, vocabulary)

    if not initial_results:
        return []

    # Get section IDs of initial results
    initial_section_ids = set()
    for item in initial_results:
        section_id = str(item.get("sectionId") or "")
        if section_id:
            initial_section_ids.add(section_id)

    # Expand to include neighboring sections
    expanded_chunks: List[Dict[str, Any]] = []
    for chunk in chunks:
        section_id = str(chunk.get("sectionId") or "")

        # Include chunks from initial sections
        if section_id in initial_section_ids:
            expanded_chunks.append(chunk)
            continue

        # Include chunks from parent/child sections (simplified: sections with similar paths)
        section_path = str(chunk.get("sectionPathText") or "")
        for initial_section_id in initial_section_ids:
            # Find a chunk from initial section to get its path
            initial_chunk = next(
                (c for c in chunks if str(c.get("sectionId") or "") == initial_section_id),
                None
            )
            if initial_chunk:
                initial_path = str(initial_chunk.get("sectionPathText") or "")
                # Check if paths share common prefix
                if section_path and initial_path:
                    # Simple hierarchy check: share first path component
                    section_parts = section_path.split(":::")
                    initial_parts = initial_path.split(":::")
                    if section_parts[0].strip() == initial_parts[0].strip():
                        expanded_chunks.append(chunk)
                        break

    # Apply hybrid retrieval on expanded chunks
    return retrieve_hybrid_vector_bm25(query, expanded_chunks, top_k, vocabulary)


def retrieve_multi_level_structure(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
) -> List[Dict[str, Any]]:
    """Strategy 6: Match at different structural levels."""
    query_tokens = set(extract_tokens(query))

    # Get initial candidates using hybrid approach
    initial_k = min(top_k * 3, len(chunks))
    candidates = retrieve_hybrid_vector_bm25(query, chunks, initial_k, vocabulary)

    # Score at different structural levels
    reranked: List[Tuple[float, Dict[str, Any]]] = []
    for item in candidates:
        base_score = float(item.get("score") or 0)

        # Level 1: Document level (doc name matching)
        doc_name = str(item.get("docName") or "")
        doc_tokens = set(extract_tokens(doc_name))
        doc_match = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)

        # Level 2: Section level (section path matching)
        section_path = str(item.get("sectionPathText") or "")
        section_tokens = set(extract_tokens(section_path))
        section_match = len(query_tokens & section_tokens) / max(len(query_tokens), 1)

        # Level 3: Heading level (heading text matching)
        heading_text = str(item.get("headingText") or "")
        heading_tokens = set(extract_tokens(heading_text))
        heading_match = len(query_tokens & heading_tokens) / max(len(query_tokens), 1)

        # Level 4: Block type level
        block_type = str(item.get("blockType") or "")
        block_tokens = set(extract_tokens(block_type))
        block_match = len(query_tokens & block_tokens) / max(len(query_tokens), 1)

        # Weighted combination of different levels
        structure_score = (
            0.1 * doc_match +
            0.3 * section_match +
            0.4 * heading_match +
            0.2 * block_match
        )

        # Final score
        final_score = base_score + 0.3 * structure_score

        item = dict(item)
        item["score"] = final_score
        item["doc_match"] = doc_match
        item["section_match"] = section_match
        item["heading_match"] = heading_match
        item["block_match"] = block_match
        reranked.append((final_score, item))

    reranked.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in reranked[:top_k]]


def compute_metrics(
    retrieved: List[Dict[str, Any]],
    evidence_chunk_ids: List[str],
    evidence_texts: List[str],
) -> Dict[str, Any]:
    """Compute retrieval metrics."""
    retrieved_ids = {str(chunk.get("chunkId") or "") for chunk in retrieved}
    evidence_set = set(evidence_chunk_ids)

    # Chunk-level metrics
    hits = len(retrieved_ids & evidence_set)
    precision = hits / max(len(retrieved), 1)
    recall = hits / max(len(evidence_set), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-6)

    # Text overlap metrics
    retrieved_text = " ".join(str(chunk.get("normalizedContent") or chunk.get("content") or "")
                            for chunk in retrieved)
    retrieved_tokens = set(extract_tokens(retrieved_text))

    evidence_text = " ".join(evidence_texts)
    evidence_tokens = set(extract_tokens(evidence_text))

    text_overlap = len(retrieved_tokens & evidence_tokens) / max(len(evidence_tokens), 1)

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
        "text_overlap": round(text_overlap, 4),
        "mrr": round(mrr, 4),
    }


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


def summarize_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize results by strategy and top_k."""
    groups: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    for item in results:
        key = (str(item.get("strategy")), int(item.get("top_k")))
        groups.setdefault(key, []).append(item)

    summary: List[Dict[str, Any]] = []
    for (strategy, top_k), items in sorted(groups.items()):
        total = len(items)
        valid_items = [item for item in items if "error" not in item]

        if not valid_items:
            summary.append({
                "strategy": strategy,
                "top_k": top_k,
                "total": total,
                "valid": 0,
                "precision_avg": 0.0,
                "recall_avg": 0.0,
                "f1_avg": 0.0,
                "text_overlap_avg": 0.0,
                "mrr_avg": 0.0,
            })
            continue

        summary.append({
            "strategy": strategy,
            "top_k": top_k,
            "total": total,
            "valid": len(valid_items),
            "precision_avg": round(sum(float(item.get("precision") or 0) for item in valid_items) / len(valid_items), 4),
            "recall_avg": round(sum(float(item.get("recall") or 0) for item in valid_items) / len(valid_items), 4),
            "f1_avg": round(sum(float(item.get("f1") or 0) for item in valid_items) / len(valid_items), 4),
            "text_overlap_avg": round(sum(float(item.get("text_overlap") or 0) for item in valid_items) / len(valid_items), 4),
            "mrr_avg": round(sum(float(item.get("mrr") or 0) for item in valid_items) / len(valid_items), 4),
        })

    return summary


def render_markdown(summary: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> str:
    """Render results as markdown report."""
    lines = [
        "# LAD-RAG Structural Retrieval Test Report",
        "",
        f"- 生成时间: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- 数据目录: {LAD_DATA_DIR}",
        "",
        "## 汇总",
        "",
        "| Strategy | TOPK | Total | Valid | Precision | Recall | F1 | Text Overlap | MRR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for item in summary:
        lines.append(
            f"| {item['strategy']} | {item['top_k']} | {item['total']} | {item['valid']} | "
            f"{item['precision_avg']:.4f} | {item['recall_avg']:.4f} | {item['f1_avg']:.4f} | "
            f"{item['text_overlap_avg']:.4f} | {item['mrr_avg']:.4f} |"
        )

    lines += ["", "## 详细结果", ""]

    # Show top 20 results for each strategy
    for strategy in sorted(set(item.get("strategy") for item in results)):
        strategy_results = [item for item in results if item.get("strategy") == strategy][:20]
        lines.append(f"### {strategy}")
        lines.append("")

        for item in strategy_results:
            error_info = f" | Error: {item['error']}" if "error" in item else ""
            lines.append(
                f"- **{item.get('case_id')}** ({item.get('doc_id')}): "
                f"P={item.get('precision', 0):.3f}, R={item.get('recall', 0):.3f}, "
                f"F1={item.get('f1', 0):.3f}, MRR={item.get('mrr', 0):.3f}{error_info}"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    log("Loading LAD data...")
    corpus, testset = load_lad_data()

    # Extract test cases
    test_cases = testset.get("items", [])
    log(f"Loaded {len(test_cases)} test cases")

    # Organize chunks by document
    chunks_by_doc: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    all_chunks: List[Dict[str, Any]] = []

    for doc in corpus.get("docs", []):
        doc_id = str(doc.get("docId") or "")
        for page in doc.get("pages", []):
            for chunk in page.get("chunks", []):
                chunk["docId"] = doc_id
                chunks_by_doc[doc_id].append(chunk)
                all_chunks.append(chunk)

    log(f"Loaded {len(all_chunks)} chunks from {len(chunks_by_doc)} documents")

    # Build vocabulary
    log("Building vocabulary...")
    vocabulary = build_vocabulary(all_chunks)
    log(f"Vocabulary size: {len(vocabulary)}")

    # Define strategies
    strategies = [
        ("baseline_vector", retrieve_baseline_vector),
        ("hybrid_vector_bm25", retrieve_hybrid_vector_bm25),
        ("structure_aware_reranking", retrieve_structure_aware_reranking),
        ("section_constrained", retrieve_section_constrained),
        ("hierarchical_expansion", retrieve_hierarchical_expansion),
        ("multi_level_structure", retrieve_multi_level_structure),
    ]

    # Define top_k values to test
    top_k_values = [3, 5, 10]

    # Run evaluations
    all_results: List[Dict[str, Any]] = []

    for strategy_name, retrieve_func in strategies:
        log(f"=== Evaluating strategy: {strategy_name} ===")
        for top_k in top_k_values:
            log(f"  top_k={top_k}")
            results = run_strategy_evaluation(
                strategy_name, retrieve_func, test_cases, chunks_by_doc, vocabulary, top_k
            )
            all_results.extend(results)

    # Summarize results
    log("Summarizing results...")
    summary = summarize_results(all_results)

    # Generate reports
    log("Generating reports...")
    report_json = {
        "generatedAt": datetime.now().isoformat(),
        "summary": summary,
        "results": all_results,
    }

    REPORT_JSON_PATH.write_text(
        json.dumps(report_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    REPORT_MD_PATH.write_text(
        render_markdown(summary, all_results),
        encoding="utf-8"
    )

    log(f"Reports saved to:")
    log(f"  JSON: {REPORT_JSON_PATH}")
    log(f"  MD:   {REPORT_MD_PATH}")

    # Print summary table
    log("\n=== Summary ===")
    log(f"{'Strategy':<30} {'TOPK':<6} {'Precision':<10} {'Recall':<10} {'F1':<10} {'MRR':<10}")
    log("-" * 80)
    for item in summary:
        log(f"{item['strategy']:<30} {item['top_k']:<6} {item['precision_avg']:<10.4f} "
            f"{item['recall_avg']:<10.4f} {item['f1_avg']:<10.4f} {item['mrr_avg']:<10.4f}")


if __name__ == "__main__":
    main()
