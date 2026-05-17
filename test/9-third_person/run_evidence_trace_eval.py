#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.evidence_trace import build_evidence_trace

SECOND_REPORT = ROOT / "test" / "9-second_person" / "results" / "model_param_test_report.json"
OUT_DIR = ROOT / "test" / "9-third_person" / "results"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_testset_path(second_report: Dict[str, Any]) -> Path:
    value = str(second_report.get("testset") or "").strip()
    if value:
        path = Path(value)
        if path.is_file():
            return path
    fallback = ROOT / "test" / "8-lad_rag_test" / "data" / "qasper_lad_testset.json"
    if fallback.is_file():
        return fallback
    raise FileNotFoundError("Cannot resolve QASPER testset path from second-person report.")


def build_case_map(testset: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    items = testset.get("items") if isinstance(testset.get("items"), list) else []
    return {str(item.get("id")): item for item in items if isinstance(item, dict) and item.get("id")}


def chunk_context_from_case(case: Dict[str, Any]) -> Dict[str, Any]:
    evidence_texts = case.get("evidence_texts") if isinstance(case.get("evidence_texts"), list) else []
    evidence_chunk_ids = case.get("evidence_chunk_ids") if isinstance(case.get("evidence_chunk_ids"), list) else []
    chunks: List[Dict[str, Any]] = []
    for idx, text in enumerate(evidence_texts):
        cid = f"evidence_{idx + 1}"
        source_id = str(evidence_chunk_ids[idx]) if idx < len(evidence_chunk_ids) else ""
        chunks.append(
            {
                "chunkId": cid,
                "chunkKey": cid,
                "sourceChunkId": source_id,
                "pageNo": 0,
                "index": idx,
                "sectionId": "",
                "sectionPathText": "QASPER evidence",
                "headingText": "",
                "content": str(text or ""),
            }
        )
    return {"source": "qasper_evidence", "currentChunks": chunks, "neighborChunks": [], "retrievalChunks": []}


def enforce_structured_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    raw = row.get("raw_response") if isinstance(row.get("raw_response"), dict) else {}
    payload = dict(raw)
    payload.setdefault("answer", row.get("answer") or "")
    payload.setdefault("cited_chunk_ids", row.get("cited_chunk_ids") if isinstance(row.get("cited_chunk_ids"), list) else [])
    payload.setdefault("follow_up_questions", [])
    payload.setdefault("insufficient_evidence", False)
    if "claim_evidence_map" not in payload:
        answer = str(payload.get("answer") or "").strip()
        payload["claim_evidence_map"] = {answer: payload.get("cited_chunk_ids") or []} if answer else {}
    return payload


def avg(rows: List[Dict[str, Any]], key_path: List[str]) -> float:
    values = []
    for row in rows:
        cur: Any = row
        for key in key_path:
            cur = cur.get(key) if isinstance(cur, dict) else None
        if isinstance(cur, (int, float)):
            values.append(float(cur))
    return round(sum(values) / max(len(values), 1), 4)


def summarize(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in results:
        groups[str(item.get("task_type") or "unknown")].append(item)
    summary = []
    for task_type, rows in sorted(groups.items()):
        total = len(rows)
        summary.append(
            {
                "task_type": task_type,
                "total": total,
                "structured_valid_rate": round(
                    sum(1 for row in rows if row["trace"]["structured_validation"]["valid"]) / max(total, 1),
                    4,
                ),
                "citation_exist_rate": avg(rows, ["trace", "consistency", "citation_exist_rate"]),
                "trace_complete_rate": avg(rows, ["trace", "consistency", "trace_complete_rate"]),
                "claim_supported_rate": avg(rows, ["trace", "consistency", "claim_supported_rate"]),
                "avg_support_score": avg(rows, ["trace", "consistency", "avg_support_score"]),
                "invalid_citation_count": sum(
                    int(row["trace"]["consistency"]["invalid_citation_count"]) for row in rows
                ),
                "missing_citation_rate": round(
                    sum(1 for row in rows if row["trace"]["consistency"]["missing_citation"]) / max(total, 1),
                    4,
                ),
            }
        )
    return summary


def render_md(summary: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> str:
    lines = [
        "# Chunk 证据链答案溯源评估报告",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 输入报告：`{SECOND_REPORT}`",
        "- 说明：本报告复用第二人真实大模型输出，构造 QASPER evidence chunk_context，评估结构化输出、引用存在性和 claim->chunk 支撑一致性。",
        "",
        "## 结构化输出要求",
        "",
        "| 字段 | 要求 |",
        "|:---|:---|",
        "| `answer` | 模型最终答案，字符串 |",
        "| `cited_chunk_ids` | 答案引用的 chunk 编号列表 |",
        "| `claim_evidence_map` | 每个关键结论对应的依赖 chunk 编号 |",
        "| `insufficient_evidence` | 证据不足时为 true |",
        "| `follow_up_questions` | 后续问题列表 |",
        "",
        "## 汇总结果",
        "",
        "| 任务类型 | 样本数 | 结构合规率 | 引用存在率 | 定位完整率 | Claim 支撑率 | 平均支撑分 | 无效引用数 | 缺失引用率 |",
        "|:---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| `{row['task_type']}` | {row['total']} | {row['structured_valid_rate']:.4f} | "
            f"{row['citation_exist_rate']:.4f} | {row['trace_complete_rate']:.4f} | "
            f"{row['claim_supported_rate']:.4f} | {row['avg_support_score']:.4f} | "
            f"{row['invalid_citation_count']} | {row['missing_citation_rate']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## 样本明细",
            "",
            "| Case | 参数模式 | 任务类型 | 结构合规 | 引用存在率 | Claim 支撑率 | 平均支撑分 | 缺失引用 |",
            "|:---|:---|:---|:---:|---:|---:|---:|:---|",
        ]
    )
    for item in results:
        trace = item["trace"]
        consistency = trace["consistency"]
        validation = trace["structured_validation"]
        lines.append(
            f"| {item['case_id']} | {item['mode']} | `{item['task_type']}` | {validation['valid']} | "
            f"{consistency['citation_exist_rate']:.4f} | {consistency['claim_supported_rate']:.4f} | "
            f"{consistency['avg_support_score']:.4f} | {', '.join(trace['missing_chunk_ids']) or '无'} |"
        )

    lines.extend(["", "## 错误案例", ""])
    bad_cases = [
        item
        for item in results
        if not item["trace"]["structured_validation"]["valid"]
        or item["trace"]["missing_chunk_ids"]
        or item["trace"]["consistency"]["claim_supported_rate"] < 1.0
    ]
    for item in bad_cases[:10]:
        trace = item["trace"]
        lines.extend(
            [
                f"### {item['case_id']} | {item['mode']} | `{item['task_type']}`",
                "",
                f"- 问题：{item.get('question')}",
                f"- 答案：{item.get('answer')}",
                f"- 缺失字段：{', '.join(trace['structured_validation']['missing_keys']) or '无'}",
                f"- 类型错误：{', '.join(trace['structured_validation']['type_errors']) or '无'}",
                f"- 无效引用：{', '.join(trace['missing_chunk_ids']) or '无'}",
                f"- Claim 支撑：{json.dumps(trace['claim_traces'], ensure_ascii=False)[:800]}",
                "",
            ]
        )
    if not bad_cases:
        lines.append("未发现结构或引用一致性错误。")

    lines.extend(
        [
            "## 结论",
            "",
            "- 证据链包装模块已能统一输出 `resolved_citations`、`missing_chunk_ids`、`claim_traces` 和一致性指标。",
            "- 当前第二人输出没有原生 `claim_evidence_map` 和 `insufficient_evidence`，第三人脚本会补齐默认结构用于评估；主系统后续应强制模型原生返回这些字段。",
            "- 如果引用编号全部来自构造的 `evidence_1` 等 evidence chunk，则引用存在性可以验证；真实主系统接入时应改用实际 `chunkId` 并保留 page/bbox 定位信息。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    second_report = load_json(SECOND_REPORT)
    testset_path = find_testset_path(second_report)
    case_map = build_case_map(load_json(testset_path))
    rows = second_report.get("rows") if isinstance(second_report.get("rows"), list) else []
    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        case_id = str(row.get("case_id") or "")
        case = case_map.get(case_id)
        if not case:
            continue
        payload = enforce_structured_payload(row)
        trace = build_evidence_trace(payload, chunk_context_from_case(case))
        results.append(
            {
                "case_id": case_id,
                "mode": row.get("mode"),
                "task_type": row.get("task_type"),
                "question": row.get("question"),
                "answer": row.get("answer"),
                "trace": trace,
            }
        )

    summary = summarize(results)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generatedAt": datetime.now().isoformat(),
        "sourceReport": str(SECOND_REPORT),
        "testset": str(testset_path),
        "summary": summary,
        "results": results,
    }
    (OUT_DIR / "evidence_trace_eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "evidence_trace_eval_report.md").write_text(render_md(summary, results), encoding="utf-8-sig")
    print(f"Wrote {OUT_DIR / 'evidence_trace_eval_report.md'}")


if __name__ == "__main__":
    main()
