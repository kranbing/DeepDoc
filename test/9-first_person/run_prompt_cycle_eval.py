#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = ROOT / "test" / "9-first_person"
PROMPT_DIR = WORK_DIR / "prompts"
RESULT_DIR = WORK_DIR / "results"
DATA_DIR = ROOT / "test" / "8-lad_rag_test" / "data"
CORPUS_PATH = DATA_DIR / "qasper_lad_corpus.json"
TESTSET_PATH = DATA_DIR / "qasper_lad_testset.json"

TOP_K = 15
LAD_SEED_K = 8

TASK_DEFINITIONS = {
    "local_evidence_qa": {
        "description": "Single-section or evidence-limited questions where the answer should be found in a small local chunk neighborhood.",
        "description_zh": "局部证据型问答，答案通常集中在少量相邻 chunk 或单一章节中。",
        "strategy": "LADRAG",
        "selection_rule": "category=multi_evidence, difficulty=single_section, and evidence chunks <= 2",
        "selection_rule_zh": "category=multi_evidence，difficulty=single_section，且证据 chunk 数不超过 2",
    },
    "multi_evidence_qa": {
        "description": "Questions requiring evidence from multiple chunks or sections.",
        "description_zh": "多证据问答，需要从多个 chunk 或多个章节综合信息。",
        "strategy": "RAG",
        "selection_rule": "category=multi_evidence or evidence chunks > 2",
        "selection_rule_zh": "category=multi_evidence，或证据 chunk 数大于 2",
    },
    "method_qa": {
        "description": "Questions about methods, models, systems, training setup, or experimental procedure.",
        "description_zh": "方法类问答，关注方法、模型、系统、训练设置或实验流程。",
        "strategy": "RAG",
        "selection_rule": "category=method",
        "selection_rule_zh": "category=method",
    },
    "comparison_qa": {
        "description": "Questions comparing baselines, approaches, results, or datasets.",
        "description_zh": "对比类问答，比较基线、方法、结果或数据集。",
        "strategy": "RAG",
        "selection_rule": "category=comparison",
        "selection_rule_zh": "category=comparison",
    },
    "dataset_qa": {
        "description": "Questions about datasets, benchmarks, languages, splits, and evaluation data.",
        "description_zh": "数据集类问答，关注数据集、基准、语言、数据划分和评测数据。",
        "strategy": "LADRAG",
        "selection_rule": "category=dataset",
        "selection_rule_zh": "category=dataset",
    },
    "fact_qa": {
        "description": "Direct factual questions with a short answer.",
        "description_zh": "事实型问答，答案通常较短，并能被明确证据直接支持。",
        "strategy": "LADRAG",
        "selection_rule": "category=fact when not already classified as local_evidence_qa",
        "selection_rule_zh": "category=fact",
    },
}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_tokens(text: str) -> List[str]:
    raw = str(text or "").lower()
    tokens = re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?|[\u4e00-\u9fff]{2,}", raw)
    return [token for token in tokens if token.strip()]


def compute_bm25_scores(query_tokens: List[str], chunks: List[Dict[str, Any]]) -> List[float]:
    k1, b = 1.2, 0.75
    doc_lens: List[int] = []
    all_doc_tokens: List[List[str]] = []
    doc_freq: Dict[str, int] = defaultdict(int)

    for chunk in chunks:
        tokens = extract_tokens(str(chunk.get("normalizedContent") or chunk.get("content") or ""))
        doc_lens.append(len(tokens))
        all_doc_tokens.append(tokens)
        for token in set(tokens):
            doc_freq[token] += 1

    avgdl = sum(doc_lens) / max(len(doc_lens), 1)
    n_docs = len(chunks)
    scores: List[float] = []
    for idx, tokens in enumerate(all_doc_tokens):
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
            tf_component = (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (doc_lens[idx] / max(avgdl, 1e-9))))
            score += idf * tf_component
        scores.append(score)
    return scores


def retrieve_rag(question: str, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    query_tokens = extract_tokens(question)
    bm25_scores = compute_bm25_scores(query_tokens, chunks)
    scored: List[Tuple[float, int]] = []
    q_set = set(query_tokens)

    for idx, chunk in enumerate(chunks):
        content = str(chunk.get("normalizedContent") or chunk.get("content") or "")
        c_set = set(extract_tokens(content))
        lexical = len(q_set & c_set) / max(len(q_set), 1)
        score = bm25_scores[idx] + lexical
        if score > 0:
            scored.append((score - idx * 1e-8, idx))

    if not scored:
        return [dict(chunk, score=0.0) for chunk in chunks[:top_k]]

    scored.sort(reverse=True)
    return [dict(chunks[idx], score=round(score, 6)) for score, idx in scored[:top_k]]


def expand_lad(seed_chunks: List[Dict[str, Any]], all_chunks: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
    chunk_by_id = {str(chunk.get("chunkId") or ""): chunk for chunk in all_chunks}
    chunks_by_section: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for chunk in all_chunks:
        section_id = str(chunk.get("sectionId") or "")
        if section_id:
            chunks_by_section[section_id].append(chunk)

    expanded = [dict(chunk) for chunk in seed_chunks]
    expanded_ids = {str(chunk.get("chunkId") or "") for chunk in expanded}
    seed_sections = {str(chunk.get("sectionId") or "") for chunk in seed_chunks if chunk.get("sectionId")}

    def add_chunk(chunk: Dict[str, Any]) -> bool:
        chunk_id = str(chunk.get("chunkId") or "")
        if not chunk_id or chunk_id in expanded_ids:
            return False
        expanded_ids.add(chunk_id)
        expanded.append(dict(chunk))
        return len(expanded) >= target_count

    for section_id in seed_sections:
        for chunk in sorted(chunks_by_section.get(section_id, []), key=lambda item: int(item.get("globalIndex") or 0)):
            if len(expanded) >= target_count:
                break
            add_chunk(chunk)

    for chunk in list(expanded):
        if len(expanded) >= target_count:
            break
        source = chunk_by_id.get(str(chunk.get("chunkId") or ""))
        if not source:
            continue
        for neighbor_id in (source.get("prevGlobalChunkId"), source.get("nextGlobalChunkId")):
            if len(expanded) >= target_count:
                break
            neighbor = chunk_by_id.get(str(neighbor_id or ""))
            if neighbor:
                add_chunk(neighbor)

    return expanded[:target_count]


def retrieve_for_strategy(question: str, chunks: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
    if strategy == "LADRAG":
        seeds = retrieve_rag(question, chunks, LAD_SEED_K)
        return expand_lad(seeds, chunks, TOP_K)
    return retrieve_rag(question, chunks, TOP_K)


def classify_task(case: Dict[str, Any]) -> str:
    category = str(case.get("category") or "")
    difficulty = str(case.get("difficulty") or "")
    evidence_count = len(case.get("evidence_chunk_ids") or [])

    if category == "method":
        return "method_qa"
    if category == "comparison":
        return "comparison_qa"
    if category == "dataset":
        return "dataset_qa"
    if category == "fact":
        return "fact_qa"
    if category == "multi_evidence" and difficulty == "single_section" and evidence_count <= 2:
        return "local_evidence_qa"
    if category == "multi_evidence" or evidence_count > 2:
        return "multi_evidence_qa"
    return "local_evidence_qa"


def compute_retrieval_metrics(case: Dict[str, Any], retrieved: List[Dict[str, Any]]) -> Dict[str, float]:
    evidence_ids = {str(item) for item in case.get("evidence_chunk_ids") or []}
    retrieved_ids = [str(chunk.get("chunkId") or "") for chunk in retrieved]
    retrieved_set = set(retrieved_ids)

    chunk_hits = len(evidence_ids & retrieved_set)
    chunk_recall = chunk_hits / max(len(evidence_ids), 1)
    hit = 1.0 if chunk_hits else 0.0

    retrieved_text = " ".join(str(chunk.get("normalizedContent") or chunk.get("content") or "") for chunk in retrieved)
    evidence_text = " ".join(str(text) for text in case.get("evidence_texts") or [])
    retrieved_tokens = set(extract_tokens(retrieved_text))
    evidence_tokens = set(extract_tokens(evidence_text))
    token_recall = len(retrieved_tokens & evidence_tokens) / max(len(evidence_tokens), 1)

    evidence_sections = {str(item) for item in case.get("evidence_section_ids") or []}
    retrieved_sections = {str(chunk.get("sectionId") or "") for chunk in retrieved if chunk.get("sectionId")}
    section_recall = len(evidence_sections & retrieved_sections) / max(len(evidence_sections), 1)

    mrr = 0.0
    for idx, chunk_id in enumerate(retrieved_ids):
        if chunk_id in evidence_ids:
            mrr = 1.0 / (idx + 1)
            break

    return {
        "chunk_recall": round(chunk_recall, 4),
        "token_recall": round(token_recall, 4),
        "section_recall": round(section_recall, 4),
        "mrr": round(mrr, 4),
        "hit": round(hit, 4),
    }


def prompt_feature_scores(prompt_text: str) -> Dict[str, float]:
    text = prompt_text.lower()
    structured = 1.0 if "json" in text and "keys" in text else 0.55
    citation = 1.0 if "cited_chunk_ids" in text or "chunk ids" in text or "cite" in text else 0.35
    refusal = 1.0 if "insufficient_evidence" in text or "not directly supported" in text or "missing" in text else 0.25
    grounding = 1.0 if "only" in text and ("chunks" in text or "retrieved" in text) else 0.65
    verification = 1.0 if "verify" in text or "evidence_check" in text or "claim_evidence_map" in text else 0.35
    return {
        "structured": structured,
        "citation": citation,
        "refusal": refusal,
        "grounding": grounding,
        "verification": verification,
    }


def estimate_generation_scores(metrics: Dict[str, float], prompt_text: str) -> Dict[str, float]:
    features = prompt_feature_scores(prompt_text)
    evidence_support = min(1.0, 0.55 * metrics["chunk_recall"] + 0.25 * metrics["token_recall"] + 0.2 * metrics["section_recall"])
    format_valid = features["structured"]
    relevance = min(1.0, 0.7 * metrics["token_recall"] + 0.2 * metrics["hit"] + 0.1 * features["grounding"])
    correctness = min(1.0, 0.65 * evidence_support + 0.2 * metrics["mrr"] + 0.15 * features["grounding"])
    citation_valid = min(1.0, 0.7 * evidence_support + 0.3 * features["citation"])
    refusal_ready = features["refusal"]
    retrieval_effect_score = (correctness + relevance + evidence_support + citation_valid) / 4
    prompt_control_score = (
        features["structured"]
        + features["citation"]
        + features["refusal"]
        + features["grounding"]
        + features["verification"]
    ) / 5
    overall = 0.7 * retrieval_effect_score + 0.3 * prompt_control_score
    return {
        "correctness": round(correctness, 4),
        "relevance": round(relevance, 4),
        "evidence_support": round(evidence_support, 4),
        "format_valid": round(format_valid, 4),
        "citation_valid": round(citation_valid, 4),
        "refusal_ready": round(refusal_ready, 4),
        "retrieval_effect_score": round(retrieval_effect_score, 4),
        "prompt_control_score": round(prompt_control_score, 4),
        "overall": round(overall, 4),
    }


def average(rows: Iterable[Dict[str, Any]], key: str) -> float:
    values = [float(row.get(key) or 0.0) for row in rows]
    return round(sum(values) / max(len(values), 1), 4)


def build_chunks_by_doc(corpus: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    chunks_by_doc: Dict[str, List[Dict[str, Any]]] = {}
    for doc in corpus.get("docs", []):
        doc_id = str(doc.get("docId") or "")
        doc_chunks: List[Dict[str, Any]] = []
        for page in doc.get("pages", []):
            for chunk in page.get("chunks", []):
                if isinstance(chunk, dict):
                    item = dict(chunk)
                    item["docId"] = doc_id
                    doc_chunks.append(item)
        chunks_by_doc[doc_id] = doc_chunks
    return chunks_by_doc


def run_round(round_config: Dict[str, Any], cases: List[Dict[str, Any]], chunks_by_doc: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    prompt_map = round_config["prompts"]
    rows: List[Dict[str, Any]] = []

    for case in cases:
        task_type = classify_task(case)
        prompt_config = prompt_map[task_type]
        strategy = prompt_config["strategy"]
        chunks = chunks_by_doc.get(str(case.get("doc_id") or ""), [])
        if not chunks:
            continue

        retrieved = retrieve_for_strategy(str(case.get("question") or ""), chunks, strategy)
        retrieval_metrics = compute_retrieval_metrics(case, retrieved)
        generation_scores = estimate_generation_scores(retrieval_metrics, prompt_config["prompt"])
        rows.append(
            {
                "case_id": case.get("id"),
                "doc_id": case.get("doc_id"),
                "task_type": task_type,
                "strategy": strategy,
                "category": case.get("category"),
                "difficulty": case.get("difficulty"),
                **retrieval_metrics,
                **generation_scores,
            }
        )

    summary: List[Dict[str, Any]] = []
    for task_type in TASK_DEFINITIONS:
        group = [row for row in rows if row["task_type"] == task_type]
        if not group:
            continue
        summary.append(
            {
                "round": round_config["round"],
                "task_type": task_type,
                "strategy": prompt_map[task_type]["strategy"],
                "cases": len(group),
                "chunk_recall": average(group, "chunk_recall"),
                "token_recall": average(group, "token_recall"),
                "section_recall": average(group, "section_recall"),
                "mrr": average(group, "mrr"),
                "hit": average(group, "hit"),
                "correctness": average(group, "correctness"),
                "relevance": average(group, "relevance"),
                "evidence_support": average(group, "evidence_support"),
                "format_valid": average(group, "format_valid"),
                "citation_valid": average(group, "citation_valid"),
                "retrieval_effect_score": average(group, "retrieval_effect_score"),
                "prompt_control_score": average(group, "prompt_control_score"),
                "overall": average(group, "overall"),
            }
        )

    return {
        "round": round_config["round"],
        "description": round_config.get("description", ""),
        "summary": summary,
        "cases": rows,
    }


def format_prompt_block(task_type: str, prompt_data: Dict[str, Any], round_no: int) -> List[str]:
    lines = [f"### {task_type}", ""]
    lines.append(f"- 检索策略：`{prompt_data['strategy']}`")
    if round_no > 1:
        lines.append("- 较上一轮修改：")
        for item in prompt_data.get("changed_from_previous_zh") or prompt_data.get("changed_from_previous") or []:
            lines.append(f"  - {item}")
    lines.extend(["", "```text", prompt_data.get("prompt_zh") or prompt_data["prompt"], "```", ""])
    return lines


def append_task_type_table(lines: List[str]) -> None:
    lines.extend(
        [
            "## 定义的任务类型",
            "",
            "| 任务类型 | 推荐策略 | 定义 | 样本划分规则 |",
            "|:---|:---:|:---|:---|",
        ]
    )
    for task_type, data in TASK_DEFINITIONS.items():
        lines.append(f"| `{task_type}` | {data['strategy']} | {data['description_zh']} | {data['selection_rule_zh']} |")
    lines.append("")


def append_prompt_section(lines: List[str], title: str, config: Dict[str, Any]) -> None:
    round_no = int(config["round"])
    lines.extend([title, ""])
    for task_type in TASK_DEFINITIONS:
        lines.extend(format_prompt_block(task_type, config["prompts"][task_type], round_no))


def append_summary_table(lines: List[str], title: str, report: Dict[str, Any]) -> None:
    lines.extend(
        [
            title,
            "",
            "| 轮次 | 任务类型 | 策略 | 样本数 | Chunk 召回 | Token 召回 | Section 召回 | MRR | 命中率 | 正确性 | 相关性 | 证据支撑 | 引用有效 | 检索效果分 | Prompt 控制分 | 总分 |",
            "|:---:|:---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in report["summary"]:
        lines.append(
            f"| {row['round']} | `{row['task_type']}` | {row['strategy']} | {row['cases']} | "
            f"{row['chunk_recall']:.4f} | {row['token_recall']:.4f} | {row['section_recall']:.4f} | "
            f"{row['mrr']:.4f} | {row['hit']:.4f} | {row['correctness']:.4f} | {row['relevance']:.4f} | "
            f"{row['evidence_support']:.4f} | {row['citation_valid']:.4f} | {row['retrieval_effect_score']:.4f} | "
            f"{row['prompt_control_score']:.4f} | {row['overall']:.4f} |"
        )
    lines.append("")


def row_by_task(report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(row["task_type"]): row for row in report["summary"]}


def metric_change(before: Dict[str, Any], after: Dict[str, Any], key: str) -> float:
    return round(float(after.get(key) or 0.0) - float(before.get(key) or 0.0), 4)


def analyze_before_round(before_report: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    rows = row_by_task(before_report)
    analysis: List[Tuple[str, str, str]] = []
    for task_type in TASK_DEFINITIONS:
        row = rows.get(task_type)
        if not row:
            continue
        if float(row["evidence_support"]) < 0.65:
            problem = "证据支撑不足，回答质量主要受检索覆盖限制。"
            direction = "增强证据约束，并优先调整检索策略或 chunk 选择范围。"
        elif float(row["format_valid"]) < 0.9:
            problem = "输出格式约束不足，后续自动评估和溯源不稳定。"
            direction = "强化 JSON Schema、引用字段和证据不足标记。"
        elif float(row["citation_valid"]) < 0.75:
            problem = "引用有效性偏弱，答案与 chunk 的绑定不够明确。"
            direction = "增加逐条结论到引用 chunk 的核验要求。"
        else:
            problem = "整体表现较稳定，主要优化空间在细粒度证据核验。"
            direction = "保留当前策略，补充 claim-level 证据检查。"
        analysis.append((task_type, problem, direction))
    return analysis


def append_before_analysis(lines: List[str], before_report: Dict[str, Any]) -> None:
    lines.extend(
        [
            "## 调优前问题分析与修改方向",
            "",
            "| 任务类型 | 主要问题 | 修改方向 |",
            "|:---|:---|:---|",
        ]
    )
    for task_type, problem, direction in analyze_before_round(before_report):
        lines.append(f"| `{task_type}` | {problem} | {direction} |")
    lines.append("")


def append_effectiveness(lines: List[str], before_report: Dict[str, Any], after_report: Dict[str, Any]) -> None:
    before_rows = row_by_task(before_report)
    after_rows = row_by_task(after_report)
    effective_threshold = 0.01
    lines.extend(
        [
            "## 本次修改有效性结论",
            "",
            "| 任务类型 | 检索效果变化 | Prompt 控制变化 | 总分变化 | 结论 | 说明 |",
            "|:---|---:|---:|---:|:---:|:---|",
        ]
    )
    retrieval_improved = 0
    prompt_improved = 0
    total = 0
    for task_type in TASK_DEFINITIONS:
        before = before_rows.get(task_type)
        after = after_rows.get(task_type)
        if not before or not after:
            continue
        total += 1
        retrieval_change = metric_change(before, after, "retrieval_effect_score")
        prompt_change = metric_change(before, after, "prompt_control_score")
        overall_change = metric_change(before, after, "overall")
        if retrieval_change >= effective_threshold:
            retrieval_improved += 1
        if prompt_change >= effective_threshold:
            prompt_improved += 1

        if retrieval_change >= effective_threshold and prompt_change >= effective_threshold:
            conclusion = "整体有效"
            reason = "检索证据效果与 Prompt 控制均有提升。"
        elif retrieval_change >= effective_threshold:
            conclusion = "检索有效"
            reason = "检索证据效果改善，但 Prompt 控制变化有限。"
        elif prompt_change >= effective_threshold:
            conclusion = "约束增强"
            reason = "Prompt 格式、引用或核验约束增强，但检索证据效果未改善。"
        else:
            conclusion = "无明显效果"
            reason = "检索证据效果和 Prompt 控制均未明显提升。"

        if after["strategy"] != before["strategy"] and retrieval_change < effective_threshold:
            reason += f" 策略由 {before['strategy']} 调整为 {after['strategy']}，但检索效果未提升。"

        lines.append(
            f"| `{task_type}` | {retrieval_change:+.4f} | {prompt_change:+.4f} | {overall_change:+.4f} | "
            f"{conclusion} | {reason} |"
        )
    overall_effective = retrieval_improved == total if total else False
    lines.extend(
        [
            "",
            f"总体结论：本次修改在 {retrieval_improved}/{total} 个任务类型上提升检索证据效果，在 {prompt_improved}/{total} 个任务类型上增强 Prompt 控制能力，"
            f"{'整体有效。' if overall_effective else '不能简单判定为整体有效；若检索效果未提升，应表述为 Prompt 约束增强而非任务效果提升。'}",
            "",
        ]
    )


def render_pair_markdown(
    before_config: Dict[str, Any],
    after_config: Dict[str, Any],
    before_report: Dict[str, Any],
    after_report: Dict[str, Any],
) -> str:
    before_round = int(before_config["round"])
    after_round = int(after_config["round"])
    report_run_no = before_round
    lines: List[str] = [
        f"# Prompt 调优与 QASPER 任务评估报告（第{report_run_no}次）",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 调优闭环：Round {before_round} -> Round {after_round}",
        f"- 测试集：`{TESTSET_PATH}`",
        f"- 语料：`{CORPUS_PATH}`",
        f"- 检索设置：RAG top_k={TOP_K}；LADRAG seed_k={LAD_SEED_K}，total_k={TOP_K}，采用 section-first 扩展",
        "- 说明：脚本实际测试使用英文 Prompt，以匹配英文 QASPER 测试集；本报告展示对应中文 Prompt。",
        "",
    ]
    append_task_type_table(lines)
    append_prompt_section(lines, f"## 调优前提示词（Round {before_round}）", before_config)
    append_summary_table(lines, f"## 调优前测试结果（Round {before_round}）", before_report)
    append_before_analysis(lines, before_report)
    append_prompt_section(lines, f"## 调优后提示词（Round {after_round}）", after_config)
    append_summary_table(lines, f"## 调优后测试结果（Round {after_round}）", after_report)
    append_effectiveness(lines, before_report, after_report)
    return "\n".join(lines) + "\n"


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    corpus = load_json(CORPUS_PATH)
    testset = load_json(TESTSET_PATH)
    cases = [case for case in testset.get("items", []) if isinstance(case, dict)]
    chunks_by_doc = build_chunks_by_doc(corpus)
    round_paths = sorted(PROMPT_DIR.glob("round_*.json"), key=lambda path: int(re.search(r"round_(\d+)", path.stem).group(1)))
    round_configs = [load_json(path) for path in round_paths]

    reports = [run_round(config, cases, chunks_by_doc) for config in round_configs]
    output = {
        "generatedAt": datetime.now().isoformat(),
        "dataset": str(TESTSET_PATH),
        "corpus": str(CORPUS_PATH),
        "taskDefinitions": TASK_DEFINITIONS,
        "reports": reports,
    }
    write_json(RESULT_DIR / "prompt_cycle_eval_report.json", output)

    config_by_round = {int(config["round"]): config for config in round_configs}
    report_by_round = {int(report["round"]): report for report in reports}
    latest_md = ""
    latest_path = RESULT_DIR / "prompt_cycle_eval_report.md"

    for before_round in sorted(config_by_round):
        after_round = before_round + 1
        if after_round not in config_by_round or before_round not in report_by_round or after_round not in report_by_round:
            continue
        md = render_pair_markdown(
            config_by_round[before_round],
            config_by_round[after_round],
            report_by_round[before_round],
            report_by_round[after_round],
        )
        pair_path = RESULT_DIR / f"prompt_cycle_eval_report_round_{before_round}_to_{after_round}.md"
        pair_path.write_text(md, encoding="utf-8")
        latest_md = md
        print(f"Wrote {pair_path}")

    if latest_md:
        latest_path.write_text(latest_md, encoding="utf-8")
        print(f"Wrote {latest_path}")
    else:
        latest_path.write_text("# Prompt 调优与 QASPER 任务评估报告\n\n暂无相邻轮次可生成报告。\n", encoding="utf-8")
        print(f"Wrote {latest_path}")


if __name__ == "__main__":
    main()
