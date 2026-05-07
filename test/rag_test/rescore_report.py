from __future__ import annotations

import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_DOC_DIR = ROOT / "data" / "projects" / "6cf73d20-55fb-43c6-987e-efc088417ca9" / "documents" / "pdf_7f3c742d"
SRC_PATH = ROOT / "rag_eval_report.partial.json"
TESTSET_PATH = ROOT / "test" / "rag_test" / "testset.json"
OUT_JSON = ROOT / "test" / "rag_test" / "rag_eval_report.json"
OUT_MD = ROOT / "test" / "rag_test" / "rag_eval_report.md"
MAX_SAMPLE_QUESTIONS = 10
# 默认只评估三个最优 chunk 策略下的三个 top_k 组合。
# 如需调整，直接修改这里的列表即可。
TARGET_STRATEGIES = ["rag_500_100", "rag_800_100", "rag_1000_100"]
TARGET_TOP_KS = [1, 3, 5]


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？；：、,.!?;:]", "", text)
    return text


def extract_keywords(item: Dict[str, Any]) -> List[str]:
    kws = item.get("expected_keywords") or item.get("keywords") or []
    if isinstance(kws, list):
        return [str(k).strip() for k in kws if str(k).strip()]
    return []


def extract_number_tokens(text: str) -> List[str]:
    raw = str(text or "")
    return re.findall(r"\d+(?:\.\d+)?%?|[一二三四五六七八九十百千万]+", raw)


def normalize_for_similarity(text: str) -> str:
    text = normalize_text(text)
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text)


def similarity_score(a: str, b: str) -> float:
    na = normalize_for_similarity(a)
    nb = normalize_for_similarity(b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    return round(SequenceMatcher(None, na, nb).ratio(), 4)


def split_into_sentences(text: str) -> List[str]:
    parts = re.split(r"[。！？!?;；\n]+", str(text or ""))
    return [p.strip() for p in parts if p.strip()]


def canonical_facts_from_gold(gold_answer: str, question: str) -> List[str]:
    facts: List[str] = []
    numbers = extract_number_tokens(gold_answer)
    facts.extend(numbers[:8])
    q = str(question or "")
    if any(token in q for token in ["是什么", "谁", "哪些", "多少", "第几", "哪四个", "哪三个", "目标", "指标", "计划", "模块", "流程"]):
        facts.extend([t for t in re.split(r"[，。；：、\s]+", gold_answer) if len(t.strip()) >= 2][:10])
    # 退化为金标答案的关键句，避免事实集为空导致过度依赖相似度。
    if not facts:
        facts.extend(split_into_sentences(gold_answer)[:3])
    normalized: List[str] = []
    seen = set()
    for fact in facts:
        nf = normalize_text(fact)
        if nf and nf not in seen:
            seen.add(nf)
            normalized.append(nf)
    return normalized


def chunk_hits_text(text: str, facts: List[str]) -> int:
    if not text or not facts:
        return 0
    return sum(1 for fact in facts if fact and fact in text)


def build_cited_text(item: Dict[str, Any], chunk_text_map: Dict[str, str]) -> str:
    cited_ids = item.get("cited_chunk_ids") or []
    if not isinstance(cited_ids, list):
        cited_ids = []
    texts = []
    for cid in cited_ids:
        text = chunk_text_map.get(str(cid), "")
        if text:
            texts.append(text)
    return normalize_text("\n".join(texts))


def score_item(item: Dict[str, Any], chunk_text_map: Dict[str, str]) -> Dict[str, Any]:
    answer_raw = str(item.get("answer") or "").strip()
    answer = normalize_text(answer_raw)
    gold_answer = str(item.get("gold_answer") or "")
    gold = normalize_text(gold_answer)

    answer_similarity = similarity_score(answer_raw, gold_answer)
    facts = canonical_facts_from_gold(gold_answer, str(item.get("question") or ""))

    cited_text = build_cited_text(item, chunk_text_map)
    answer_hit_count = chunk_hits_text(answer, facts)
    cited_hit_count = chunk_hits_text(cited_text, facts)

    if facts:
        answer_support = answer_hit_count / len(facts)
        cited_support = cited_hit_count / len(facts)
        # 如果答案本身已经覆盖了关键事实，但引用块较弱，则 groundedness 不能过低。
        key_fact_f1 = round(answer_support, 4)
        groundedness = round(min(1.0, max(cited_support, answer_support * 0.7)), 4)
    else:
        # 无法抽出事实时，回退到语义相似度。
        key_fact_f1 = answer_similarity
        groundedness = answer_similarity if cited_text else 0.0

    answer_chunk_hit = 1 if (item.get("cited_chunk_ids") and cited_text) else 0
    exact_match = answer == gold and bool(answer)
    return {
        **item,
        "exact_match": exact_match,
        "answer_chunk_hit": answer_chunk_hit,
        "answer_similarity": answer_similarity,
        "key_fact_f1": key_fact_f1,
        "groundedness": groundedness,
    }


def summarize(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
    for item in results:
        groups[(str(item.get("strategy")), int(item.get("top_k") or 0))].append(item)

    summary: List[Dict[str, Any]] = []
    for strategy in TARGET_STRATEGIES:
        for top_k in TARGET_TOP_KS:
            items = groups.get((strategy, top_k), [])
            total = len(items)
            summary.append(
                {
                    "strategy": strategy,
                    "top_k": top_k,
                    "total": total,
                    "answer_chunk_hit_rate": round(sum(float(x.get("answer_chunk_hit") or 0) for x in items) / max(total, 1), 4),
                    "avg_answer_similarity": round(sum(float(x.get("answer_similarity") or 0) for x in items) / max(total, 1), 4),
                    "avg_key_fact_f1": round(sum(float(x.get("key_fact_f1") or 0) for x in items) / max(total, 1), 4),
                    "avg_groundedness": round(sum(float(x.get("groundedness") or 0) for x in items) / max(total, 1), 4),
                    "avg_retrieved": round(sum(int(x.get("retrieved_count") or 0) for x in items) / max(total, 1), 2),
                }
            )
    return summary


def render_md(summary: List[Dict[str, Any]], results: List[Dict[str, Any]]) -> str:
    lines = [
        "# RAG 评估报告",
        "",
        f"- 源文件：{SRC_PATH.name}",
        f"- 测试集：{TESTSET_PATH.name}",
        f"- 生成时间：{__import__('datetime').datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        "## 汇总",
        "",
        "| Strategy | TOPK | Total | Answer Chunk Hit | Answer Similarity | Key Fact F1 | Groundedness | Avg Retrieved |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['strategy']} | {s['top_k']} | {s['total']} | {s['answer_chunk_hit_rate']:.4f} | {s['avg_answer_similarity']:.4f} | {s['avg_key_fact_f1']:.4f} | {s['avg_groundedness']:.4f} | {s['avg_retrieved']:.2f} |"
        )
    lines += ["", "## 样本", ""]
    for item in results[:20]:
        lines += [
            f"### {item.get('test_id')} | {item.get('strategy')} | top_k={item.get('top_k')}",
            f"- 问题：{item.get('question')}",
            f"- 标准答案：{item.get('gold_answer')}",
            f"- 模型答案：{item.get('answer')}",
            f"- Answer Chunk Hit：{item.get('answer_chunk_hit')} | Similarity：{item.get('answer_similarity')} | Key Fact F1：{item.get('key_fact_f1')} | Groundedness：{item.get('groundedness')}",
            f"- cited_chunk_ids：{', '.join(item.get('cited_chunk_ids') or []) if item.get('cited_chunk_ids') else '无'}",
            "",
        ]
    return "\n".join(lines)


def load_project_chunk_text_map() -> Dict[str, str]:
    chunk_text_map: Dict[str, str] = {}
    if not PROJECT_DOC_DIR.is_dir():
        return chunk_text_map
    for path in PROJECT_DOC_DIR.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if path.name == "chunks.json" and isinstance(data, dict):
            pages = data.get("pages") if isinstance(data.get("pages"), list) else []
            for page in pages:
                if not isinstance(page, dict):
                    continue
                for chunk in page.get("chunks") if isinstance(page.get("chunks"), list) else []:
                    if not isinstance(chunk, dict):
                        continue
                    cid = str(chunk.get("chunkId") or chunk.get("chunkKey") or "").strip()
                    content = str(chunk.get("content") or chunk.get("normalizedContent") or "")
                    if cid and content:
                        chunk_text_map[cid] = content
        elif isinstance(data, dict):
            pages = data.get("pages") if isinstance(data.get("pages"), list) else data.get("ocrBlocksByPage") if isinstance(data.get("ocrBlocksByPage"), list) else []
            for page in pages:
                if not isinstance(page, dict):
                    continue
                chunks = page.get("chunks") if isinstance(page.get("chunks"), list) else []
                for chunk in chunks:
                    if not isinstance(chunk, dict):
                        continue
                    cid = str(chunk.get("chunkId") or chunk.get("chunkKey") or "").strip()
                    content = str(chunk.get("content") or chunk.get("normalizedContent") or "")
                    if cid and content:
                        chunk_text_map[cid] = content
    return chunk_text_map


def main() -> None:
    payload = json.loads(SRC_PATH.read_text(encoding="utf-8"))
    chunk_text_map = load_project_chunk_text_map()
    results_all = [score_item(item, chunk_text_map) for item in payload.get("results", []) if isinstance(item, dict)]
    filtered = [
        item
        for item in results_all
        if str(item.get("strategy") or "") in TARGET_STRATEGIES and int(item.get("top_k") or 0) in TARGET_TOP_KS
    ]
    results = filtered[:MAX_SAMPLE_QUESTIONS]
    summary = summarize(results)
    OUT_JSON.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_md(summary, results), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
