"""
Relation Extractor Module (Member 1)

Extracts relations between entities using:
  1. Co-occurrence analysis (entities in same chunk/section)
  2. Pattern matching (linguistic patterns)
  3. LLM-based classification via DeepSeek API
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib import request as urlrequest

ROOT = Path(__file__).resolve().parent.parent.parent

# Relation patterns: (regex_pattern, relation_type)
RELATION_PATTERNS = [
    (re.compile(r'(\w+)\s+(?:uses?|utilizes?|employs?|leverages?)\s+(\w+)', re.I), "USES"),
    (re.compile(r'(\w+)\s+(?:evaluates?|evaluated|tests?|tested)\s+(?:on|against)\s+(\w+)', re.I), "EVALUATES_ON"),
    (re.compile(r'(\w+)\s+(?:achieves?|achieved|attains?|reaches?)\s+(\w+)', re.I), "ACHIEVES"),
    (re.compile(r'(\w+)\s+(?:based\s+on|builds?\s+(?:on|upon)|extends?|improves?)\s+(\w+)', re.I), "BASED_ON"),
    (re.compile(r'(\w+)\s+(?:proposes?|proposed|introduces?|presents?)\s+(\w+)', re.I), "PROPOSES"),
    (re.compile(r'(\w+)\s+(?:belongs?\s+to|is\s+(?:a|an)\s+kind\s+of|is\s+(?:a|an)\s+type\s+of)\s+(\w+)', re.I), "BELONGS_TO"),
    (re.compile(r'(\w+)\s+(?:depends?\s+on|requires?|needs?)\s+(\w+)', re.I), "DEPENDS_ON"),
    (re.compile(r'(\w+)\s+(?:compares?\s+(?:with|to)|outperforms?|surpasses?|beats?)\s+(\w+)', re.I), "COMPARES_WITH"),
    (re.compile(r'(\w+)\s+(?:contains?|includes?|comprises?|consists?\s+of)\s+(\w+)', re.I), "CONTAINS"),
    (re.compile(r'(\w+)\s+(?:is\s+part\s+of|belongs?\s+to)\s+(\w+)', re.I), "PART_OF"),
]

# Relation keywords for pattern-based extraction
RELATION_KEYWORDS = {
    "USES": ["use", "uses", "utilize", "employ", "leverage", "apply", "adopt"],
    "EVALUATES_ON": ["evaluate", "evaluated", "test", "tested", "benchmark", "assess"],
    "ACHIEVES": ["achieve", "achieved", "attain", "reach", "obtain", "score"],
    "BASED_ON": ["based on", "build on", "extend", "improve", "enhance", "modify", "adapt"],
    "PROPOSES": ["propose", "introduce", "present", "design", "develop", "create"],
    "BELONGS_TO": ["belong", "type of", "kind of", "category", "class"],
    "DEPENDS_ON": ["depend", "require", "need", "rely on", "prerequisite"],
    "COMPARES_WITH": ["compare", "outperform", "surpass", "beat", "exceed", "rival"],
    "CONTAINS": ["contain", "include", "comprise", "consist", "encompass"],
}


def _get_deepseek_api_key() -> Optional[str]:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    key_file = ROOT / "backend" / ".deepseek_api_key"
    if key_file.is_file():
        return key_file.read_text(encoding="utf-8").strip() or None
    return None


def _llm_classify_relation(
    entity_a: str, entity_b: str, context: str, api_key: str = ""
) -> Optional[Dict[str, Any]]:
    """Use LLM to classify relation between two entities."""
    if not api_key:
        api_key = _get_deepseek_api_key()
    if not api_key:
        return None

    system_prompt = (
        "You are a relation classification system. Given two entities and their context, "
        "classify the relation between them. Return JSON with: "
        "'relation' (one of: USES, EVALUATES_ON, ACHIEVES, BASED_ON, PROPOSES, BELONGS_TO, "
        "DEPENDS_ON, COMPARES_WITH, CONTAINS, PART_OF, NONE), "
        "'confidence' (0.0-1.0), 'evidence' (short supporting text, max 80 chars). "
        "Return NONE if no meaningful relation exists. Return ONLY valid JSON."
    )

    user_prompt = f"Entity A: {entity_a}\nEntity B: {entity_b}\nContext: {context[:800]}"

    body = {
        "model": "deepseek-chat",
        "temperature": 0.1,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        req = urlrequest.Request(
            "https://api.deepseek.com/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        message = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        data = json.loads(message) if message.strip().startswith("{") else {}
        relation = data.get("relation", "NONE")
        confidence = float(data.get("confidence", 0))
        evidence = str(data.get("evidence", ""))[:100]

        if relation == "NONE" or confidence < 0.3:
            return None

        return {
            "relation": relation,
            "confidence": confidence,
            "evidence": evidence,
            "source": "llm",
        }
    except Exception as e:
        print(f"[relation_extractor] LLM classification failed: {e}")
        return None


def extract_relations_pattern_based(
    text: str,
    entities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract relations using pattern matching."""
    relations = []
    entity_names = {e["name"].lower(): e for e in entities}

    # Build name lookup with aliases
    name_set: Set[str] = set()
    for e in entities:
        name_set.add(e["name"].lower())

    # Pattern matching on text
    for pattern, rel_type in RELATION_PATTERNS:
        for match in pattern.finditer(text):
            a_text = match.group(1).strip().lower()
            b_text = match.group(2).strip().lower()

            # Match to known entities (fuzzy: substring match)
            a_ent = _find_matching_entity(a_text, entity_names)
            b_ent = _find_matching_entity(b_text, entity_names)

            if a_ent and b_ent and a_ent["id"] != b_ent["id"]:
                relations.append({
                    "source_id": a_ent["id"],
                    "target_id": b_ent["id"],
                    "source_name": a_ent["name"],
                    "target_name": b_ent["name"],
                    "relation": rel_type,
                    "confidence": 0.7,
                    "evidence": match.group(0)[:100],
                    "source": "pattern",
                })

    return relations


def _find_matching_entity(text: str, entity_map: Dict[str, Dict]) -> Optional[Dict]:
    """Find entity matching text (exact or substring)."""
    text_lower = text.lower().strip()
    if text_lower in entity_map:
        return entity_map[text_lower]

    # Substring match
    for name, ent in entity_map.items():
        if name in text_lower or text_lower in name:
            return ent
    return None


def extract_relations_co_occurrence(
    entities: List[Dict[str, Any]],
    chunk_id: str,
    section: str = "",
) -> List[Dict[str, Any]]:
    """Extract relations based on co-occurrence in same chunk/section."""
    relations = []
    # Group by type
    by_type = {}
    for e in entities:
        t = e.get("type", "Concept")
        by_type.setdefault(t, []).append(e)

    # Method -> Dataset (likely EVALUATES_ON)
    for m in by_type.get("Method", []):
        for d in by_type.get("Dataset", []):
            relations.append({
                "source_id": m["id"],
                "target_id": d["id"],
                "source_name": m["name"],
                "target_name": d["name"],
                "relation": "EVALUATES_ON",
                "confidence": 0.5,
                "evidence": f"Co-occurrence in {chunk_id}",
                "source": "co_occurrence",
            })

    # Method -> Metric (likely ACHIEVES)
    for m in by_type.get("Method", []):
        for met in by_type.get("Metric", []):
            relations.append({
                "source_id": m["id"],
                "target_id": met["id"],
                "source_name": m["name"],
                "target_name": met["name"],
                "relation": "ACHIEVES",
                "confidence": 0.4,
                "evidence": f"Co-occurrence in {chunk_id}",
                "source": "co_occurrence",
            })

    # Method -> Method (same section, likely COMPARES_WITH or BASED_ON)
    methods = by_type.get("Method", [])
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            relations.append({
                "source_id": methods[i]["id"],
                "target_id": methods[j]["id"],
                "source_name": methods[i]["name"],
                "target_name": methods[j]["name"],
                "relation": "COMPARES_WITH",
                "confidence": 0.35,
                "evidence": f"Co-occurrence in {chunk_id}",
                "source": "co_occurrence",
            })

    return relations


def extract_relations_from_chunk(
    chunk: Dict[str, Any],
    entities: List[Dict[str, Any]],
    use_llm: bool = True,
    api_key: str = "",
    max_llm_pairs: int = 5,
) -> List[Dict[str, Any]]:
    """Extract relations from a single chunk."""
    text = chunk.get("normalizedContent") or chunk.get("content") or chunk.get("cleanText") or ""
    chunk_id = chunk.get("chunkId", "")
    doc_id = chunk.get("docId", "")
    section = chunk.get("sectionTitle", "")

    if not text.strip() or len(entities) < 2:
        return []

    # 1. Pattern-based
    relations = extract_relations_pattern_based(text, entities)

    # 2. Co-occurrence
    co_relations = extract_relations_co_occurrence(entities, chunk_id, section)
    relations.extend(co_relations)

    # 3. LLM-based (for top entity pairs without existing relations)
    if use_llm:
        covered_pairs = {(r["source_id"], r["target_id"]) for r in relations}
        # Pick entity pairs not yet covered
        pairs = []
        for i, a in enumerate(entities):
            for b in entities[i+1:]:
                if (a["id"], b["id"]) not in covered_pairs and (b["id"], a["id"]) not in covered_pairs:
                    pairs.append((a, b))

        for a, b in pairs[:max_llm_pairs]:
            result = _llm_classify_relation(a["name"], b["name"], text, api_key)
            if result and result["relation"] != "NONE":
                relations.append({
                    "source_id": a["id"],
                    "target_id": b["id"],
                    "source_name": a["name"],
                    "target_name": b["name"],
                    "relation": result["relation"],
                    "confidence": result["confidence"],
                    "evidence": result.get("evidence", ""),
                    "source": "llm",
                })

    # Add metadata
    for r in relations:
        r["source_doc_id"] = doc_id
        r["source_chunk_id"] = chunk_id
        r["source_section"] = section

    return relations


def extract_structural_relations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract CONTAINS relations from document structure (sections, chunks)."""
    relations = []

    # Build section hierarchy from chunk data
    sections_seen = {}
    doc_id = ""

    for chunk in chunks:
        cid = chunk.get("chunkId", "")
        sid = chunk.get("sectionId", "")
        stitle = chunk.get("sectionTitle", "")
        doc_id = chunk.get("docId", "")

        if sid and sid not in sections_seen:
            sections_seen[sid] = {
                "id": f"section_{sid}",
                "name": stitle,
                "type": "Section",
            }

        # Section CONTAINS Chunk
        if sid:
            relations.append({
                "source_id": f"section_{sid}",
                "target_id": f"chunk_{cid}",
                "source_name": stitle,
                "target_name": cid,
                "relation": "CONTAINS",
                "confidence": 1.0,
                "evidence": "Document structure",
                "source": "structural",
                "source_doc_id": doc_id,
                "source_chunk_id": cid,
            })

    # Document CONTAINS Section
    for sid, sec in sections_seen.items():
        relations.append({
            "source_id": f"doc_{doc_id}",
            "target_id": sec["id"],
            "source_name": doc_id,
            "target_name": sec["name"],
            "relation": "CONTAINS",
            "confidence": 1.0,
            "evidence": "Document structure",
            "source": "structural",
            "source_doc_id": doc_id,
            "source_chunk_id": "",
        })

    return relations
