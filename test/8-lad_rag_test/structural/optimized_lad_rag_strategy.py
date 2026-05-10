#!/usr/bin/env python3
"""
Optimized LAD-RAG Strategy

Based on the structural retrieval test results, this module implements an optimized
LAD-RAG strategy that combines the best aspects of different approaches:

1. Hybrid vector + BM25 for initial retrieval (best recall)
2. Multi-level structure matching for reranking (best MRR)
3. Section-aware context expansion for comprehensive coverage

Key findings from the test:
- multi_level_structure achieved best MRR (0.3470) and recall (0.4433) at top_k=10
- hybrid_vector_bm25 achieved good recall (0.4385) at top_k=10
- Structure matching improves ranking quality (MRR) more than recall
- Section constraints can hurt recall if sections are misidentified

Optimization strategy:
- Use hybrid retrieval for initial candidate generation
- Apply multi-level structure scoring for reranking
- Expand context based on section hierarchy
- Adaptive top_k based on question complexity
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def extract_tokens(text: str) -> List[str]:
    """Extract tokens from text for lexical matching."""
    raw = str(text or "")
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[一-鿿]{2,}|\d+(?:\.\d+)?%?", raw)
    return [t.lower() for t in tokens if str(t).strip()]


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


def is_complex_question(question: str) -> bool:
    """Detect if a question is complex (requires multiple evidence pieces)."""
    q = question.lower()
    # Complex question markers
    complex_markers = [
        "哪些", "什么", "如何", "流程", "步骤", "模块", "功能", "维度", "关键",
        "创新", "区别", "为什么", "怎么", "compare", "difference", "how", "what",
        "which", "why", "explain", "describe", "list", "steps", "process"
    ]
    return any(marker in q for marker in complex_markers)


def get_adaptive_top_k(question: str, requested_top_k: int) -> int:
    """Get adaptive top_k based on question complexity."""
    base = max(1, int(requested_top_k or 5))
    if is_complex_question(question):
        # Complex questions benefit from more context
        return min(15, max(base, 8))
    return min(10, max(base, 3))


def compute_bm25_score(
    query_tokens: List[str],
    doc_tokens: List[str],
    doc_len: int,
    avgdl: float,
    n_docs: int,
    doc_freq: Dict[str, int],
) -> float:
    """Compute BM25 score for a single document."""
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

        # IDF component
        idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))

        # TF component with length normalization
        freq = tf[term]
        tf_component = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (doc_len / avgdl)))

        score += idf * tf_component

    return score


def compute_structure_score(
    query_tokens: Set[str],
    chunk: Dict[str, Any],
) -> float:
    """Compute structure matching score at multiple levels."""
    if not query_tokens:
        return 0.0

    # Level 1: Document level (doc name matching)
    doc_name = str(chunk.get("docName") or "")
    doc_tokens = set(extract_tokens(doc_name))
    doc_match = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)

    # Level 2: Section level (section path matching)
    section_path = str(chunk.get("sectionPathText") or "")
    section_tokens = set(extract_tokens(section_path))
    section_match = len(query_tokens & section_tokens) / max(len(query_tokens), 1)

    # Level 3: Heading level (heading text matching)
    heading_text = str(chunk.get("headingText") or "")
    heading_tokens = set(extract_tokens(heading_text))
    heading_match = len(query_tokens & heading_tokens) / max(len(query_tokens), 1)

    # Level 4: Block type level
    block_type = str(chunk.get("blockType") or "")
    block_tokens = set(extract_tokens(block_type))
    block_match = len(query_tokens & block_tokens) / max(len(query_tokens), 1)

    # Weighted combination of different levels
    # Heading match is most informative for academic papers
    structure_score = (
        0.1 * doc_match +
        0.3 * section_match +
        0.4 * heading_match +
        0.2 * block_match
    )

    # Bonus for having heading text (indicates structured content)
    if heading_text.strip():
        structure_score += 0.05

    # Bonus for being a title or heading block type
    if "title" in block_type.lower() or "heading" in block_type.lower():
        structure_score += 0.03

    return min(1.0, structure_score)


def optimized_lad_rag_retrieve(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int,
    vocabulary: Dict[str, int],
    *,
    use_structure_reranking: bool = True,
    use_context_expansion: bool = True,
    structure_weight: float = 0.3,
    bm25_weight: float = 0.4,
    vector_weight: float = 0.6,
) -> List[Dict[str, Any]]:
    """
    Optimized LAD-RAG retrieval strategy.

    Combines hybrid retrieval with structure-aware reranking and context expansion.

    Args:
        query: Search query
        chunks: List of document chunks with LAD structure
        top_k: Number of results to return
        vocabulary: Pre-built vocabulary for vectorization
        use_structure_reranking: Whether to apply structure-based reranking
        use_context_expansion: Whether to expand context based on section hierarchy
        structure_weight: Weight for structure score in final ranking
        bm25_weight: Weight for BM25 score in hybrid retrieval
        vector_weight: Weight for vector score in hybrid retrieval

    Returns:
        List of retrieved chunks with scores
    """
    if not chunks:
        return []

    # Get adaptive top_k based on question complexity
    adaptive_top_k = get_adaptive_top_k(query, top_k)

    # Step 1: Initial candidate generation using hybrid retrieval
    # Get more candidates than needed for reranking
    candidate_k = min(len(chunks), max(adaptive_top_k * 3, 30))

    query_tokens = extract_tokens(query)
    query_set = set(query_tokens)
    query_vec = simple_tfidf_vector(query_tokens, vocabulary)

    # Compute document statistics for BM25
    doc_lens = []
    all_doc_tokens = []
    doc_freq: Dict[str, int] = defaultdict(int)

    for chunk in chunks:
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        tokens = extract_tokens(content)
        doc_lens.append(len(tokens))
        all_doc_tokens.append(tokens)

        # Count document frequency
        unique_tokens = set(tokens)
        for token in unique_tokens:
            doc_freq[token] += 1

    avgdl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(chunks)

    # Score all chunks
    scored_chunks: List[Tuple[float, Dict[str, Any]]] = []

    for idx, chunk in enumerate(chunks):
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        chunk_tokens = all_doc_tokens[idx]
        chunk_vec = simple_tfidf_vector(chunk_tokens, vocabulary)

        # Vector similarity (TF-IDF based)
        vector_sim = compute_cosine_similarity(query_vec, chunk_vec)

        # BM25 score
        bm25_score = compute_bm25_score(
            query_tokens, chunk_tokens, doc_lens[idx], avgdl, n_docs, doc_freq
        )
        # Normalize BM25 score to [0, 1] range
        bm25_normalized = min(1.0, bm25_score / max(1, len(query_tokens)))

        # Hybrid score
        hybrid_score = vector_weight * vector_sim + bm25_weight * bm25_normalized

        # Structure score (if enabled)
        structure_score = 0.0
        if use_structure_reranking:
            structure_score = compute_structure_score(query_set, chunk)

        # Final score
        final_score = hybrid_score
        if use_structure_reranking:
            final_score += structure_weight * structure_score

        if final_score > 0:
            item = dict(chunk)
            item["score"] = round(final_score, 6)
            item["vector_score"] = round(vector_sim, 6)
            item["bm25_score"] = round(bm25_normalized, 6)
            item["structure_score"] = round(structure_score, 6)
            scored_chunks.append((final_score, item))

    # Sort by score and get initial candidates
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    candidates = [item for _, item in scored_chunks[:candidate_k]]

    # Step 2: Context expansion (if enabled)
    if use_context_expansion and len(candidates) > 0:
        expanded_candidates = expand_context(candidates, chunks, query_set)
        # Re-sort expanded candidates
        expanded_candidates.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
        candidates = expanded_candidates

    # Step 3: Final selection
    return candidates[:adaptive_top_k]


def expand_context(
    candidates: List[Dict[str, Any]],
    all_chunks: List[Dict[str, Any]],
    query_tokens: Set[str],
) -> List[Dict[str, Any]]:
    """
    Expand context based on section hierarchy.

    Adds neighboring chunks from the same section or related sections
    to provide more comprehensive context.
    """
    if not candidates:
        return []

    # Get section IDs of top candidates
    candidate_section_ids = set()
    for item in candidates[:5]:  # Only expand from top 5
        section_id = str(item.get("sectionId") or "")
        if section_id:
            candidate_section_ids.add(section_id)

    # Find chunks from same sections that aren't already in candidates
    candidate_ids = {str(item.get("chunkId") or "") for item in candidates}
    expanded = list(candidates)  # Start with existing candidates

    for chunk in all_chunks:
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in candidate_ids:
            continue

        section_id = str(chunk.get("sectionId") or "")
        if section_id in candidate_section_ids:
            # Add chunk from same section with reduced score
            item = dict(chunk)
            original_score = float(item.get("score") or 0)
            item["score"] = round(original_score * 0.8, 6)  # Reduce score for expanded chunks
            item["is_expanded"] = True
            expanded.append(item)
            candidate_ids.add(chunk_id)

    # Also expand to parent/child sections
    section_paths = set()
    for item in candidates[:3]:
        section_path = str(item.get("sectionPathText") or "")
        if section_path:
            section_paths.add(section_path)

    # Find related sections (sharing path prefix)
    related_section_ids = set()
    for path in section_paths:
        path_parts = path.split(":::")
        if len(path_parts) > 1:
            parent_path = ":::".join(path_parts[:-1]).strip()
            for chunk in all_chunks:
                chunk_path = str(chunk.get("sectionPathText") or "")
                if chunk_path.startswith(parent_path):
                    related_section_ids.add(str(chunk.get("sectionId") or ""))

    # Add chunks from related sections
    for chunk in all_chunks:
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in candidate_ids:
            continue

        section_id = str(chunk.get("sectionId") or "")
        if section_id in related_section_ids:
            item = dict(chunk)
            original_score = float(item.get("score") or 0)
            item["score"] = round(original_score * 0.6, 6)  # Lower score for related sections
            item["is_expanded"] = True
            item["expansion_type"] = "related_section"
            expanded.append(item)
            candidate_ids.add(chunk_id)

    return expanded


def retrieve_and_format(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 5,
    *,
    use_structure_reranking: bool = True,
    use_context_expansion: bool = True,
) -> Dict[str, Any]:
    """
    Main entry point for optimized LAD-RAG retrieval.

    Returns formatted results with metadata.
    """
    if not chunks:
        return {
            "query": query,
            "top_k": top_k,
            "results": [],
            "metadata": {
                "strategy": "optimized_lad_rag",
                "total_chunks": 0,
            }
        }

    # Build vocabulary
    vocabulary = build_vocabulary(chunks)

    # Retrieve using optimized strategy
    results = optimized_lad_rag_retrieve(
        query,
        chunks,
        top_k,
        vocabulary,
        use_structure_reranking=use_structure_reranking,
        use_context_expansion=use_context_expansion,
    )

    # Format results
    formatted_results = []
    for item in results:
        formatted_results.append({
            "chunkId": str(item.get("chunkId") or ""),
            "docId": str(item.get("docId") or ""),
            "docName": str(item.get("docName") or ""),
            "content": str(item.get("normalizedContent") or item.get("content") or "")[:500] + "..." if len(str(item.get("normalizedContent") or item.get("content") or "")) > 500 else str(item.get("normalizedContent") or item.get("content") or ""),
            "sectionPath": str(item.get("sectionPathText") or ""),
            "headingText": str(item.get("headingText") or ""),
            "blockType": str(item.get("blockType") or ""),
            "scores": {
                "final": float(item.get("score") or 0),
                "vector": float(item.get("vector_score") or 0),
                "bm25": float(item.get("bm25_score") or 0),
                "structure": float(item.get("structure_score") or 0),
            },
            "is_expanded": bool(item.get("is_expanded", False)),
            "expansion_type": str(item.get("expansion_type") or ""),
        })

    return {
        "query": query,
        "top_k": top_k,
        "results": formatted_results,
        "metadata": {
            "strategy": "optimized_lad_rag",
            "total_chunks": len(chunks),
            "retrieved_count": len(formatted_results),
            "use_structure_reranking": use_structure_reranking,
            "use_context_expansion": use_context_expansion,
        }
    }


# Example usage
if __name__ == "__main__":
    # This module is designed to be imported and used by other scripts
    # Example:
    # from optimized_lad_rag_strategy import retrieve_and_format
    # result = retrieve_and_format("what is the main contribution?", chunks, top_k=5)
    pass
