from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


TASK_TYPES = {
    "fact_qa",
    "local_evidence_qa",
    "multi_evidence_qa",
    "method_qa",
    "comparison_qa",
    "dataset_qa",
}


@dataclass(frozen=True)
class TaskRoute:
    task_type: str
    retrieval_mode: str
    prompt_template: str
    system_prompt: str
    response_contract: str
    output_schema: Dict[str, Any]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


SYSTEM_PROMPT_BASE = (
    "You are a document QA assistant. Answer only from provided chunks, document overview, "
    "and conversation context. Do not invent facts. Return exactly one JSON object."
)


PROMPT_TEMPLATES: Dict[str, str] = {
    "fact_qa": (
        "Answer the factual question using only the provided chunks. "
        "Keep the answer concise. Cite chunk ids that directly support the factual claim. "
        "If no chunk directly supports the answer, say the evidence is insufficient."
    ),
    "local_evidence_qa": (
        "Use only the local chunk neighborhood. Verify every claim against the cited chunks. "
        "If the local chunks only partially support the answer, answer the supported part and state what evidence is missing."
    ),
    "multi_evidence_qa": (
        "Synthesize the answer across all relevant retrieved chunks. "
        "Map each major claim to supporting chunk ids. Do not fill gaps with outside knowledge."
    ),
    "method_qa": (
        "Answer method, model, system, training, or experiment questions from the retrieved chunks. "
        "Separate the paper's proposed method from background or related work when possible."
    ),
    "comparison_qa": (
        "Compare only items supported by retrieved chunks. "
        "State the comparison basis and cite evidence for each compared item. Mark missing sides explicitly."
    ),
    "dataset_qa": (
        "Answer dataset, benchmark, split, language, metric, or evaluation-data questions from retrieved chunks. "
        "Include dataset attributes only when cited chunks directly support them."
    ),
}


OUTPUT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "fact_qa": {
        "type": "object",
        "required": ["cited_chunk_ids", "answer", "follow_up_questions", "insufficient_evidence"],
        "properties": {
            "cited_chunk_ids": {"type": "array", "items": {"type": "string"}},
            "answer": {"type": "string"},
            "follow_up_questions": {"type": "array", "items": {"type": "string"}},
            "insufficient_evidence": {"type": "boolean"},
        },
    },
    "local_evidence_qa": {
        "type": "object",
        "required": ["cited_chunk_ids", "answer", "follow_up_questions", "evidence_check", "insufficient_evidence"],
        "properties": {
            "cited_chunk_ids": {"type": "array", "items": {"type": "string"}},
            "answer": {"type": "string"},
            "follow_up_questions": {"type": "array", "items": {"type": "string"}},
            "evidence_check": {"type": "string"},
            "insufficient_evidence": {"type": "boolean"},
        },
    },
    "multi_evidence_qa": {
        "type": "object",
        "required": ["cited_chunk_ids", "answer", "follow_up_questions", "claim_evidence_map", "insufficient_evidence"],
        "properties": {
            "cited_chunk_ids": {"type": "array", "items": {"type": "string"}},
            "answer": {"type": "string"},
            "follow_up_questions": {"type": "array", "items": {"type": "string"}},
            "claim_evidence_map": {"type": "object"},
            "insufficient_evidence": {"type": "boolean"},
        },
    },
    "method_qa": {
        "type": "object",
        "required": ["cited_chunk_ids", "answer", "follow_up_questions", "proposed_method", "experimental_settings", "insufficient_evidence"],
        "properties": {
            "cited_chunk_ids": {"type": "array", "items": {"type": "string"}},
            "answer": {"type": "string"},
            "follow_up_questions": {"type": "array", "items": {"type": "string"}},
            "proposed_method": {"type": "string"},
            "experimental_settings": {"type": "string"},
            "insufficient_evidence": {"type": "boolean"},
        },
    },
    "comparison_qa": {
        "type": "object",
        "required": ["cited_chunk_ids", "answer", "follow_up_questions", "compared_items", "comparison_basis", "insufficient_evidence"],
        "properties": {
            "cited_chunk_ids": {"type": "array", "items": {"type": "string"}},
            "answer": {"type": "string"},
            "follow_up_questions": {"type": "array", "items": {"type": "string"}},
            "compared_items": {"type": "array", "items": {"type": "string"}},
            "comparison_basis": {"type": "string"},
            "insufficient_evidence": {"type": "boolean"},
        },
    },
    "dataset_qa": {
        "type": "object",
        "required": ["cited_chunk_ids", "answer", "follow_up_questions", "dataset_names", "verified_attributes", "insufficient_evidence"],
        "properties": {
            "cited_chunk_ids": {"type": "array", "items": {"type": "string"}},
            "answer": {"type": "string"},
            "follow_up_questions": {"type": "array", "items": {"type": "string"}},
            "dataset_names": {"type": "array", "items": {"type": "string"}},
            "verified_attributes": {"type": "object"},
            "insufficient_evidence": {"type": "boolean"},
        },
    },
}


FALLBACK_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["cited_chunk_ids", "answer", "follow_up_questions"],
    "properties": {
        "cited_chunk_ids": {"type": "array", "items": {"type": "string"}},
        "answer": {"type": "string"},
        "follow_up_questions": {"type": "array", "items": {"type": "string"}},
    },
}


def response_contract_for_task(task_type: str) -> str:
    schema = OUTPUT_SCHEMAS.get(task_type, FALLBACK_SCHEMA)
    required = ", ".join(schema.get("required") or [])
    return (
        f"Return JSON only. Required keys: {required}. "
        "Only include cited_chunk_ids that appear in the provided chunks. "
        "If evidence is insufficient, set insufficient_evidence=true when that key is required."
    )


def _contains_any(text: str, markers: List[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def _selected_count(selected_items: Optional[List[Dict[str, Any]]]) -> int:
    if not isinstance(selected_items, list):
        return 0
    return sum(1 for item in selected_items if isinstance(item, dict))


def classify_task(question: str, *, selected_items: Optional[List[Dict[str, Any]]] = None) -> str:
    q = str(question or "").strip()
    selected_count = _selected_count(selected_items)

    if selected_count > 0:
        return "local_evidence_qa"

    if _contains_any(
        q,
        [
            "compare",
            "comparison",
            "baseline",
            "better than",
            "versus",
            "vs",
            "different from",
            "区别",
            "对比",
            "比较",
            "优于",
        ],
    ):
        return "comparison_qa"

    if _contains_any(
        q,
        [
            "method",
            "model",
            "approach",
            "architecture",
            "algorithm",
            "training",
            "experiment setup",
            "方法",
            "模型",
            "算法",
            "训练",
            "实验设置",
        ],
    ):
        return "method_qa"

    if _contains_any(
        q,
        [
            "dataset",
            "benchmark",
            "corpus",
            "data set",
            "split",
            "metric",
            "evaluation set",
            "数据集",
            "基准",
            "语料",
            "指标",
        ],
    ):
        return "dataset_qa"

    if _contains_any(q, ["list", "which", "what are", "how many", "哪些", "多少", "列出"]):
        return "multi_evidence_qa"

    if len(re.findall(r"\w+", q)) <= 10:
        return "fact_qa"

    return "multi_evidence_qa"


def default_retrieval_mode(task_type: str) -> str:
    if task_type in {"fact_qa", "local_evidence_qa"}:
        return "lad"
    return "rag"


def dispatch_task(
    question: str,
    *,
    selected_items: Optional[List[Dict[str, Any]]] = None,
    requested_retrieval_mode: Optional[str] = None,
) -> TaskRoute:
    task_type = classify_task(question, selected_items=selected_items)
    requested = str(requested_retrieval_mode or "auto").strip().lower()
    if requested in {"rag", "lad"}:
        retrieval_mode = requested
        reason = f"explicit retrieval mode: {requested}"
    else:
        retrieval_mode = default_retrieval_mode(task_type)
        reason = f"auto dispatch from task_type={task_type}"

    return TaskRoute(
        task_type=task_type,
        retrieval_mode=retrieval_mode,
        prompt_template=PROMPT_TEMPLATES[task_type],
        system_prompt=SYSTEM_PROMPT_BASE,
        response_contract=response_contract_for_task(task_type),
        output_schema=OUTPUT_SCHEMAS.get(task_type, FALLBACK_SCHEMA),
        reason=reason,
    )
