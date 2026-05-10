#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TESTSET_CANDIDATES = [
    ROOT / "test" / "8-lad_rag_test" / "data" / "qasper_lad_testset.json",
    ROOT / "test" / "lad_rag_test" / "data" / "qasper_lad_testset.json",
    ROOT / "test" / "Qasper_after" / "validation.json",
    ROOT / "test" / "rag_test" / "testset.json",
]
OUT_DIR = ROOT / "test" / "9-second_person" / "results"
MODEL_CONFIG_PATH = ROOT / "test" / "9-second_person" / "model_configs.json"

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.clients.deepseek_client import deepseek_chat_json
from backend.services.task_dispatcher import dispatch_task


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_testset_path(user_path: str = "") -> Path:
    if user_path:
        path = Path(user_path)
        if not path.is_absolute():
            path = ROOT / path
        if not path.is_file():
            raise FileNotFoundError(f"Testset not found: {path}")
        return path
    for path in DEFAULT_TESTSET_CANDIDATES:
        if path.is_file():
            return path
    tried = "\n".join(str(path) for path in DEFAULT_TESTSET_CANDIDATES)
    raise FileNotFoundError(f"No supported testset found. Tried:\n{tried}")


def normalize_cases(data: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    if isinstance(data.get("items"), list):
        return [case for case in data["items"] if isinstance(case, dict)][:limit]

    if isinstance(data.get("cases"), list):
        return [case for case in data["cases"] if isinstance(case, dict)][:limit]

    papers = data.get("papers") if isinstance(data.get("papers"), list) else []
    out: List[Dict[str, Any]] = []
    for paper in papers:
        if not isinstance(paper, dict):
            continue
        qas = paper.get("qas") if isinstance(paper.get("qas"), list) else []
        paragraphs: List[str] = []
        full_text = paper.get("full_text") if isinstance(paper.get("full_text"), dict) else {}
        for section in full_text.get("paragraphs") if isinstance(full_text.get("paragraphs"), list) else []:
            if isinstance(section, list):
                paragraphs.extend(str(p).strip() for p in section if str(p).strip())
        fallback_evidence = paragraphs[:3] or [str(paper.get("abstract") or "")]
        for idx, qa in enumerate(qas):
            if not isinstance(qa, dict):
                continue
            question = str(qa.get("question") or "").strip()
            if not question:
                continue
            answers = qa.get("answers") if isinstance(qa.get("answers"), list) else []
            evidence_texts: List[str] = []
            for answer in answers:
                if not isinstance(answer, dict):
                    continue
                evidence = answer.get("evidence") if isinstance(answer.get("evidence"), list) else []
                evidence_texts.extend(str(item).strip() for item in evidence if str(item).strip())
            out.append(
                {
                    "id": f"{paper.get('paper_id', 'paper')}_{idx:04d}",
                    "paper_id": paper.get("paper_id"),
                    "paper_title": paper.get("title"),
                    "question": question,
                    "evidence_texts": evidence_texts or fallback_evidence,
                }
            )
            if len(out) >= limit:
                return out
    return out


def build_prompt(case: Dict[str, Any], route: Any) -> str:
    evidence_texts = case.get("evidence_texts") if isinstance(case.get("evidence_texts"), list) else []
    chunks = []
    for idx, text in enumerate(evidence_texts[:6]):
        chunks.append(f"[evidence_{idx + 1}]\n{str(text).strip()}")
    if not chunks:
        chunks.append("[evidence_1]\n(no evidence text provided)")

    return "\n\n".join(
        [
            f"Paper title: {case.get('paper_title') or ''}",
            f"Question: {case.get('question') or ''}",
            f"Task type: {route.task_type}",
            f"Retrieval mode: {route.retrieval_mode}",
            f"Task instruction: {route.prompt_template}",
            "Evidence chunks:",
            "\n\n".join(chunks),
            (
                "Return JSON only with keys: answer, cited_chunk_ids, follow_up_questions. "
                "Use evidence ids such as evidence_1 as cited_chunk_ids."
            ),
        ]
    )


def evaluate_payload(payload: Dict[str, Any], elapsed_ms: int, mode: str, case: Dict[str, Any], route: Any) -> Dict[str, Any]:
    cited = payload.get("cited_chunk_ids") if isinstance(payload.get("cited_chunk_ids"), list) else []
    answer = str(payload.get("answer") or "")
    follow = payload.get("follow_up_questions") if isinstance(payload.get("follow_up_questions"), list) else []
    return {
        "case_id": case.get("id"),
        "question": case.get("question"),
        "mode": mode,
        "task_type": route.task_type,
        "retrieval_mode": route.retrieval_mode,
        "format_valid": bool(answer and isinstance(cited, list) and isinstance(follow, list)),
        "citation_field_present": "cited_chunk_ids" in payload,
        "citation_count": len(cited),
        "cited_chunk_ids": [str(item) for item in cited],
        "answer_length": len(answer),
        "answer": answer,
        "raw_response": payload,
        "latency_ms": elapsed_ms,
        "error": "",
    }


def summarize(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    modes = sorted({str(row["mode"]) for row in rows})
    summary = []
    for mode in modes:
        group = [row for row in rows if row["mode"] == mode]
        total = len(group)
        errors = [row for row in group if row.get("error")]
        ok = [row for row in group if not row.get("error")]
        summary.append(
            {
                "mode": mode,
                "total": total,
                "error_rate": round(len(errors) / max(total, 1), 4),
                "format_valid_rate": round(sum(1 for row in ok if row.get("format_valid")) / max(len(ok), 1), 4),
                "citation_present_rate": round(sum(1 for row in ok if row.get("citation_field_present")) / max(len(ok), 1), 4),
                "avg_latency_ms": round(sum(int(row.get("latency_ms") or 0) for row in ok) / max(len(ok), 1), 2),
                "avg_answer_length": round(sum(int(row.get("answer_length") or 0) for row in ok) / max(len(ok), 1), 2),
            }
        )
    return summary


def render_md(summary: List[Dict[str, Any]], rows: List[Dict[str, Any]], testset_path: Path) -> str:
    fastest = min(summary, key=lambda item: item["avg_latency_ms"]) if summary else None
    longest = max(summary, key=lambda item: item["avg_answer_length"]) if summary else None
    lowest_error = min(summary, key=lambda item: item["error_rate"]) if summary else None
    lines = [
        "# 第二人模型参数测试报告",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 测试集：`{testset_path}`",
        "- 说明：该脚本真实调用 DeepSeek API，需要配置 `DEEPSEEK_API_KEY` 或 `backend/.deepseek_api_key`。",
        "",
        "## 参数模式汇总",
        "",
        "| 参数模式 | 样本数 | 错误率 | 格式合规率 | 引用字段存在率 | 平均延迟(ms) | 平均答案长度 |",
        "|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        lines.append(
            f"| {item['mode']} | {item['total']} | {item['error_rate']:.4f} | "
            f"{item['format_valid_rate']:.4f} | {item['citation_present_rate']:.4f} | "
            f"{item['avg_latency_ms']:.2f} | {item['avg_answer_length']:.2f} |"
        )

    lines.extend(["", "## 参数影响分析", ""])
    if fastest:
        lines.append(f"- 延迟最低的参数模式：`{fastest['mode']}`，平均延迟 {fastest['avg_latency_ms']:.2f} ms。")
    if longest:
        lines.append(f"- 回答最长的参数模式：`{longest['mode']}`，平均答案长度 {longest['avg_answer_length']:.2f} 字符。")
    if lowest_error:
        lines.append(f"- 错误率最低的参数模式：`{lowest_error['mode']}`，错误率 {lowest_error['error_rate']:.4f}。")
    lines.append("- 解释：`stable` 更偏稳定和短回答；`balanced` 用于默认折中；`exploratory` 更容易生成更长答案，但可能带来更高延迟。")

    lines.extend(
        [
            "",
            "## 样本明细",
            "",
            "| Case | 参数模式 | 任务类型 | 检索策略 | 格式合规 | 引用数 | 延迟(ms) | 错误 |",
            "|:---|:---|:---|:---:|:---:|---:|---:|:---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.get('case_id')} | {row.get('mode')} | `{row.get('task_type')}` | {row.get('retrieval_mode')} | "
            f"{row.get('format_valid')} | {row.get('citation_count')} | {row.get('latency_ms')} | {row.get('error') or ''} |"
        )

    lines.extend(["", "## 模型回答样例", ""])
    for row in rows[: min(len(rows), 12)]:
        answer = str(row.get("answer") or "").replace("\n", " ").strip()
        if len(answer) > 500:
            answer = answer[:500] + "..."
        cited = ", ".join(row.get("cited_chunk_ids") or [])
        lines.extend(
            [
                f"### {row.get('case_id')} | {row.get('mode')} | `{row.get('task_type')}`",
                "",
                f"- 问题：{row.get('question')}",
                f"- 引用：{cited or '无'}",
                f"- 回答：{answer or row.get('error') or '无回答'}",
                "",
            ]
        )

    lines.extend(["## 工程结论", ""])
    if summary:
        lines.append("- 任务分发链路已跑通：每条样本都经过 `task_type -> retrieval_mode -> prompt -> model_config`。")
        lines.append("- 大模型异常处理已进入真实调用路径：API 错误、超时、空响应、JSON 解析失败会写入样本明细。")
        lines.append("- 后续若要评估正确性，需要接入 gold answer 或 evidence 一致性评分；当前报告主要评估参数对格式、引用、长度和延迟的影响。")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real LLM parameter tests for task-dispatched QASPER cases.")
    parser.add_argument("--limit", type=int, default=6, help="Maximum QASPER cases to test.")
    parser.add_argument("--modes", nargs="+", default=["stable", "balanced", "exploratory"], help="Parameter modes to run.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between API calls.")
    parser.add_argument("--testset", default="", help="Optional testset path. Supports qasper_lad_testset.json or Qasper_after/*.json.")
    args = parser.parse_args()

    configs = load_json(MODEL_CONFIG_PATH)
    testset_path = resolve_testset_path(args.testset)
    testset = load_json(testset_path)
    cases = normalize_cases(testset, max(1, args.limit))
    if not cases:
        raise RuntimeError(f"No supported QA cases found in {testset_path}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    system_prompt = (
        "You are a careful academic QA assistant. Answer only from provided evidence. "
        "Return exactly one JSON object."
    )
    for case in cases:
        route = dispatch_task(str(case.get("question") or ""), requested_retrieval_mode="auto")
        user_prompt = build_prompt(case, route)
        for mode in args.modes:
            cfg = configs[mode]
            start = time.time()
            try:
                payload = deepseek_chat_json(
                    ROOT,
                    system_prompt,
                    user_prompt,
                    model=str(cfg.get("model") or "deepseek-chat"),
                    temperature=float(cfg.get("temperature", 0.2)),
                    top_p=float(cfg.get("top_p", 0.9)),
                    max_tokens=int(cfg.get("max_tokens", 768)),
                    timeout_seconds=int(cfg.get("timeout_seconds", 120)),
                    max_retries=int(cfg.get("max_retries", 2)),
                )
                elapsed_ms = int((time.time() - start) * 1000)
                rows.append(evaluate_payload(payload, elapsed_ms, mode, case, route))
            except HTTPException as exc:
                elapsed_ms = int((time.time() - start) * 1000)
                rows.append(
                    {
                        "case_id": case.get("id"),
                        "question": case.get("question"),
                        "mode": mode,
                        "task_type": route.task_type,
                        "retrieval_mode": route.retrieval_mode,
                        "format_valid": False,
                        "citation_field_present": False,
                        "citation_count": 0,
                        "cited_chunk_ids": [],
                        "answer_length": 0,
                        "answer": "",
                        "raw_response": {},
                        "latency_ms": elapsed_ms,
                        "error": str(exc.detail)[:300],
                    }
                )
            if args.sleep > 0:
                time.sleep(args.sleep)

    summary = summarize(rows)
    report = {
        "generatedAt": datetime.now().isoformat(),
        "testset": str(testset_path),
        "configs": configs,
        "summary": summary,
        "rows": rows,
    }
    (OUT_DIR / "model_param_test_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "model_param_test_report.md").write_text(render_md(summary, rows, testset_path), encoding="utf-8-sig")
    print(f"Wrote {OUT_DIR / 'model_param_test_report.md'}")


if __name__ == "__main__":
    main()
