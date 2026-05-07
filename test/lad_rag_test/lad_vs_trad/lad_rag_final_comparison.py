#!/usr/bin/env python3
"""
LAD-RAG vs Traditional RAG Final Comparison

LAD-RAG config: seed=8, section_first, hybrid retrieval
Traditional RAG: direct hybrid retrieval
Total chunks: 10, 15, 20
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
LAD_DATA_DIR = ROOT / "test" / "lad_rag_test" / "data"
REPORT_PATH = Path(__file__).parent / "lad_rag_final_comparison_report.json"

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


def compute_bm25_scores(query_tokens: List[str], chunks: List[Dict[str, Any]]) -> List[float]:
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


def retrieve_hybrid(
    query: str,
    query_embedding,
    chunk_embeddings,
    chunks: List[Dict[str, Any]],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Retrieve using hybrid (vector + BM25)."""
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
        results.append(item)

    return results


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
            key=lambda c: int(c.get("globalIndex") or 0)
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
        for neighbor_id in [original.get("prevGlobalChunkId"), original.get("nextGlobalChunkId")]:
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
                key=lambda c: int(c.get("globalIndex") or 0)
            )
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
    retrieved_ids = {str(chunk.get("chunkId") or "") for chunk in retrieved}
    evidence_set = set(evidence_chunk_ids)

    chunk_hits = len(retrieved_ids & evidence_set)
    chunk_recall = chunk_hits / max(len(evidence_set), 1)

    retrieved_text = " ".join(str(chunk.get("normalizedContent") or chunk.get("content") or "") for chunk in retrieved)
    retrieved_tokens = set(extract_tokens(retrieved_text))
    evidence_text = " ".join(evidence_texts)
    evidence_tokens = set(extract_tokens(evidence_text))
    token_recall = len(retrieved_tokens & evidence_tokens) / max(len(evidence_tokens), 1)

    retrieved_sections = {str(chunk.get("sectionId") or "") for chunk in retrieved if chunk.get("sectionId")}
    evidence_sections = set(evidence_section_ids)
    section_recall = len(retrieved_sections & evidence_sections) / max(len(evidence_sections), 1)

    mrr = 0.0
    for i, chunk in enumerate(retrieved):
        if str(chunk.get("chunkId") or "") in evidence_set:
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
            chunk_texts = [str(c.get("normalizedContent") or c.get("content") or "") for c in all_chunks]
            chunk_embeddings = model.encode(chunk_texts, normalize_embeddings=True, show_progress_bar=True)

            for idx, chunk in enumerate(all_chunks):
                doc_id = str(chunk.get("docId") or "")
                if doc_id not in embeddings_by_doc:
                    embeddings_by_doc[doc_id] = {"indices": [], "embeddings": []}
                embeddings_by_doc[doc_id]["indices"].append(idx)

            for doc_id, data in embeddings_by_doc.items():
                data["embeddings"] = chunk_embeddings[data["indices"]]

            log(f"Computed embeddings for {len(chunk_texts)} chunks")

    # LAD-RAG config
    SEED_COUNT = 8
    TOTAL_CHUNKS_LIST = [10, 15, 20]

    log(f"\n=== Configuration ===")
    log(f"LAD-RAG: seed={SEED_COUNT}, strategy=section_first")
    log(f"Traditional RAG: direct hybrid")
    log(f"Total chunks: {TOTAL_CHUNKS_LIST}")

    # Run comparison
    all_results = {
        "traditional": {tc: [] for tc in TOTAL_CHUNKS_LIST},
        "lad": {tc: [] for tc in TOTAL_CHUNKS_LIST},
    }

    for case in test_cases:
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

        query_embedding = None
        if model is not None:
            query_embedding = model.encode(question, normalize_embeddings=True)

        for total_chunks in TOTAL_CHUNKS_LIST:
            # Traditional RAG
            trad_results = retrieve_hybrid(question, query_embedding, doc_embeddings, chunks, total_chunks)
            trad_metrics = compute_metrics(trad_results, evidence_chunk_ids, evidence_texts, evidence_section_ids)

            all_results["traditional"][total_chunks].append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "category": category,
                "difficulty": difficulty,
                **trad_metrics,
            })

            # LAD-RAG
            seed_chunks = retrieve_hybrid(question, query_embedding, doc_embeddings, chunks, SEED_COUNT)
            lad_results = expand_section_first(seed_chunks, chunks, total_chunks)
            lad_metrics = compute_metrics(lad_results, evidence_chunk_ids, evidence_texts, evidence_section_ids)

            all_results["lad"][total_chunks].append({
                "case_id": case.get("id"),
                "doc_id": doc_id,
                "category": category,
                "difficulty": difficulty,
                **lad_metrics,
            })

    # Save report
    report = {
        "generatedAt": datetime.now().isoformat(),
        "config": {
            "lad_seed": SEED_COUNT,
            "lad_strategy": "section_first",
            "total_chunks": TOTAL_CHUNKS_LIST,
            "test_cases": len(test_cases),
        },
        "results": all_results,
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"\nReport saved to: {REPORT_PATH}")

    # Print summary
    log("\n" + "="*80)
    log("FINAL COMPARISON: LAD-RAG vs Traditional RAG")
    log("="*80)

    # Overall comparison
    log(f"\n{'Method':<25} {'Total':<8} {'Chunk R':<10} {'Token R':<10} {'Section R':<10} {'MRR':<10} {'Hit':<10}")
    log("-"*83)

    for tc in TOTAL_CHUNKS_LIST:
        trad = all_results["traditional"][tc]
        lad = all_results["lad"][tc]

        log(f"{'Traditional RAG':<25} {tc:<8} {avg_metric(trad, 'chunk_recall'):<10.4f} "
            f"{avg_metric(trad, 'token_recall'):<10.4f} {avg_metric(trad, 'section_recall'):<10.4f} "
            f"{avg_metric(trad, 'mrr'):<10.4f} {avg_metric(trad, 'hit'):<10.4f}")

        log(f"{'LAD-RAG':<25} {tc:<8} {avg_metric(lad, 'chunk_recall'):<10.4f} "
            f"{avg_metric(lad, 'token_recall'):<10.4f} {avg_metric(lad, 'section_recall'):<10.4f} "
            f"{avg_metric(lad, 'mrr'):<10.4f} {avg_metric(lad, 'hit'):<10.4f}")

        # Improvement
        trad_chunk = avg_metric(trad, "chunk_recall")
        lad_chunk = avg_metric(lad, "chunk_recall")
        if trad_chunk > 0:
            imp = (lad_chunk - trad_chunk) / trad_chunk * 100
            log(f"{'Improvement':<25} {'':8} {imp:+.2f}%")
        log("")

    # By difficulty
    log("\n" + "="*80)
    log("BY DIFFICULTY")
    log("="*80)

    for tc in [15]:  # Only show for total=15
        log(f"\nTotal chunks = {tc}")
        log(f"{'Difficulty':<20} {'Method':<20} {'Chunk R':<10} {'Token R':<10} {'Count':<8}")
        log("-"*68)

        for difficulty in ["single_section", "cross_section"]:
            trad = [r for r in all_results["traditional"][tc] if r.get("difficulty") == difficulty]
            lad = [r for r in all_results["lad"][tc] if r.get("difficulty") == difficulty]

            if trad:
                log(f"{difficulty:<20} {'Traditional':<20} {avg_metric(trad, 'chunk_recall'):<10.4f} "
                    f"{avg_metric(trad, 'token_recall'):<10.4f} {len(trad):<8}")
            if lad:
                log(f"{'':20} {'LAD-RAG':<20} {avg_metric(lad, 'chunk_recall'):<10.4f} "
                    f"{avg_metric(lad, 'token_recall'):<10.4f} {len(lad):<8}")

            if trad and lad:
                trad_c = avg_metric(trad, "chunk_recall")
                lad_c = avg_metric(lad, "chunk_recall")
                if trad_c > 0:
                    imp = (lad_c - trad_c) / trad_c * 100
                    log(f"{'':20} {'Improvement':<20} {imp:+.2f}%")
            log("")

    # By category
    log("\n" + "="*80)
    log("BY CATEGORY (total=15)")
    log("="*80)

    categories = sorted(set(r.get("category") for r in all_results["traditional"][15]))
    log(f"\n{'Category':<20} {'Trad Chunk R':<15} {'LAD Chunk R':<15} {'Improvement':<15} {'Count':<8}")
    log("-"*73)

    for category in categories:
        trad = [r for r in all_results["traditional"][15] if r.get("category") == category]
        lad = [r for r in all_results["lad"][15] if r.get("category") == category]

        trad_c = avg_metric(trad, "chunk_recall") if trad else 0
        lad_c = avg_metric(lad, "chunk_recall") if lad else 0

        imp = ((lad_c - trad_c) / trad_c * 100) if trad_c > 0 else 0

        log(f"{category:<20} {trad_c:<15.4f} {lad_c:<15.4f} {imp:+.15}% {len(trad):<8}")


if __name__ == "__main__":
    main()
