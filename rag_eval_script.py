from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parent
QASPER_AFTER_DIR = ROOT / "test" / "Qasper_after"
SPLITS = ["train", "validation", "test"]
TOP_KS = [1, 3, 5]
STRATEGIES = [
    {"name": "rag_500_100", "chunk_size": 500, "overlap": 100},
    {"name": "rag_300_100", "chunk_size": 300, "overlap": 100},
    {"name": "semantic_78_600_900_160", "chunk_size": 0, "overlap": 0},
]
DEFAULT_MAX_ITEMS = 10
TRAIN_MAX_ITEMS = 100
DEFAULT_MAX_CASES = 20
FALLBACK_ANSWER = "文档中未找到足够依据。"
ANSWER_LANGUAGE = "English"
REPORT_JSON_PATH = QASPER_AFTER_DIR / "rag_eval_report.json"
REPORT_MD_PATH = QASPER_AFTER_DIR / "rag_eval_report.md"
PARTIAL_JSON_PATH = QASPER_AFTER_DIR / "rag_eval_report.partial.json"


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def load_split(split: str) -> Dict[str, Any]:
    path = QASPER_AFTER_DIR / f"{split}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing split file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
    return text


def extract_tokens(text: str) -> List[str]:
    raw = str(text or "")
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[\u4e00-\u9fff]{2,}|\d+(?:\.\d+)?%?", raw)
    return [t.lower() for t in tokens if str(t).strip()]


def split_chunks_for_strategy(paper: Dict[str, Any], strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = paper.get("chunks") if isinstance(paper.get("chunks"), list) else []
    if strategy["chunk_size"] <= 0:
        return [dict(chunk) for chunk in chunks if isinstance(chunk, dict)]

    out: List[Dict[str, Any]] = []
    buffer: List[Dict[str, Any]] = []
    char_count = 0
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        text = str(chunk.get("text") or "").strip()
        if not text:
            continue
        add = len(text) + (2 if buffer else 0)
        if buffer and char_count + add > strategy["chunk_size"]:
            content = "\n\n".join(str(x.get("text") or "").strip() for x in buffer).strip()
            source_ids = [str(x.get("chunk_id") or "") for x in buffer if str(x.get("chunk_id") or "").strip()]
            out.append(
                {
                    "chunkId": f"{strategy['name']}_{len(out):04d}",
                    "content": content,
                    "normalizedContent": content,
                    "pageNo": 1,
                    "index": len(out),
                    "sourceChunkIds": source_ids,
                    "sourcePageNos": [],
                    "sourceChunkCount": len(buffer),
                }
            )

            keep: List[Dict[str, Any]] = []
            overlap_chars = 0
            for item in reversed(buffer):
                kept_text = str(item.get("text") or "").strip()
                add2 = len(kept_text) + (2 if keep else 0)
                if keep and overlap_chars + add2 > strategy["overlap"]:
                    break
                keep.insert(0, item)
                overlap_chars += add2
                if overlap_chars >= strategy["overlap"]:
                    break
            buffer = keep
            char_count = sum(len(str(x.get("text") or "").strip()) for x in buffer) + max(0, len(buffer) - 1) * 2

        buffer.append(chunk)
        char_count += add

    if buffer:
        content = "\n\n".join(str(x.get("text") or "").strip() for x in buffer).strip()
        source_ids = [str(x.get("chunk_id") or "") for x in buffer if str(x.get("chunk_id") or "").strip()]
        out.append(
            {
                "chunkId": f"{strategy['name']}_{len(out):04d}",
                "content": content,
                "normalizedContent": content,
                "pageNo": 1,
                "index": len(out),
                "sourceChunkIds": source_ids,
                "sourcePageNos": [],
                "sourceChunkCount": len(buffer),
            }
        )
    return out


def retrieve_chunks(chunks: List[Dict[str, Any]], question: str, top_k: int) -> List[Dict[str, Any]]:
    q_tokens = set(extract_tokens(question))
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for idx, chunk in enumerate(chunks):
        text = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        c_tokens = set(extract_tokens(text))
        overlap = len(q_tokens & c_tokens)
        score = overlap / max(len(q_tokens), 1)
        if question and normalize_text(question) in normalize_text(text):
            score += 0.5
        if overlap <= 0 and score <= 0:
            continue
        item = dict(chunk)
        item["score"] = round(float(score) - idx * 1e-6, 6)
        scored.append((item["score"], item))
    if not scored:
        return [dict(chunk, score=0.0) for chunk in chunks[: max(1, top_k)]]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[: max(1, top_k)]]


def get_chunk_identifier(chunk: Dict[str, Any]) -> str:
    for key in ("chunkId", "chunk_id"):
        value = str(chunk.get(key) or "").strip()
        if value:
            return value
    return ""


def expand_retrieved_chunk_ids(retrieved: Sequence[Dict[str, Any]]) -> List[str]:
    expanded: List[str] = []
    for chunk in retrieved:
        if not isinstance(chunk, dict):
            continue
        chunk_id = get_chunk_identifier(chunk)
        if chunk_id:
            expanded.append(chunk_id)
        source_ids = chunk.get("sourceChunkIds") if isinstance(chunk.get("sourceChunkIds"), list) else []
        for source_id in source_ids:
            source_id = str(source_id or "").strip()
            if source_id:
                expanded.append(source_id)
    return list(dict.fromkeys(expanded))


def build_model_answer(question: str, retrieved: List[Dict[str, Any]], paper: Dict[str, Any]) -> Dict[str, Any]:
    from backend.services.qa_service import ask_deepseek_with_selection_v2

    current_items = [dict(chunk) for chunk in retrieved]
    support_items: List[Dict[str, Any]] = []
    doc_name = str(paper.get("title") or paper.get("paper_id") or "Qasper paper")
    prompt_question = f"{question}\n\nAnswer in {ANSWER_LANGUAGE}. Keep the answer concise and factual."
    doc_overview = {
        "status": "ready",
        "title": doc_name,
        "overviewShort": str(paper.get("abstract") or "").strip()[:600],
    }
    try:
        result = ask_deepseek_with_selection_v2(
            ROOT,
            current_items,
            support_items,
            prompt_question,
            doc_name,
            doc_id=str(paper.get("paper_id") or ""),
            doc_overview=doc_overview,
            compacted_context="",
            recent_turns=[],
            manual_selected=False,
            context_source="qasper_after_eval",
        )
        answer = str(result.get("answer") or "").strip() or FALLBACK_ANSWER
        cited_chunk_ids = [
            str(x).strip()
            for x in (result.get("cited_chunk_ids") if isinstance(result.get("cited_chunk_ids"), list) else [])
            if str(x).strip()
        ]
        return {"answer": answer, "cited_chunk_ids": cited_chunk_ids, "llm_error": ""}
    except Exception as exc:
        log(f"LLM answer failed: {exc}")
        return {"answer": FALLBACK_ANSWER, "cited_chunk_ids": [], "llm_error": str(exc)}


def normalize_answer(text: str) -> str:
    return normalize_text(text)


def answer_tokens(text: str) -> List[str]:
    return extract_tokens(text)


def compute_score(
    answer: str,
    gold_answer: str,
    keywords: Sequence[str],
    cited_chunk_ids: Sequence[str],
    evidence_chunk_ids: Sequence[str],
    retrieved_chunk_ids: Sequence[str],
) -> Dict[str, Any]:
    answer_norm = normalize_answer(answer)
    gold_norm = normalize_answer(gold_answer)
    exact_match = bool(answer_norm) and answer_norm == gold_norm

    keyword_list = [str(k).strip() for k in keywords if str(k).strip()]
    if not keyword_list:
        keyword_list = [tok for tok in answer_tokens(gold_answer) if len(tok) >= 2][:8]
    keyword_hits = sum(1 for kw in keyword_list if normalize_answer(kw) in answer_norm)
    keyword_recall = round(keyword_hits / max(len(keyword_list), 1), 4) if keyword_list else 0.0

    gold_tok = set(answer_tokens(gold_answer))
    ans_tok = set(answer_tokens(answer))
    token_recall = round(len(gold_tok & ans_tok) / max(len(gold_tok), 1), 4) if gold_tok else 0.0

    cited_set = {str(x).strip() for x in cited_chunk_ids if str(x).strip()}
    evidence_set = {str(x).strip() for x in evidence_chunk_ids if str(x).strip()}
    retrieved_set = {str(x).strip() for x in retrieved_chunk_ids if str(x).strip()}

    retrieval_hit = bool(retrieved_set & evidence_set)
    evidence_hit = bool(cited_set & evidence_set)
    evidence_recall = round(len(retrieved_set & evidence_set) / max(len(evidence_set), 1), 4) if evidence_set else 0.0
    cited_support_rate = round(len(cited_set & evidence_set) / max(len(cited_set), 1), 4) if cited_set else 0.0

    return {
        "exact_match": exact_match,
        "keyword_hits": keyword_hits,
        "keyword_recall": keyword_recall,
        "token_recall": token_recall,
        "retrieval_hit": retrieval_hit,
        "evidence_hit": evidence_hit,
        "evidence_recall": evidence_recall,
        "cited_support_rate": cited_support_rate,
    }


def summarize_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    for item in results:
        groups.setdefault((str(item["strategy"]), int(item["top_k"])), []).append(item)

    summary: List[Dict[str, Any]] = []
    for (strategy, top_k), items in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        total = len(items)
        summary.append(
            {
                "strategy": strategy,
                "top_k": top_k,
                "total": total,
                "exact_match_rate": round(sum(1 for x in items if x.get("exact_match")) / max(total, 1), 4),
                "keyword_recall_avg": round(sum(float(x.get("keyword_recall") or 0) for x in items) / max(total, 1), 4),
                "token_recall_avg": round(sum(float(x.get("token_recall") or 0) for x in items) / max(total, 1), 4),
                "retrieval_hit_rate": round(sum(1 for x in items if x.get("retrieval_hit")) / max(total, 1), 4),
                "evidence_hit_rate": round(sum(1 for x in items if x.get("evidence_hit")) / max(total, 1), 4),
                "evidence_recall_avg": round(sum(float(x.get("evidence_recall") or 0) for x in items) / max(total, 1), 4),
                "cited_support_rate_avg": round(sum(float(x.get("cited_support_rate") or 0) for x in items) / max(total, 1), 4),
            }
        )
    return summary


def render_markdown(summary: List[Dict[str, Any]], results: List[Dict[str, Any]], max_cases: int) -> str:
    lines = [
        "# Qasper_after RAG 测试报告",
        "",
        f"- 生成时间: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- 数据目录: {QASPER_AFTER_DIR}",
        f"- chunk 策略: {', '.join(s['name'] for s in STRATEGIES)}",
        f"- TOPK: {', '.join(map(str, TOP_KS))}",
        f"- 每组参数固定前 {max_cases} 条 QA",
        "",
        "## 汇总",
        "",
        "| Strategy | TOPK | Total | Exact Match | Keyword Recall | Token Recall | Retrieval Hit | Evidence Hit | Evidence Recall | Cited Support |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary:
        lines.append(
            f"| {item['strategy']} | {item['top_k']} | {item['total']} | {item['exact_match_rate']:.4f} | {item['keyword_recall_avg']:.4f} | {item['token_recall_avg']:.4f} | {item['retrieval_hit_rate']:.4f} | {item['evidence_hit_rate']:.4f} | {item['evidence_recall_avg']:.4f} | {item['cited_support_rate_avg']:.4f} |"
        )
    lines += ["", "## 详细结果", ""]
    for item in results[:30]:
        lines += [
            f"### {item['paper_id']} | {item['split']} | {item['question_id']} | {item['strategy']} | top_k={item['top_k']}",
            f"- 问题: {item['question']}",
            f"- 标准答案: {item['gold_answer']}",
            f"- 模型答案: {item['answer']}",
            f"- 引用 chunks: {', '.join(item['cited_chunk_ids']) if item['cited_chunk_ids'] else '无'}",
            f"- 召回块数: {item['retrieved_count']}",
            f"- exact_match: {item['exact_match']}",
            f"- keyword_recall: {item['keyword_recall']}",
            f"- token_recall: {item['token_recall']}",
            f"- retrieval_hit: {item['retrieval_hit']}",
            f"- evidence_hit: {item['evidence_hit']}",
            f"- evidence_recall: {item['evidence_recall']}",
            f"- cited_support_rate: {item['cited_support_rate']}",
            f"- llm_error: {item.get('llm_error') or '无'}",
            "",
        ]
    return "\n".join(lines)


def collect_cases(papers: Sequence[Dict[str, Any]], max_cases: int) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        qas = paper.get("qas") if isinstance(paper.get("qas"), list) else []
        for qa in qas:
            if not isinstance(qa, dict):
                continue
            cases.append({"paper": paper, "qa": qa})
            if len(cases) >= max_cases:
                return cases
    return cases


def run_single_case(paper: Dict[str, Any], qa: Dict[str, Any], strategy: Dict[str, Any], top_k: int) -> Dict[str, Any]:
    chunks = split_chunks_for_strategy(paper, strategy)
    question = str(qa.get("question") or "").strip()
    gold_answer = str((qa.get("gold_answers") or [""])[0] or "").strip()
    evidence_chunk_ids = qa.get("evidence_chunk_ids") if isinstance(qa.get("evidence_chunk_ids"), list) else []
    retrieved = retrieve_chunks(chunks, question, top_k)
    retrieved_chunk_ids = expand_retrieved_chunk_ids(retrieved)
    llm_result = build_model_answer(question, retrieved, paper)
    cited_chunk_ids = [
        str(x).strip()
        for x in (llm_result.get("cited_chunk_ids") if isinstance(llm_result.get("cited_chunk_ids"), list) else [])
        if str(x).strip()
    ]
    answer = str(llm_result.get("answer") or "").strip()
    metrics = compute_score(
        answer,
        gold_answer,
        qa.get("keywords") or [],
        cited_chunk_ids,
        evidence_chunk_ids,
        retrieved_chunk_ids,
    )
    return {
        "split": paper.get("source_split"),
        "paper_id": paper.get("paper_id"),
        "title": paper.get("title"),
        "question_id": qa.get("question_id"),
        "question": question,
        "gold_answer": gold_answer,
        "answer": answer,
        "strategy": strategy["name"],
        "top_k": top_k,
        "retrieved_count": len(retrieved),
        "cited_chunk_ids": cited_chunk_ids,
        "evidence_chunk_ids": evidence_chunk_ids,
        "llm_error": str(llm_result.get("llm_error") or ""),
        **metrics,
    }


def main() -> None:
    if not QASPER_AFTER_DIR.is_dir():
        raise FileNotFoundError(f"Missing Qasper_after directory: {QASPER_AFTER_DIR}")

    max_items = int(os.getenv("RAG_EVAL_MAX_ITEMS", str(DEFAULT_MAX_ITEMS)) or DEFAULT_MAX_ITEMS)
    max_items = max(1, max_items)
    train_max_items = int(os.getenv("RAG_EVAL_TRAIN_MAX_ITEMS", str(TRAIN_MAX_ITEMS)) or TRAIN_MAX_ITEMS)
    train_max_items = max(1, min(train_max_items, TRAIN_MAX_ITEMS))
    max_cases = int(os.getenv("RAG_EVAL_MAX_CASES", str(DEFAULT_MAX_CASES)) or DEFAULT_MAX_CASES)
    max_cases = max(1, max_cases)

    log(f"Loading Qasper_after from {QASPER_AFTER_DIR}")
    log(f"Using strategies: {', '.join(s['name'] for s in STRATEGIES)}")
    log(f"Using top_k values: {', '.join(map(str, TOP_KS))}")
    log(f"Using max papers per split: {max_items}")
    log(f"Using train split max papers: {train_max_items}")
    log(f"Using max QA cases per strategy/top_k: {max_cases}")
    log(f"Using answer language: {ANSWER_LANGUAGE}")

    all_papers: List[Dict[str, Any]] = []
    for split in SPLITS:
        data = load_split(split)
        papers = data.get("papers") if isinstance(data.get("papers"), list) else []
        limit = train_max_items if split == "train" else max_items
        all_papers.extend([p for p in papers if isinstance(p, dict)][:limit])

    cases = collect_cases(all_papers, max_cases)
    all_results: List[Dict[str, Any]] = []
    total_runs = len(cases) * len(STRATEGIES) * len(TOP_KS)
    run_idx = 0

    for strategy in STRATEGIES:
        log(f"=== Strategy start: {strategy['name']} ===")
        for top_k in TOP_KS:
            log(f"--- top_k={top_k} ---")
            for case in cases:
                paper = case["paper"]
                qa = case["qa"]
                run_idx += 1
                log(f"Progress {run_idx}/{max(total_runs, 1)} | {paper.get('paper_id')} | {qa.get('question_id')}")
                try:
                    result = run_single_case(paper, qa, strategy, top_k)
                    all_results.append(result)
                except Exception as exc:
                    all_results.append(
                        {
                            "split": paper.get("source_split"),
                            "paper_id": paper.get("paper_id"),
                            "title": paper.get("title"),
                            "question_id": qa.get("question_id"),
                            "question": qa.get("question"),
                            "gold_answer": (qa.get("gold_answers") or [""])[0] if isinstance(qa.get("gold_answers"), list) else "",
                            "answer": "",
                            "strategy": strategy["name"],
                            "top_k": top_k,
                            "retrieved_count": 0,
                            "cited_chunk_ids": [],
                            "evidence_chunk_ids": qa.get("evidence_chunk_ids") if isinstance(qa.get("evidence_chunk_ids"), list) else [],
                            "exact_match": False,
                            "keyword_hits": 0,
                            "keyword_recall": 0.0,
                            "token_recall": 0.0,
                            "retrieval_hit": False,
                            "evidence_hit": False,
                            "evidence_recall": 0.0,
                            "cited_support_rate": 0.0,
                            "llm_error": "",
                            "error": str(exc),
                        }
                    )

                with PARTIAL_JSON_PATH.open("w", encoding="utf-8") as f:
                    json.dump({"summary": summarize_results(all_results), "results": all_results}, f, ensure_ascii=False, indent=2)

    summary = summarize_results(all_results)
    REPORT_JSON_PATH.write_text(json.dumps({"summary": summary, "results": all_results}, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(summary, all_results, max_cases), encoding="utf-8")

    log(f"Saved JSON report to: {REPORT_JSON_PATH}")
    log(f"Saved MD report to: {REPORT_MD_PATH}")
    log(f"Saved partial JSON report to: {PARTIAL_JSON_PATH}")


if __name__ == "__main__":
    main()
