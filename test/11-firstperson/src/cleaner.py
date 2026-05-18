"""
Entity and Relation Cleaner Module (Member 1)

Cleans extracted entities and relations:
  - Remove duplicates
  - Merge similar entities
  - Normalize names
  - Filter noise/low-quality
"""

import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Dict, List, Set, Tuple

# Common noise words to filter
NOISE_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "this", "that", "these", "those", "it", "its", "we", "our", "you",
    "your", "they", "their", "he", "she", "his", "her", "which", "what",
    "who", "whom", "because", "but", "and", "or", "if", "while",
    "figure", "table", "section", "equation", "paper", "work", "et", "al",
    "also", "however", "therefore", "thus", "furthermore", "moreover",
    "e.g", "i.e", "etc", "vs", "ie", "eg", "fig", "tab", "sec", "eq",
}


def normalize_name(name: str) -> str:
    """Normalize entity name for comparison."""
    name = name.strip()
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    # Remove leading/trailing punctuation
    name = name.strip('.,;:!?()[]{}"\'-')
    return name


def name_similarity(a: str, b: str) -> float:
    """Compute similarity between two entity names."""
    a_lower = a.lower().strip()
    b_lower = b.lower().strip()

    if a_lower == b_lower:
        return 1.0

    # Check if one is substring of the other
    if a_lower in b_lower or b_lower in a_lower:
        return 0.9

    # Check acronym match (e.g., "NMT" matches "Neural Machine Translation")
    a_words = a_lower.split()
    b_words = b_lower.split()
    if len(a_words) == 1 and len(b_words) >= 2:
        acronym = ''.join(w[0] for w in b_words if w)
        if a_lower == acronym:
            return 0.95
    if len(b_words) == 1 and len(a_words) >= 2:
        acronym = ''.join(w[0] for w in a_words if w)
        if b_lower == acronym:
            return 0.95

    # Sequence matcher
    return SequenceMatcher(None, a_lower, b_lower).ratio()


def is_noise_entity(entity: Dict[str, Any]) -> bool:
    """Check if an entity is noise (should be removed)."""
    name = entity.get("name", "").strip()

    # Empty or whitespace only
    if not name:
        return True

    # Too short (single char or 2 chars for non-acronyms)
    if len(name) <= 1:
        return True
    if len(name) <= 2 and not name.isupper():
        return True

    # Pure numbers
    if name.replace('.', '').replace('-', '').isdigit():
        return True

    # Common noise words
    if name.lower().strip('.,;:') in NOISE_WORDS:
        return True

    # Single common word
    words = name.lower().split()
    if len(words) == 1 and words[0] in NOISE_WORDS:
        return True

    # Very long names (likely extraction error)
    if len(name) > 100:
        return True

    # Names that are just punctuation or special chars
    if not any(c.isalnum() for c in name):
        return True

    # HTML fragments (table cells, div tags, etc.)
    if '<' in name and '>' in name:
        return True
    if name.startswith('>'):
        return True

    return False


def is_low_quality_relation(relation: Dict[str, Any]) -> bool:
    """Check if a relation is low quality (should be removed)."""
    # Low confidence
    confidence = relation.get("confidence", 0)
    if confidence < 0.25:
        return True

    # Self-loop
    if relation.get("source_id") == relation.get("target_id"):
        return True

    # Empty source or target
    if not relation.get("source_name", "").strip() or not relation.get("target_name", "").strip():
        return True

    # Invalid relation type
    valid_types = {
        "CONTAINS", "PROPOSES", "USES", "EVALUATES_ON", "ACHIEVES",
        "BASED_ON", "BELONGS_TO", "DEPENDS_ON", "COMPARES_WITH", "PART_OF",
    }
    if relation.get("relation") not in valid_types:
        return True

    return False


def deduplicate_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove exact duplicates and merge similar entities."""
    if not entities:
        return []

    # First pass: exact dedup by normalized name + type
    seen: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for ent in entities:
        key = (normalize_name(ent["name"]).lower(), ent.get("type", "Concept"))
        if key not in seen:
            seen[key] = ent.copy()
        else:
            # Keep the one with higher confidence
            existing = seen[key]
            if ent.get("confidence", 0) > existing.get("confidence", 0):
                # Merge: keep higher confidence but combine sources
                ent_copy = ent.copy()
                ent_copy["source"] = f"{existing.get('source', '')},{ent.get('source', '')}"
                seen[key] = ent_copy

    deduped = list(seen.values())

    # Second pass: merge similar entities (same type)
    merged = []
    used = set()
    for i, a in enumerate(deduped):
        if i in used:
            continue
        group = [a]
        for j, b in enumerate(deduped):
            if j <= i or j in used:
                continue
            if a.get("type") == b.get("type"):
                sim = name_similarity(a["name"], b["name"])
                if sim >= 0.85:
                    group.append(b)
                    used.add(j)

        # Pick best from group (longest name, highest confidence)
        best = max(group, key=lambda e: (len(e.get("name", "")), e.get("confidence", 0)))
        # Collect all source chunk IDs
        all_chunks = set()
        for g in group:
            cid = g.get("source_chunk_id", "")
            if cid:
                all_chunks.add(cid)
        best["source_chunk_ids"] = list(all_chunks)
        merged.append(best)
        used.add(i)

    return merged


def clean_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Full cleaning pipeline for entities."""
    # 1. Remove noise
    filtered = [e for e in entities if not is_noise_entity(e)]

    # 2. Normalize names
    for e in filtered:
        e["name"] = normalize_name(e["name"])

    # 3. Deduplicate and merge
    deduped = deduplicate_entities(filtered)

    # 4. Re-assign IDs after dedup
    for i, e in enumerate(deduped):
        doc_id = e.get("source_doc_id", "unknown")
        e["id"] = f"ent_{doc_id}_{i:04d}"

    return deduped


def clean_relations(
    relations: List[Dict[str, Any]],
    valid_entity_ids: Set[str],
) -> List[Dict[str, Any]]:
    """Full cleaning pipeline for relations."""
    # 1. Filter low quality
    filtered = [r for r in relations if not is_low_quality_relation(r)]

    # 2. Remove relations with invalid entity references
    valid = []
    for r in filtered:
        src = r.get("source_id", "")
        tgt = r.get("target_id", "")
        # Allow structural nodes (section_, chunk_, doc_)
        if src.startswith(("section_", "chunk_", "doc_")) or src in valid_entity_ids:
            if tgt.startswith(("section_", "chunk_", "doc_")) or tgt in valid_entity_ids:
                valid.append(r)

    # 3. Deduplicate (same source, target, relation)
    seen = {}
    for r in valid:
        key = (r["source_id"], r["target_id"], r["relation"])
        if key not in seen or r.get("confidence", 0) > seen[key].get("confidence", 0):
            seen[key] = r

    return list(seen.values())


def generate_cleaning_report(
    raw_entities: List[Dict[str, Any]],
    cleaned_entities: List[Dict[str, Any]],
    raw_relations: List[Dict[str, Any]],
    cleaned_relations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate a cleaning statistics report."""
    raw_types = Counter(e.get("type", "Unknown") for e in raw_entities)
    cleaned_types = Counter(e.get("type", "Unknown") for e in cleaned_entities)
    raw_sources = Counter(e.get("source", "unknown") for e in raw_entities)
    cleaned_sources = Counter(e.get("source", "unknown") for e in cleaned_entities)
    rel_types = Counter(r.get("relation", "Unknown") for r in cleaned_relations)

    return {
        "entities": {
            "raw_count": len(raw_entities),
            "cleaned_count": len(cleaned_entities),
            "removed_count": len(raw_entities) - len(cleaned_entities),
            "dedup_rate": round(1 - len(cleaned_entities) / max(len(raw_entities), 1), 3),
            "raw_type_distribution": dict(raw_types.most_common()),
            "cleaned_type_distribution": dict(cleaned_types.most_common()),
            "raw_source_distribution": dict(raw_sources.most_common()),
            "cleaned_source_distribution": dict(cleaned_sources.most_common()),
        },
        "relations": {
            "raw_count": len(raw_relations),
            "cleaned_count": len(cleaned_relations),
            "removed_count": len(raw_relations) - len(cleaned_relations),
            "type_distribution": dict(rel_types.most_common()),
        },
    }
