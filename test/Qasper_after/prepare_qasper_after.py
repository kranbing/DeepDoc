from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence

from datasets import load_from_disk

ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_DIR = ROOT / "test" / "Qasper"
OUTPUT_DIR = ROOT / "test" / "Qasper_after"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_OUT = OUTPUT_DIR / "train.json"
VALIDATION_OUT = OUTPUT_DIR / "validation.json"
TEST_OUT = OUTPUT_DIR / "test.json"
META_OUT = OUTPUT_DIR / "meta.json"


def clean_text(text: str) -> str:
    text = str(text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(full_text: Any) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    if not isinstance(full_text, dict):
        return chunks

    section_names = full_text.get("section_name") if isinstance(full_text.get("section_name"), list) else []
    paragraphs_by_section = full_text.get("paragraphs") if isinstance(full_text.get("paragraphs"), list) else []
    section_count = max(len(section_names), len(paragraphs_by_section))

    for sec_idx in range(section_count):
        section_name = clean_text(section_names[sec_idx] if sec_idx < len(section_names) else "")
        paragraphs = paragraphs_by_section[sec_idx] if sec_idx < len(paragraphs_by_section) else []
        if not isinstance(paragraphs, list):
            continue
        for para_idx, paragraph in enumerate(paragraphs):
            text = clean_text(paragraph)
            if not text:
                continue
            chunk_id = f"s{sec_idx:03d}_p{para_idx:03d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "section_name": section_name,
                    "paragraph_index": para_idx,
                    "text": text,
                }
            )
    return chunks


def normalize_answer_item(answer: Dict[str, Any]) -> Dict[str, Any]:
    ans = answer.get("answer") if isinstance(answer, dict) else {}
    return {
        "annotation_id": str(answer.get("annotation_id") or ""),
        "worker_id": str(answer.get("worker_id") or ""),
        "unanswerable": bool(ans.get("unanswerable")),
        "yes_no": bool(ans.get("yes_no")),
        "free_form_answer": clean_text(ans.get("free_form_answer") or ""),
        "extractive_spans": [clean_text(x) for x in (ans.get("extractive_spans") if isinstance(ans.get("extractive_spans"), list) else []) if clean_text(x)],
        "evidence": [clean_text(x) for x in (ans.get("evidence") if isinstance(ans.get("evidence"), list) else []) if clean_text(x)],
        "highlighted_evidence": [clean_text(x) for x in (ans.get("highlighted_evidence") if isinstance(ans.get("highlighted_evidence"), list) else []) if clean_text(x)],
    }


def normalize_qas(qas: Any, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chunk_text_map = {c["chunk_id"]: c["text"] for c in chunks}
    normalized: List[Dict[str, Any]] = []
    if not isinstance(qas, dict):
        return normalized

    questions = qas.get("question") if isinstance(qas.get("question"), list) else []
    question_ids = qas.get("question_id") if isinstance(qas.get("question_id"), list) else []
    question_writers = qas.get("question_writer") if isinstance(qas.get("question_writer"), list) else []
    topic_backgrounds = qas.get("topic_background") if isinstance(qas.get("topic_background"), list) else []
    nlp_backgrounds = qas.get("nlp_background") if isinstance(qas.get("nlp_background"), list) else []
    paper_reads = qas.get("paper_read") if isinstance(qas.get("paper_read"), list) else []
    search_queries = qas.get("search_query") if isinstance(qas.get("search_query"), list) else []
    answers_by_question = qas.get("answers") if isinstance(qas.get("answers"), list) else []

    total = max(
        len(questions),
        len(question_ids),
        len(question_writers),
        len(topic_backgrounds),
        len(nlp_backgrounds),
        len(paper_reads),
        len(search_queries),
        len(answers_by_question),
    )

    for q_idx in range(total):
        answers = answers_by_question[q_idx] if q_idx < len(answers_by_question) else {}
        if not isinstance(answers, dict):
            answers = {}
        answer_items: List[Dict[str, Any]] = []
        answer_payloads = answers.get("answer") if isinstance(answers.get("answer"), list) else []
        annotation_ids = answers.get("annotation_id") if isinstance(answers.get("annotation_id"), list) else []
        worker_ids = answers.get("worker_id") if isinstance(answers.get("worker_id"), list) else []
        answer_total = max(len(answer_payloads), len(annotation_ids), len(worker_ids))
        for ans_idx in range(answer_total):
            answer_payload = answer_payloads[ans_idx] if ans_idx < len(answer_payloads) else {}
            if not isinstance(answer_payload, dict):
                answer_payload = {}
            answer_items.append(
                normalize_answer_item(
                    {
                        "annotation_id": annotation_ids[ans_idx] if ans_idx < len(annotation_ids) else "",
                        "worker_id": worker_ids[ans_idx] if ans_idx < len(worker_ids) else "",
                        "answer": answer_payload,
                    }
                )
            )

        evidence_texts: List[str] = []
        for answer in answer_items:
            if not isinstance(answer, dict):
                continue
            for ev in (answer.get("evidence") if isinstance(answer.get("evidence"), list) else []):
                ev_text = clean_text(ev)
                if ev_text:
                    evidence_texts.append(ev_text)
            for hev in (answer.get("highlighted_evidence") if isinstance(answer.get("highlighted_evidence"), list) else []):
                hev_text = clean_text(hev)
                if hev_text:
                    evidence_texts.append(hev_text)

        evidence_chunk_ids: List[str] = []
        if evidence_texts:
            for chunk in chunks:
                if any(ev and ev in chunk["text"] for ev in evidence_texts):
                    evidence_chunk_ids.append(chunk["chunk_id"])
        evidence_chunk_ids = list(dict.fromkeys(evidence_chunk_ids))

        gold_answers = [clean_text(a.get("free_form_answer", "")) for a in answer_items if isinstance(a, dict)]
        gold_answers = [x for x in gold_answers if x]
        if not gold_answers:
            gold_answers = [clean_text(questions[q_idx] if q_idx < len(questions) else "")]

        normalized.append(
            {
                "question_id": str(question_ids[q_idx] if q_idx < len(question_ids) else f"q{q_idx:04d}"),
                "question": clean_text(questions[q_idx] if q_idx < len(questions) else ""),
                "question_writer": clean_text(question_writers[q_idx] if q_idx < len(question_writers) else ""),
                "topic_background": clean_text(topic_backgrounds[q_idx] if q_idx < len(topic_backgrounds) else ""),
                "nlp_background": clean_text(nlp_backgrounds[q_idx] if q_idx < len(nlp_backgrounds) else ""),
                "paper_read": clean_text(paper_reads[q_idx] if q_idx < len(paper_reads) else ""),
                "search_query": clean_text(search_queries[q_idx] if q_idx < len(search_queries) else ""),
                "answers": answer_items,
                "gold_answers": gold_answers,
                "evidence_chunk_ids": evidence_chunk_ids,
                "evidence_texts": evidence_texts[:20],
                "answerable": not all(a.get("unanswerable") for a in answer_items if isinstance(a, dict)) if answer_items else True,
            }
        )
    return normalized


def convert_split(split_name: str, dataset) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    for idx, row in enumerate(dataset):
        if not isinstance(row, dict):
            continue
        chunks = split_paragraphs(row.get("full_text") or [])
        qas = normalize_qas(row.get("qas") or [], chunks)
        records.append(
            {
                "paper_id": str(row.get("id") or ""),
                "title": clean_text(row.get("title") or ""),
                "abstract": clean_text(row.get("abstract") or ""),
                "full_text": row.get("full_text") or [],
                "chunks": chunks,
                "qas": qas,
                "figures_and_tables": row.get("figures_and_tables") or [],
                "source_split": split_name,
            }
        )
    return {
        "split": split_name,
        "num_papers": len(records),
        "papers": records,
    }


def main() -> None:
    ds = load_from_disk(str(INPUT_DIR))
    outputs = {}
    for split_name in ["train", "validation", "test"]:
        if split_name not in ds:
            continue
        outputs[split_name] = convert_split(split_name, ds[split_name])

    META_OUT.write_text(
        json.dumps(
            {
                "source": str(INPUT_DIR),
                "generated_from": "allenai/qasper",
                "splits": list(outputs.keys()),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if "train" in outputs:
        TRAIN_OUT.write_text(json.dumps(outputs["train"], ensure_ascii=False, indent=2), encoding="utf-8")
    if "validation" in outputs:
        VALIDATION_OUT.write_text(json.dumps(outputs["validation"], ensure_ascii=False, indent=2), encoding="utf-8")
    if "test" in outputs:
        TEST_OUT.write_text(json.dumps(outputs["test"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {META_OUT}")
    for name, path in [("train", TRAIN_OUT), ("validation", VALIDATION_OUT), ("test", TEST_OUT)]:
        if name in outputs:
            print(f"Wrote {path}")


if __name__ == "__main__":
    main()
