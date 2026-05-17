"""
Entity & Relation Extraction Demo (Member 1)

Demonstrates extraction on a single document.
Run: python test/kg_extraction/extract_demo.py
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "test"))

from kg_extraction.entity_extractor import extract_entities_from_document
from kg_extraction.relation_extractor import extract_relations_from_chunk, extract_structural_relations
from kg_extraction.cleaner import clean_entities, clean_relations, generate_cleaning_report


def load_lad_chunks(doc_path: Path) -> list:
    with open(doc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("chunks", [])


def main():
    # Use a sample document
    doc_path = ROOT / "test" / "8-lad_rag_test" / "data" / "documents" / "1603.09631" / "lad_chunk.json"
    if not doc_path.exists():
        print(f"Document not found: {doc_path}")
        sys.exit(1)

    print(f"Loading document: {doc_path}")
    chunks = load_lad_chunks(doc_path)
    print(f"Loaded {len(chunks)} chunks")

    # Extract entities
    print("\n--- Entity Extraction ---")
    t0 = time.time()
    raw_entities = extract_entities_from_document(chunks, use_llm=True, max_llm_calls=5, llm_batch_size=3)
    t1 = time.time()
    print(f"Raw entities: {len(raw_entities)} (took {t1-t0:.1f}s)")

    # Extract relations
    print("\n--- Relation Extraction ---")
    raw_relations = extract_structural_relations(chunks)
    # Per-chunk relations
    for chunk in chunks[:10]:  # demo: first 10 chunks
        chunk_entities = [e for e in raw_entities if e.get("source_chunk_id") == chunk.get("chunkId")]
        if len(chunk_entities) >= 2:
            rels = extract_relations_from_chunk(chunk, chunk_entities, use_llm=False)
            raw_relations.extend(rels)
    t2 = time.time()
    print(f"Raw relations: {len(raw_relations)} (took {t2-t1:.1f}s)")

    # Clean
    print("\n--- Cleaning ---")
    cleaned_entities = clean_entities(raw_entities)
    entity_ids = {e["id"] for e in cleaned_entities}
    cleaned_relations = clean_relations(raw_relations, entity_ids)
    report = generate_cleaning_report(raw_entities, cleaned_entities, raw_relations, cleaned_relations)

    print(f"Cleaned entities: {len(cleaned_entities)} (removed {report['entities']['removed_count']})")
    print(f"Cleaned relations: {len(cleaned_relations)} (removed {report['relations']['removed_count']})")
    print(f"\nEntity type distribution: {report['entities']['cleaned_type_distribution']}")
    print(f"Relation type distribution: {report['relations']['type_distribution']}")

    # Save results
    output_dir = ROOT / "test" / "kg_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "demo_entities.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_entities, f, ensure_ascii=False, indent=2)
    with open(output_dir / "demo_relations.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_relations, f, ensure_ascii=False, indent=2)
    with open(output_dir / "demo_extraction_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {output_dir}")
    print("Done!")


if __name__ == "__main__":
    main()
