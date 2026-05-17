from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_QASPER_PATH = ROOT / "test" / "Qasper_after" / "validation.json"
DEFAULT_OUT_DIR = ROOT / "test" / "8-lad_rag_test" / "data"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_id(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("_") or "item"


def read_qasper(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("papers"), list):
        raise ValueError(f"Qasper_after split JSON expected: {path}")
    return data


def infer_category(question: str, evidence_count: int) -> str:
    q = question.lower()
    if evidence_count > 1:
        return "multi_evidence"
    if any(token in q for token in ("compare", "difference", "better", "worse", "versus")):
        return "comparison"
    if any(token in q for token in ("how", "method", "approach", "procedure")):
        return "method"
    if any(token in q for token in ("result", "performance", "score", "metric")):
        return "result"
    if any(token in q for token in ("dataset", "data", "corpus")):
        return "dataset"
    return "fact"


def build_section_nodes(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    section_to_id: Dict[str, str] = {}
    sections: List[Dict[str, Any]] = []
    for chunk in chunks:
        section_name = clean_text(chunk.get("section_name") or "Document")
        if section_name in section_to_id:
            continue
        section_id = f"sec_{len(sections):04d}"
        section_to_id[section_name] = section_id
        parts = [part.strip() for part in section_name.split(":::") if part.strip()]
        sections.append(
            {
                "sectionId": section_id,
                "title": parts[-1] if parts else section_name,
                "level": max(1, min(len(parts), 6)),
                "isAttachedSubheading": False,
                "structureRole": "formal_section",
                "headingConfidence": 1.0,
                "headingPattern": "qasper_section_name",
                "chunkId": "",
                "pageNo": 0,
                "globalIndex": len(sections),
                "parentId": None,
                "path": parts or [section_name],
            }
        )
    return sections, section_to_id


def build_lad_doc(paper: Dict[str, Any]) -> Dict[str, Any]:
    paper_id = safe_id(paper.get("paper_id"))
    raw_chunks = paper.get("chunks") if isinstance(paper.get("chunks"), list) else []
    sections, section_to_id = build_section_nodes(raw_chunks)
    enhanced: List[Dict[str, Any]] = []
    by_section_count: Dict[str, int] = {}

    for global_index, raw in enumerate(raw_chunks):
        if not isinstance(raw, dict):
            continue
        section_name = clean_text(raw.get("section_name") or "Document")
        section_id = section_to_id.get(section_name) or "sec_0000"
        section = next((item for item in sections if item["sectionId"] == section_id), None)
        section_path = section.get("path") if isinstance(section, dict) else [section_name]
        chunk_id = f"{paper_id}_{safe_id(raw.get('chunk_id'))}"
        by_section_count[section_id] = int(by_section_count.get(section_id, 0)) + 1
        enhanced.append(
            {
                "chunkId": chunk_id,
                "chunkKey": chunk_id,
                "sourceChunkId": str(raw.get("chunk_id") or ""),
                "docId": paper_id,
                "docName": clean_text(paper.get("title") or paper_id),
                "pageNo": 0,
                "index": int(raw.get("paragraph_index") or 0),
                "globalIndex": global_index,
                "label": "paragraph",
                "blockType": "paragraph",
                "content": clean_text(raw.get("text") or ""),
                "normalizedContent": clean_text(raw.get("text") or ""),
                "cleanText": clean_text(raw.get("text") or ""),
                "charCount": len(clean_text(raw.get("text") or "")),
                "sectionId": section_id,
                "sectionTitle": section_path[-1] if section_path else section_name,
                "sectionLevel": len(section_path) if section_path else 1,
                "sectionPath": section_path,
                "sectionPathText": " > ".join(section_path),
                "isHeading": False,
                "headingLevel": None,
                "headingText": "",
                "headingConfidence": 0.0,
                "headingPattern": "qasper_paragraph",
                "structureRole": "paragraph",
            }
        )

    for idx, chunk in enumerate(enhanced):
        chunk["prevGlobalChunkId"] = enhanced[idx - 1]["chunkId"] if idx > 0 else None
        chunk["nextGlobalChunkId"] = enhanced[idx + 1]["chunkId"] if idx + 1 < len(enhanced) else None

    by_section: Dict[str, List[Dict[str, Any]]] = {}
    for chunk in enhanced:
        by_section.setdefault(str(chunk.get("sectionId") or ""), []).append(chunk)
    for chunks in by_section.values():
        chunks.sort(key=lambda item: int(item.get("globalIndex") or 0))
        for idx, chunk in enumerate(chunks):
            chunk["prevSamePageChunkId"] = chunks[idx - 1]["chunkId"] if idx > 0 else None
            chunk["nextSamePageChunkId"] = chunks[idx + 1]["chunkId"] if idx + 1 < len(chunks) else None

    for section in sections:
        sid = section["sectionId"]
        first_chunk = by_section.get(sid, [None])[0]
        if isinstance(first_chunk, dict):
            section["chunkId"] = first_chunk["chunkId"]
            section["globalIndex"] = first_chunk["globalIndex"]

    return {
        "status": "ready",
        "source": "Qasper_after",
        "generatedAt": utc_now(),
        "docId": paper_id,
        "docName": clean_text(paper.get("title") or paper_id),
        "abstract": clean_text(paper.get("abstract") or ""),
        "profile": "en",
        "pageCount": 0,
        "totalChunks": len(enhanced),
        "structure": {
            "sectionCount": len(sections),
            "headingStats": {"qasper_section": len(sections)},
            "sections": sections,
        },
        "pages": [
            {
                "pageNo": 0,
                "chunkCount": len(enhanced),
                "imageSize": {},
                "chunks": enhanced,
            }
        ],
        "chunks": enhanced,
    }


def map_evidence_ids(paper_id: str, evidence_ids: List[str]) -> List[str]:
    prefix = safe_id(paper_id)
    return [f"{prefix}_{safe_id(cid)}" for cid in evidence_ids if str(cid).strip()]


def first_gold_answer(q: Dict[str, Any]) -> str:
    answers = q.get("gold_answers") if isinstance(q.get("gold_answers"), list) else []
    for answer in answers:
        text = clean_text(answer)
        if text and text.lower() != clean_text(q.get("question")).lower():
            return text
    for answer in answers:
        text = clean_text(answer)
        if text:
            return text
    return ""


def build_test_cases(papers: List[Dict[str, Any]], lad_docs: Dict[str, Dict[str, Any]], *, max_cases: int) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for paper in papers:
        paper_id = safe_id(paper.get("paper_id"))
        lad = lad_docs.get(paper_id)
        if not isinstance(lad, dict):
            continue
        by_source_chunk: Dict[str, Dict[str, Any]] = {
            str(chunk.get("sourceChunkId") or ""): chunk
            for chunk in lad.get("chunks", [])
            if isinstance(chunk, dict)
        }
        qas = paper.get("qas") if isinstance(paper.get("qas"), list) else []
        for q in qas:
            if not isinstance(q, dict) or not q.get("answerable"):
                continue
            question = clean_text(q.get("question"))
            evidence = [str(cid).strip() for cid in (q.get("evidence_chunk_ids") if isinstance(q.get("evidence_chunk_ids"), list) else []) if str(cid).strip()]
            if not question or not evidence:
                continue
            evidence_chunk_ids = map_evidence_ids(paper_id, evidence)
            evidence_section_ids = []
            for source_cid in evidence:
                chunk = by_source_chunk.get(source_cid)
                sid = str(chunk.get("sectionId") or "").strip() if isinstance(chunk, dict) else ""
                if sid and sid not in evidence_section_ids:
                    evidence_section_ids.append(sid)
            gold = first_gold_answer(q)
            if not gold:
                continue
            cases.append(
                {
                    "id": f"qasper_{len(cases)+1:04d}",
                    "dataset": "qasper",
                    "doc_id": paper_id,
                    "paper_id": paper_id,
                    "paper_title": clean_text(paper.get("title")),
                    "question_id": str(q.get("question_id") or ""),
                    "category": infer_category(question, len(evidence_chunk_ids)),
                    "difficulty": "cross_section" if len(evidence_section_ids) > 1 else "single_section",
                    "question": question,
                    "gold_answer": gold,
                    "gold_answers": q.get("gold_answers") if isinstance(q.get("gold_answers"), list) else [gold],
                    "evidence_chunk_ids": evidence_chunk_ids,
                    "evidence_section_ids": evidence_section_ids,
                    "evidence_texts": q.get("evidence_texts") if isinstance(q.get("evidence_texts"), list) else [],
                }
            )
            if len(cases) >= max_cases:
                return cases
    return cases


def build_corpus_manifest(lad_docs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for doc_id, lad in lad_docs.items():
        for chunk in lad.get("chunks") if isinstance(lad.get("chunks"), list) else []:
            if not isinstance(chunk, dict):
                continue
            items.append(
                {
                    "chunkId": chunk.get("chunkId"),
                    "docId": doc_id,
                    "docName": lad.get("docName"),
                    "pageNo": chunk.get("pageNo", 0),
                    "index": len(items),
                    "label": "paragraph",
                    "content": chunk.get("content"),
                    "normalizedContent": chunk.get("normalizedContent"),
                    "charCount": chunk.get("charCount"),
                    "sourceChunkIds": [chunk.get("chunkId")],
                    "sourcePageNos": [0],
                    "sourceChunkCount": 1,
                    "sourceSectionIds": [chunk.get("sectionId")] if chunk.get("sectionId") else [],
                    "sourceSectionPathTexts": [chunk.get("sectionPathText")] if chunk.get("sectionPathText") else [],
                    "sourceBlockTypes": [chunk.get("blockType") or "paragraph"],
                    "headingText": chunk.get("headingText") or chunk.get("sectionTitle") or "",
                    "sectionId": chunk.get("sectionId") or "",
                    "sectionPathText": chunk.get("sectionPathText") or "",
                    "blockType": chunk.get("blockType") or "paragraph",
                }
            )
    return {
        "status": "ready",
        "source": "qasper_lad_manifest",
        "docCount": len(lad_docs),
        "chunkCount": len(items),
        "documents": sorted(lad_docs.keys()),
        "updatedAt": utc_now(),
        "items": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build LAD-like structure index and retrieval testset from Qasper_after JSON.")
    parser.add_argument("--input", type=Path, default=DEFAULT_QASPER_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--max-papers", type=int, default=20)
    parser.add_argument("--max-cases", type=int, default=120)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = read_qasper(args.input)
    papers = [paper for paper in data.get("papers", []) if isinstance(paper, dict)][: max(1, int(args.max_papers))]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = args.output_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    lad_docs: Dict[str, Dict[str, Any]] = {}
    for paper in papers:
        lad = build_lad_doc(paper)
        doc_id = str(lad.get("docId") or "")
        lad_docs[doc_id] = lad
        doc_dir = docs_dir / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        (doc_dir / "lad_chunk.json").write_text(json.dumps(lad, ensure_ascii=False, indent=2), encoding="utf-8")

    corpus = {
        "status": "ready",
        "source": str(args.input),
        "split": data.get("split"),
        "generatedAt": utc_now(),
        "docCount": len(lad_docs),
        "docs": list(lad_docs.values()),
    }
    testset = {
        "status": "ready",
        "source": str(args.input),
        "generatedAt": utc_now(),
        "caseCount": 0,
        "items": build_test_cases(papers, lad_docs, max_cases=max(1, int(args.max_cases))),
    }
    testset["caseCount"] = len(testset["items"])
    manifest = build_corpus_manifest(lad_docs)

    (args.output_dir / "qasper_lad_corpus.json").write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "qasper_lad_testset.json").write_text(json.dumps(testset, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.output_dir / "qasper_lad_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.output_dir / 'qasper_lad_corpus.json'}")
    print(f"Wrote {args.output_dir / 'qasper_lad_testset.json'}")
    print(f"Wrote {args.output_dir / 'qasper_lad_manifest.json'}")
    print(f"docs={len(lad_docs)} cases={testset['caseCount']} manifest_items={len(manifest['items'])}")


if __name__ == "__main__":
    main()
