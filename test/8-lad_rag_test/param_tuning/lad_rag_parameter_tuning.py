#!/usr/bin/env python3
"""
LAD-RAG Parameter Tuning

Fixed: HYBRID seed retrieval
Variables:
- Expansion strategy (neighbor-first, section-first, mixed)
- Seed count (3, 5, 8, 10)
- Total chunks fixed at 15
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
REPORT_PATH = Path(__file__).parent / "lad_rag_parameter_tuning_report.json"

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


def get_embedding_model():
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

    return SentenceTransformer("all-MiniLM-L6-v2")


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


def retrieve_hybrid_seed(
    query: str,
    query_embedding,
    chunk_embeddings,
    chunks: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Retrieve seed chunks using hybrid (vector + BM25)."""
    query_tokens = extract_tokens(query)

    # BM25 scores
    bm25_scores = compute_bm25_scores(query_tokens, chunks)

    # Vector scores
    vector_scores = np.zeros(len(chunks))
    if query_embedding is not None and chunk_embeddings is not None:
        vector_scores = np.dot(chunk_embeddings, query_embedding)

    # Normalize scores
    bm25_max = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
    vec_max = max(vector_scores) if max(vector_scores) > 0 else 1.0

    # Combine scores
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
        item["seed_method"] = "hybrid"
        results.append(item)

    return results


def expand_neighbor_first(
    seed_chunks: List[Dict[str, Any]],
    all_chunks: List[Dict[str, Any]],
    target_count: int,
) -> List[Dict[str, Any]]:
    """Strategy 1: Expand neighbors first, then same section."""
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

    def add_chunk(chunk: Dict[str, Any], method: str) -> bool:
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in expanded_ids:
            return False
        expanded_ids.add(chunk_id)
        item = dict(chunk)
        item["expand_method"] = method
        expanded.append(item)
        return len(expanded) >= target_count

    # Phase 1: Neighbors of seed chunks
    for chunk in seed_chunks:
        if len(expanded) >= target_count:
            break

        chunk_id = str(chunk.get("chunkId") or "")
        original = chunk_by_id.get(chunk_id)
        if not original:
            continue

        for neighbor_id in [
            original.get("prevGlobalChunkId"),
            original.get("nextGlobalChunkId"),
            original.get("prevSamePageChunkId"),
            original.get("nextSamePageChunkId"),
        ]:
            if not neighbor_id:
                continue
            neighbor = chunk_by_id.get(str(neighbor_id))
            if neighbor:
                if add_chunk(neighbor, "neighbor"):
                    return expanded

    # Phase 2: Same section
    for section_id in seed_sections:
        if len(expanded) >= target_count:
            break

        section_chunks = sorted(
            chunks_by_section.get(section_id, []),
            key=lambda c: int(c.get("globalIndex") or 0)
        )

        for chunk in section_chunks:
            if len(expanded) >= target_count:
                break
            if chunk.get("isHeading"):
                continue
            add_chunk(chunk, "same_section")

    # Phase 3: Other sections
    if len(expanded) < target_count:
        for section_id in set(chunks_by_section.keys()) - seed_sections:
            if len(expanded) >= target_count:
                break
            section_chunks = sorted(
                chunks_by_section.get(section_id, []),
                key=lambda c: int(c.get("globalIndex") or 0)
            )
            for chunk in section_chunks:
                if len(expanded) >= target_count:
                    break
                if chunk.get("isHeading"):
                    continue
                add_chunk(chunk, "other_section")

    return expanded[:target_count]


def expand_section_first(
    seed_chunks: List[Dict[str, Any]],
    all_chunks: List[Dict[str, Any]],
    target_count: int,
) -> List[Dict[str, Any]]:
    """Strategy 2: Expand same section first, then neighbors."""
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

    def add_chunk(chunk: Dict[str, Any], method: str) -> bool:
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in expanded_ids:
            return False
        expanded_ids.add(chunk_id)
        item = dict(chunk)
        item["expand_method"] = method
        expanded.append(item)
        return len(expanded) >= target_count

    # Phase 1: Same section (most relevant)
    for section_id in seed_sections:
        if len(expanded) >= target_count:
            break

        section_chunks = sorted(
            chunks_by_section.get(section_id, []),
            key=lambda c: int(c.get("globalIndex") or 0)
        )

        for chunk in section_chunks:
            if len(expanded) >= target_count:
                break
            if chunk.get("isHeading"):
                continue
            add_chunk(chunk, "same_section")

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
                if add_chunk(neighbor, "neighbor"):
                    return expanded

    # Phase 3: Other sections
    if len(expanded) < target_count:
        for section_id in set(chunks_by_section.keys()) - seed_sections:
            if len(expanded) >= target_count:
                break
            section_chunks = sorted(
                chunks_by_section.get(section_id, []),
                key=lambda c: int(c.get("globalIndex") or 0)
            )
            for chunk in section_chunks:
                if len(expanded) >= target_count:
                    break
                if chunk.get("isHeading"):
                    continue
                add_chunk(chunk, "other_section")

    return expanded[:target_count]


def expand_mixed(
    seed_chunks: List[Dict[str, Any]],
    all_chunks: List[Dict[str, Any]],
    target_count: int,
) -> List[Dict[str, Any]]:
    """Strategy 3: Interleave section and neighbor expansion."""
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

    def add_chunk(chunk: Dict[str, Any], method: str) -> bool:
        chunk_id = str(chunk.get("chunkId") or "")
        if chunk_id in expanded_ids:
            return False
        expanded_ids.add(chunk_id)
        item = dict(chunk)
        item["expand_method"] = method
        expanded.append(item)
        return len(expanded) >= target_count

    # Collect candidates from different sources
    neighbor_candidates = []
    section_candidates = []

    # Neighbors
    for chunk in seed_chunks:
        chunk_id = str(chunk.get("chunkId") or "")
        original = chunk_by_id.get(chunk_id)
        if not original:
            continue

        for neighbor_id in [
            original.get("prevGlobalChunkId"),
            original.get("nextGlobalChunkId"),
            original.get("prevSamePageChunkId"),
            original.get("nextSamePageChunkId"),
        ]:
            if not neighbor_id:
                continue
            neighbor = chunk_by_id.get(str(neighbor_id))
            if neighbor and str(neighbor.get("chunkId") or "") not in seed_ids:
                neighbor_candidates.append(neighbor)

    # Same section chunks
    for section_id in seed_sections:
        section_chunks = sorted(
            chunks_by_section.get(section_id, []),
            key=lambda c: int(c.get("globalIndex") or 0)
        )
        for chunk in section_chunks:
            chunk_id = str(chunk.get("chunkId") or "")
            if chunk_id not in seed_ids and not chunk.get("isHeading"):
                section_candidates.append(chunk)

    # Interleave: alternate between section and neighbor
    ni, si = 0, 0
    use_section = True  # Start with section (more relevant)

    while len(expanded) < target_count:
        if use_section and si < len(section_candidates):
            if add_chunk(section_candidates[si], "same_section"):
                return expanded
            si += 1
        elif ni < len(neighbor_candidates):
            if add_chunk(neighbor_candidates[ni], "neighbor"):
                return expanded
            ni += 1
        elif si < len(section_candidates):
            if add_chunk(section_candidates[si], "same_section"):
                return expanded
            si += 1
        else:
            break

        use_section = not use_section

    # If still not enough, add from other sections
    if len(expanded) < target_count:
        for section_id in set(chunks_by_section.keys()) - seed_sections:
            if len(expanded) >= target_count:
                break
            section_chunks = sorted(
                chunks_by_section.get(section_id, []),
                key=lambda c: int(c.get("globalIndex") or 0)
            )
            for chunk in section_chunks:
                if len(expanded) >= target_count:
                    break
                if chunk.get("isHeading"):
                    continue
                add_chunk(chunk, "other_section")

    return expanded[:target_count]


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
    model = None
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

            for idx, chunk in enumerate(all_chunks):
                doc_id = str(chunk.get("docId") or "")
                if doc_id not in embeddings_by_doc:
                    embeddings_by_doc[doc_id] = {"indices": [], "embeddings": []}
                embeddings_by_doc[doc_id]["indices"].append(idx)

            for doc_id, data in embeddings_by_doc.items():
                indices = data["indices"]
                data["embeddings"] = chunk_embeddings[indices]

            log(f"Computed embeddings for {len(chunk_texts)} chunks")

    # Configuration
    TOTAL_CHUNKS = 15
    SEED_COUNTS = [3, 5, 8, 10]
    EXPANSION_STRATEGIES = {
        "neighbor_first": expand_neighbor_first,
        "section_first": expand_section_first,
        "mixed": expand_mixed,
    }

    log(f"\n=== Configuration ===")
    log(f"Total chunks: {TOTAL_CHUNKS}")
    log(f"Seed counts: {SEED_COUNTS}")
    log(f"Expansion strategies: {list(EXPANSION_STRATEGIES.keys())}")

    # Run experiments
    all_results = {}

    for seed_count in SEED_COUNTS:
        for strategy_name, expand_func in EXPANSION_STRATEGIES.items():
            config_name = f"seed{seed_count}_{strategy_name}"
            log(f"\n--- Testing: {config_name} ---")

            results = []
            for case in test_cases:
                doc_id = str(case.get("doc_id") or "")
                question = str(case.get("question") or "")
                evidence_chunk_ids = case.get("evidence_chunk_ids", [])
                evidence_texts = case.get("evidence_texts", [])
                evidence_section_ids = case.get("evidence_section_ids", [])

                chunks = chunks_by_doc.get(doc_id, [])
                if not chunks:
                    continue

                doc_data = embeddings_by_doc.get(doc_id)
                doc_embeddings = doc_data["embeddings"] if doc_data else None

                query_embedding = None
                if model is not None:
                    query_embedding = model.encode(question, normalize_embeddings=True)

                # Get seed chunks using hybrid
                seed_chunks = retrieve_hybrid_seed(
                    question, query_embedding, doc_embeddings, chunks, seed_count
                )

                # Expand using strategy
                expanded = expand_func(seed_chunks, chunks, TOTAL_CHUNKS)

                # Compute metrics
                metrics = compute_metrics(
                    expanded, evidence_chunk_ids, evidence_texts, evidence_section_ids
                )

                results.append({
                    "case_id": case.get("id"),
                    "config": config_name,
                    "seed_count": seed_count,
                    "strategy": strategy_name,
                    "total_chunks": len(expanded),
                    **metrics,
                })

            all_results[config_name] = results

            # Print summary
            chunk_r = avg_metric(results, "chunk_recall")
            token_r = avg_metric(results, "token_recall")
            section_r = avg_metric(results, "section_recall")
            mrr = avg_metric(results, "mrr")
            hit = avg_metric(results, "hit")

            log(f"  {config_name}: ChunkR={chunk_r:.4f} TokenR={token_r:.4f} SectionR={section_r:.4f} MRR={mrr:.4f} Hit={hit:.4f}")

    # Save report
    report = {
        "generatedAt": datetime.now().isoformat(),
        "config": {
            "total_chunks": TOTAL_CHUNKS,
            "seed_counts": SEED_COUNTS,
            "strategies": list(EXPANSION_STRATEGIES.keys()),
        },
        "results": all_results,
    }

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log(f"\nReport saved to: {REPORT_PATH}")

    # Print summary table
    log("\n" + "="*80)
    log("SUMMARY: LAD-RAG Parameter Tuning")
    log("="*80)
    log(f"{'Config':<25} {'Chunk R':<10} {'Token R':<10} {'Section R':<10} {'MRR':<10} {'Hit':<10}")
    log("-" * 75)

    for config_name, results in all_results.items():
        chunk_r = avg_metric(results, "chunk_recall")
        token_r = avg_metric(results, "token_recall")
        section_r = avg_metric(results, "section_recall")
        mrr = avg_metric(results, "mrr")
        hit = avg_metric(results, "hit")

        log(f"{config_name:<25} {chunk_r:<10.4f} {token_r:<10.4f} {section_r:<10.4f} {mrr:<10.4f} {hit:<10.4f}")

    # Find best configuration
    best_config = None
    best_score = 0

    for config_name, results in all_results.items():
        # Use weighted score: 0.4*chunk_r + 0.4*token_r + 0.2*section_r
        chunk_r = avg_metric(results, "chunk_recall")
        token_r = avg_metric(results, "token_recall")
        section_r = avg_metric(results, "section_recall")
        score = 0.4 * chunk_r + 0.4 * token_r + 0.2 * section_r

        if score > best_score:
            best_score = score
            best_config = config_name

    log(f"\nBest configuration: {best_config} (score: {best_score:.4f})")


if __name__ == "__main__":
    main()
