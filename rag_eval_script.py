from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.main import read_workspace
from backend.services.overview_service import ensure_document_overview, read_document_overview
from backend.services.qa_service import (
    ask_deepseek_with_selection_v2,
    normalize_chunk_context_items,
)
from backend.services.project_store import ensure_project_layout
from backend.services.vector_store import search_project_vector_index

# Best three chunk strategies from chunk_strategy_test/report.md
STRATEGIES: List[Dict[str, Any]] = [
    {"name": "rag_500_100", "label": "RAG Text Chunks", "strategy": "rag", "chunk_size": 500, "overlap": 100},
    {"name": "rag_300_100", "label": "RAG Text Chunks", "strategy": "rag", "chunk_size": 300, "overlap": 100},
    {"name": "semantic_78_600_900_160", "label": "Semantic Text Chunks", "strategy": "semantic", "config_hint": "semantic_78_600_900_160"},
]
TOP_KS = [1, 3, 5]

TESTSET_PATH = ROOT / "rag_test" / "testset.json"
REPORT_JSON_PATH = ROOT / "rag_eval_report.json"
REPORT_MD_PATH = ROOT / "rag_eval_report.md"


def load_testset() -> Dict[str, Any]:
    log(f"Loading testset from {TESTSET_PATH}")
    with open(TESTSET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    log(f"Loaded {len(data.get('items') or [])} test cases")
    return data


def resolve_project_and_doc(testset: Dict[str, Any]) -> Tuple[Path, Dict[str, Any]]:
    project_id = str(testset.get("source_project_id") or "").strip()
    doc_id = str(testset.get("source_document_id") or "").strip()
    if not project_id or not doc_id:
        raise RuntimeError("testset.json 缺少 source_project_id 或 source_document_id")

    project_dir = ROOT / "data" / "projects" / project_id
    log(f"Resolving project {project_id}")
    ensure_project_layout(project_dir)
    ws = read_workspace(project_dir)
    docs = ws.get("docs") if isinstance(ws.get("docs"), list) else []
    doc = next((item for item in docs if isinstance(item, dict) and str(item.get("id") or "") == doc_id), None)
    if not doc:
        raise RuntimeError(f"未在 workspace 中找到文档: {doc_id}")
    log(f"Resolved document {doc_id}: {doc.get('name') or doc_id}")
    return project_dir, doc


def compute_score(answer: str, gold_answer: str, keywords: Sequence[str]) -> Dict[str, Any]:
    answer_l = answer.lower().strip()
    gold_l = gold_answer.lower().strip()
    keyword_hits = sum(1 for kw in keywords if str(kw).lower() in answer_l)
    exact = answer_l == gold_l
    contains_gold_core = all(token.lower() in answer_l for token in gold_answer.split()[:3]) if gold_answer else False
    return {
        "exact_match": exact,
        "keyword_hits": keyword_hits,
        "contains_gold_core": contains_gold_core,
    }


def build_context_for_question(
    project_dir: Path,
    doc: Dict[str, Any],
    question: str,
    top_k: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], str]:
    doc_id = str(doc.get("id") or "")
    log(f"Retrieving chunks with top_k={top_k} for question: {question}")
    search_res = search_project_vector_index(project_dir, question, top_k=top_k, doc_id=doc_id)
    current_chunks = normalize_chunk_context_items(search_res.get("results"))
    log(f"Retrieved {len(current_chunks)} chunks")
    support_chunks: List[Dict[str, Any]] = []
    overview = read_document_overview(project_dir, doc_id)
    if not isinstance(overview, dict) or str(overview.get("status") or "") != "ready":
        log("Overview missing or not ready, generating overview")
        try:
            overview = ensure_document_overview(ROOT, project_dir, doc)
        except Exception as exc:
            log(f"Overview generation failed: {exc}")
            overview = {}
    return current_chunks, support_chunks, overview, "auto_retrieval"


def run_case(
    project_dir: Path,
    doc: Dict[str, Any],
    item: Dict[str, Any],
    strategy: Dict[str, Any],
    top_k: int,
) -> Dict[str, Any]:
    question = str(item.get("question") or "").strip()
    gold_answer = str(item.get("gold_answer") or "").strip()
    doc_name = str(doc.get("name") or doc.get("id") or "")
    log(f"Running {strategy['name']} | top_k={top_k} | {item.get('id')}: {question}")
    current_chunks, support_chunks, overview, context_source = build_context_for_question(project_dir, doc, question, top_k)

    try:
        qa = ask_deepseek_with_selection_v2(
            ROOT,
            current_chunks,
            support_chunks,
            question,
            doc_name,
            doc_id=str(doc.get("id") or ""),
            doc_overview=overview,
            compacted_context="",
            recent_turns=[],
            manual_selected=False,
            context_source=context_source,
        )
        answer = str(qa.get("answer") or "")
        cited_chunk_ids = qa.get("cited_chunk_ids") if isinstance(qa.get("cited_chunk_ids"), list) else []
        follow_up_questions = qa.get("follow_up_questions") if isinstance(qa.get("follow_up_questions"), list) else []
        log(f"QA done | cited={len(cited_chunk_ids)} | answer_len={len(answer)}")
    except Exception as exc:
        log(f"QA failed: {exc}")
        raise

    metrics = compute_score(answer, gold_answer, item.get("expected_keywords") or item.get("keywords") or [])
    return {
        "test_id": item.get("id"),
        "category": item.get("category"),
        "difficulty": item.get("difficulty"),
        "question": question,
        "gold_answer": gold_answer,
        "answer": answer,
        "cited_chunk_ids": cited_chunk_ids,
        "follow_up_questions": follow_up_questions,
        "retrieved_count": len(current_chunks),
        "strategy": strategy["name"],
        "top_k": top_k,
        **metrics,
    }


def summarize_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    for item in results:
        key = (str(item["strategy"]), int(item["top_k"]))
        groups.setdefault(key, []).append(item)

    summary: List[Dict[str, Any]] = []
    for (strategy_name, top_k), items in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        total = len(items)
        exact = sum(1 for x in items if x.get("exact_match"))
        keyword = sum(1 for x in items if x.get("keyword_hits", 0) > 0)
        core = sum(1 for x in items if x.get("contains_gold_core"))
        avg_retrieved = sum(int(x.get("retrieved_count") or 0) for x in items) / max(total, 1)
        summary.append(
            {
                "strategy": strategy_name,
                "top_k": top_k,
                "total": total,
                "exact_match_rate": round(exact / total, 4) if total else 0.0,
                "keyword_hit_rate": round(keyword / total, 4) if total else 0.0,
                "gold_core_rate": round(core / total, 4) if total else 0.0,
                "avg_retrieved": round(avg_retrieved, 2),
            }
        )
    return summary


def render_markdown(testset: Dict[str, Any], results: List[Dict[str, Any]], summary: List[Dict[str, Any]]) -> str:
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = testset.get("source_document_name") or testset.get("source_document_id")
    lines: List[str] = []
    lines.append("# RAG 主链路测试报告")
    lines.append("")
    lines.append(f"- 生成时间：{created_at}")
    lines.append(f"- 来源项目：{testset.get('source_project_id')}")
    lines.append(f"- 来源文档：{project_name}")
    lines.append(f"- 测试集规模：{len(testset.get('items') or [])}")
    lines.append(f"- 分块策略：{', '.join(strategy['name'] for strategy in STRATEGIES)}")
    lines.append(f"- TOPK：{', '.join(map(str, TOP_KS))}")
    lines.append("")
    lines.append("## 策略与 TOPK 汇总")
    lines.append("")
    lines.append("| Strategy | TOPK | Total | Exact Match | Keyword Hit | Gold-Core | Avg Retrieved |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for s in summary:
        lines.append(
            f"| {s['strategy']} | {s['top_k']} | {s['total']} | {s['exact_match_rate']:.4f} | {s['keyword_hit_rate']:.4f} | {s['gold_core_rate']:.4f} | {s['avg_retrieved']:.2f} |"
        )

    lines.append("")
    lines.append("## 详细结果")
    lines.append("")
    for item in results:
        lines.append(f"### {item['test_id']} | {item['strategy']} | top_k={item['top_k']}")
        lines.append(f"- 类别：{item['category']} | 难度：{item['difficulty']}")
        lines.append(f"- 问题：{item['question']}")
        lines.append(f"- 标准答案：{item['gold_answer']}")
        lines.append(f"- 模型答案：{item['answer']}")
        lines.append(f"- 引用 chunks：{', '.join(item['cited_chunk_ids']) if item['cited_chunk_ids'] else '无'}")
        lines.append(f"- 召回块数：{item['retrieved_count']}")
        lines.append(f"- exact_match：{item['exact_match']}")
        lines.append(f"- keyword_hits：{item['keyword_hits']}")
        lines.append(f"- gold_core：{item['contains_gold_core']}")
        if item.get("follow_up_questions"):
            lines.append(f"- follow_up_questions：{' | '.join(map(str, item['follow_up_questions']))}")
        if item.get("error"):
            lines.append(f"- error：{item['error']}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    log("Starting RAG evaluation script")
    testset = load_testset()
    project_dir, doc = resolve_project_and_doc(testset)
    log(f"Using strategies: {', '.join(strategy['name'] for strategy in STRATEGIES)}")
    log(f"Using top_k values: {', '.join(map(str, TOP_KS))}")

    all_results: List[Dict[str, Any]] = []
    total_runs = len(STRATEGIES) * len(TOP_KS) * len(testset.get("items") or [])
    run_idx = 0
    for strategy in STRATEGIES:
        log(f"=== Strategy start: {strategy['name']} ===")
        for top_k in TOP_KS:
            log(f"--- top_k={top_k} ---")
            for item in testset.get("items") or []:
                if not isinstance(item, dict):
                    continue
                run_idx += 1
                log(f"Progress {run_idx}/{total_runs}")
                try:
                    result = run_case(project_dir, doc, item, strategy, top_k)
                    all_results.append(result)
                except Exception as exc:
                    log(f"Recorded failure for {item.get('id')}: {exc}")
                    all_results.append(
                        {
                            "test_id": item.get("id"),
                            "category": item.get("category"),
                            "difficulty": item.get("difficulty"),
                            "question": item.get("question"),
                            "gold_answer": item.get("gold_answer"),
                            "answer": "",
                            "cited_chunk_ids": [],
                            "follow_up_questions": [],
                            "retrieved_count": 0,
                            "strategy": strategy["name"],
                            "top_k": top_k,
                            "exact_match": False,
                            "keyword_hits": 0,
                            "contains_gold_core": False,
                            "error": str(exc),
                        }
                    )

                # 逐步落盘，避免最后 JSON 序列化失败导致全部结果丢失
                partial_payload = {
                    "summary": summarize_results(all_results),
                    "results": all_results,
                }
                with open(REPORT_JSON_PATH.with_suffix(".partial.json"), "w", encoding="utf-8") as f:
                    json.dump(partial_payload, f, ensure_ascii=False, indent=2)

    summary = summarize_results(all_results)
    report_md = render_markdown(testset, all_results, summary)

    with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": all_results}, f, ensure_ascii=False, indent=2)
    with open(REPORT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(report_md)

    log(f"Saved JSON report to: {REPORT_JSON_PATH}")
    log(f"Saved MD report to: {REPORT_MD_PATH}")
    log(f"Saved partial JSON report to: {REPORT_JSON_PATH.with_suffix('.partial.json')}")


if __name__ == "__main__":
    main()
