from __future__ import annotations

from backend.services.evidence_trace import build_evidence_trace, validate_structured_payload


def test_validate_structured_payload_ok() -> None:
    payload = {
        "answer": "A uses B.",
        "cited_chunk_ids": ["c1"],
        "claim_evidence_map": {"A uses B.": ["c1"]},
        "insufficient_evidence": False,
        "follow_up_questions": [],
    }
    result = validate_structured_payload(payload)
    assert result["valid"] is True
    assert result["missing_keys"] == []


def test_build_evidence_trace_missing_and_existing() -> None:
    payload = {
        "answer": "The model uses cross-lingual pretraining.",
        "cited_chunk_ids": ["c1", "missing"],
        "claim_evidence_map": {"model uses cross-lingual pretraining": ["c1", "missing"]},
        "insufficient_evidence": False,
        "follow_up_questions": [],
    }
    context = {
        "currentChunks": [
            {
                "chunkId": "c1",
                "pageNo": 2,
                "index": 1,
                "bboxPx": {"x1": 0, "y1": 10, "x2": 100, "y2": 50},
                "sectionPathText": "Approach",
                "content": "The model uses cross-lingual pretraining for transfer.",
            }
        ],
        "neighborChunks": [],
        "retrievalChunks": [],
    }
    trace = build_evidence_trace(payload, context)
    assert trace["consistency"]["citation_exist_rate"] == 0.5
    assert trace["missing_chunk_ids"] == ["missing"]
    assert trace["claim_traces"][0]["support_score"] > 0
    assert trace["resolved_citations"][0]["page_no"] == 2
