"""
Knowledge Graph Pipeline - Unified Entry Point

Runs the full KG pipeline:
  1. Read data from test/8-lad_rag_test/data/documents/
  2. Entity extraction (rule-based + LLM)
  3. Relation extraction (pattern + co-occurrence + LLM)
  4. Cleaning (dedup, merge, filter)
  5. Write to JSON graph store
  6. Query tests
  7. Output graph JSON, reports, and visualization

Run: conda run -n deepdoc python test/run_kg_pipeline.py
"""

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_DIR = ROOT / "test"
OUTPUT_DIR = TEST_DIR / "kg_output"

# Ensure test/ is in path for imports
sys.path.insert(0, str(TEST_DIR))

from kg_extraction.entity_extractor import extract_entities_from_document
from kg_extraction.relation_extractor import (
    extract_relations_from_chunk,
    extract_structural_relations,
)
from kg_extraction.cleaner import (
    clean_entities,
    clean_relations,
    generate_cleaning_report,
)
from kg_storage.json_store import JsonGraphStore
from kg_storage.query_engine import QueryEngine
from kg_design.visualize_graph import generate_html_preview, generate_markdown_preview

# Data source — user's uploaded documents
DATA_DIR = ROOT / "data" / "projects" / "e8d8bb21-228a-49ee-8a87-bf5138a84900" / "documents"


def load_documents(max_docs: int = 5) -> dict:
    """Load lad_chunk.json files for processing."""
    documents = {}

    doc_ids = [d.name for d in DATA_DIR.iterdir() if d.is_dir()][:max_docs]

    for doc_id in doc_ids:
        chunk_path = DATA_DIR / doc_id / "lad_chunk.json"
        if chunk_path.exists():
            with open(chunk_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            chunks = data.get("chunks", [])
            doc_name = data.get("docName", doc_id)
            abstract = data.get("abstract", "")
            sections = data.get("structure", {}).get("sections", [])
            documents[doc_id] = {
                "chunks": chunks,
                "docName": doc_name,
                "abstract": abstract,
                "sections": sections,
                "chunk_count": len(chunks),
            }
            print(f"  Loaded {doc_id}: {len(chunks)} chunks - {doc_name[:60]}")

    return documents


def process_document(
    doc_id: str,
    doc_data: dict,
    use_llm: bool = True,
    max_llm_calls: int = 10,
) -> dict:
    """Process a single document: extract entities, relations, clean."""
    chunks = doc_data["chunks"]
    doc_name = doc_data["docName"]

    print(f"\n{'='*60}")
    print(f"Processing: {doc_id} - {doc_name[:60]}")
    print(f"  Chunks: {len(chunks)}")

    # 1. Entity extraction
    print("  [1/4] Extracting entities...")
    t0 = time.time()
    raw_entities = extract_entities_from_document(
        chunks, use_llm=use_llm, max_llm_calls=max_llm_calls, llm_batch_size=3
    )
    t1 = time.time()
    print(f"    Raw entities: {len(raw_entities)} ({t1-t0:.1f}s)")

    # 2. Relation extraction
    print("  [2/4] Extracting relations...")
    raw_relations = extract_structural_relations(chunks)

    # Per-chunk relation extraction (rule-based, no LLM for speed)
    for chunk in chunks:
        chunk_entities = [e for e in raw_entities if e.get("source_chunk_id") == chunk.get("chunkId")]
        if len(chunk_entities) >= 2:
            rels = extract_relations_from_chunk(chunk, chunk_entities, use_llm=False)
            raw_relations.extend(rels)

    t2 = time.time()
    print(f"    Raw relations: {len(raw_relations)} ({t2-t1:.1f}s)")

    # 3. Cleaning
    print("  [3/4] Cleaning...")
    cleaned_entities = clean_entities(raw_entities)

    # Build name->id mapping to remap relations after entity ID reassignment
    name_to_new_id = {}
    for e in cleaned_entities:
        name_to_new_id[e["name"].lower()] = e["id"]

    # Remap relation source/target IDs using entity names
    old_id_to_name = {}
    for e in raw_entities:
        old_id_to_name[e["id"]] = e["name"].lower()

    for r in raw_relations:
        src_old = r.get("source_id", "")
        tgt_old = r.get("target_id", "")
        # Preserve structural IDs (section_, chunk_, doc_) - don't remap them
        if src_old.startswith(("section_", "chunk_", "doc_")) and tgt_old.startswith(("section_", "chunk_", "doc_")):
            continue
        # Try to remap via name lookup
        src_name = old_id_to_name.get(src_old) or r.get("source_name", "").lower()
        tgt_name = old_id_to_name.get(tgt_old) or r.get("target_name", "").lower()
        if src_name in name_to_new_id:
            r["source_id"] = name_to_new_id[src_name]
        if tgt_name in name_to_new_id:
            r["target_id"] = name_to_new_id[tgt_name]

    entity_ids = {e["id"] for e in cleaned_entities}
    cleaned_relations = clean_relations(raw_relations, entity_ids)
    report = generate_cleaning_report(raw_entities, cleaned_entities, raw_relations, cleaned_relations)
    print(f"    Cleaned entities: {len(cleaned_entities)} (removed {report['entities']['removed_count']})")
    print(f"    Cleaned relations: {len(cleaned_relations)} (removed {report['relations']['removed_count']})")

    # 4. Add document node
    doc_node = {
        "id": f"doc_{doc_id}",
        "type": "Document",
        "name": doc_name,
        "description": doc_data.get("abstract", "")[:200],
        "source_doc_id": doc_id,
        "confidence": 1.0,
    }
    cleaned_entities.insert(0, doc_node)

    # Add section nodes (with hierarchy)
    for sec in doc_data.get("sections", []):
        sec_id = sec.get("sectionId", "")
        sec_node = {
            "id": f"section_{sec_id}",
            "type": "Section",
            "name": sec.get("title", sec_id),
            "source_doc_id": doc_id,
            "confidence": 1.0,
            "parentId": sec.get("parentId"),
            "level": sec.get("level", 1),
        }
        cleaned_entities.append(sec_node)

    # Add chunk nodes (needed for structural CONTAINS relations)
    for chunk in chunks:
        cid = chunk.get("chunkId", "")
        if not cid:
            continue
        text = chunk.get("normalizedContent") or chunk.get("cleanText") or chunk.get("content") or ""
        # Strip HTML tags for display name
        import re as _re
        clean_name = _re.sub(r'<[^>]+>', '', text).strip()
        clean_name = _re.sub(r'\s+', ' ', clean_name)[:80]
        chunk_node = {
            "id": f"chunk_{cid}",
            "type": "Chunk",
            "name": clean_name if clean_name else cid,
            "source_doc_id": doc_id,
            "source_chunk_id": cid,
            "sectionId": chunk.get("sectionId", ""),
            "confidence": 1.0,
        }
        cleaned_entities.append(chunk_node)

    return {
        "doc_id": doc_id,
        "entities": cleaned_entities,
        "relations": cleaned_relations,
        "report": report,
    }


def build_graph(all_results: list) -> JsonGraphStore:
    """Build the knowledge graph from all document results."""
    store = JsonGraphStore()

    total_entities = 0
    total_relations = 0

    for result in all_results:
        entities = result["entities"]
        relations = result["relations"]

        store.add_nodes(entities)
        store.add_edges(relations)

        total_entities += len(entities)
        total_relations += len(relations)

    print(f"\n[Graph Built]")
    stats = store.get_stats()
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  Node types: {stats['node_types']}")
    print(f"  Edge types: {stats['edge_types']}")

    return store


def run_query_tests(engine: QueryEngine) -> dict:
    """Run query test suite."""
    print(f"\n{'='*60}")
    print("Running Query Tests")
    print(f"{'='*60}")

    results = {}

    # Test 1: Graph summary
    summary = engine.get_graph_summary()
    results["graph_summary"] = summary
    print(f"\n[Test 1] Graph Summary")
    print(f"  Nodes: {summary['total_nodes']}, Edges: {summary['total_edges']}")

    # Test 2: Search by name
    print(f"\n[Test 2] Search by name")
    for keyword in ["BERT", "Transformer", "NMT", "attention"]:
        matches = engine.find_entity(keyword)
        results[f"search_{keyword}"] = {"count": len(matches), "top": [
            {"name": m.get("name"), "type": m.get("type")} for m in matches[:3]
        ]}
        print(f"  '{keyword}': {len(matches)} matches")

    # Test 3: One-hop query
    print(f"\n[Test 3] One-hop queries")
    nodes = engine.store.get_all_nodes()
    methods = [n for n in nodes if n.get("type") == "Method"]
    if methods:
        test_node = methods[0]
        rels = engine.get_entity_relations(test_node["id"])
        results["one_hop"] = {
            "entity": test_node.get("name"),
            "neighbor_count": rels.get("neighbor_count", 0),
        }
        print(f"  '{test_node.get('name')}': {rels.get('neighbor_count', 0)} neighbors")

    # Test 4: Two-entity path
    print(f"\n[Test 4] Two-entity path")
    datasets = [n for n in nodes if n.get("type") == "Dataset"]
    if methods and datasets:
        path_result = engine.check_relation(methods[0]["id"], datasets[0]["id"])
        results["path_query"] = {
            "source": methods[0].get("name"),
            "target": datasets[0].get("name"),
            "direct": path_result["direct_relation"],
            "paths": path_result["path_count"],
        }
        print(f"  {methods[0].get('name')} -> {datasets[0].get('name')}: "
              f"direct={path_result['direct_relation']}, paths={path_result['path_count']}")

    # Test 5: Candidate search
    print(f"\n[Test 5] Candidate search")
    for query in ["question answering", "machine translation"]:
        candidates = engine.search_candidates(query)
        results[f"candidates_{query.replace(' ', '_')}"] = {
            "count": candidates.get("candidate_count", 0),
        }
        print(f"  '{query}': {candidates.get('candidate_count', 0)} candidates")

    return results


def generate_extraction_reports(all_results: list, output_dir: Path) -> None:
    """Generate per-member extraction reports."""
    # Aggregate stats
    total_raw_entities = 0
    total_cleaned_entities = 0
    total_raw_relations = 0
    total_cleaned_relations = 0
    entity_types = Counter()
    relation_types = Counter()
    entity_sources = Counter()

    for result in all_results:
        report = result.get("report", {})
        total_raw_entities += report.get("entities", {}).get("raw_count", 0)
        total_cleaned_entities += report.get("entities", {}).get("cleaned_count", 0)
        total_raw_relations += report.get("relations", {}).get("raw_count", 0)
        total_cleaned_relations += report.get("relations", {}).get("cleaned_count", 0)

        for ent in result.get("entities", []):
            entity_types[ent.get("type", "Unknown")] += 1
            entity_sources[ent.get("source", "unknown")] += 1
        for rel in result.get("relations", []):
            relation_types[rel.get("relation", "Unknown")] += 1

    # Member 1 report: extraction_report.md
    extraction_report = f"""# Knowledge Extraction Report

**Generated:** {datetime.now().isoformat()}
**Documents Processed:** {len(all_results)}

## Entity Extraction Statistics

| Metric | Value |
|--------|-------|
| Raw entities extracted | {total_raw_entities} |
| After cleaning | {total_cleaned_entities} |
| Removed (noise + duplicates) | {total_raw_entities - total_cleaned_entities} |
| Dedup rate | {round(1 - total_cleaned_entities / max(total_raw_entities, 1), 3):.1%} |

### Entity Type Distribution

| Type | Count |
|------|-------|
"""
    for t, c in entity_types.most_common():
        extraction_report += f"| {t} | {c} |\n"

    extraction_report += f"""
### Extraction Source Distribution

| Source | Count |
|--------|-------|
"""
    for s, c in entity_sources.most_common():
        extraction_report += f"| {s} | {c} |\n"

    extraction_report += f"""
## Relation Extraction Statistics

| Metric | Value |
|--------|-------|
| Raw relations extracted | {total_raw_relations} |
| After cleaning | {total_cleaned_relations} |
| Removed (low quality) | {total_raw_relations - total_cleaned_relations} |

### Relation Type Distribution

| Type | Count |
|------|-------|
"""
    for t, c in relation_types.most_common():
        extraction_report += f"| {t} | {c} |\n"

    extraction_report += """
## Per-Document Results

| Doc ID | Entities | Relations |
|--------|----------|-----------|
"""
    for result in all_results:
        extraction_report += f"| {result['doc_id']} | {len(result['entities'])} | {len(result['relations'])} |\n"

    report_path = output_dir / "extraction_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(extraction_report)
    print(f"  Extraction report: {report_path}")


def main():
    print("=" * 60)
    print("DeepDoc Knowledge Graph Pipeline")
    print("=" * 60)

    # Check API key
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        key_file = ROOT / "backend" / ".deepseek_api_key"
        if key_file.exists():
            api_key = key_file.read_text(encoding="utf-8").strip()

    use_llm = bool(api_key)
    if use_llm:
        print(f"DeepSeek API key found (length={len(api_key)}). LLM extraction ENABLED.")
    else:
        print("WARNING: No DeepSeek API key. Using rule-based extraction only.")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load documents
    print(f"\n[Step 1] Loading documents from {DATA_DIR}")
    max_docs = 5  # Process up to 5 documents for demo
    documents = load_documents(max_docs=max_docs)
    if not documents:
        print("ERROR: No documents found!")
        sys.exit(1)
    print(f"Loaded {len(documents)} documents")

    # Step 2-4: Process each document
    print(f"\n[Step 2-4] Processing documents...")
    all_results = []
    for doc_id, doc_data in documents.items():
        result = process_document(
            doc_id, doc_data,
            use_llm=use_llm,
            max_llm_calls=8,
        )
        all_results.append(result)

    # Step 5: Build graph
    print(f"\n[Step 5] Building knowledge graph...")
    store = build_graph(all_results)

    # Save graph
    graph_path = OUTPUT_DIR / "kg_graph.json"
    store.save(str(graph_path))
    print(f"  Graph saved to {graph_path}")

    # Step 6: Query tests
    engine = QueryEngine(store)
    query_results = run_query_tests(engine)

    # Save query results
    query_path = OUTPUT_DIR / "query_report.json"
    with open(query_path, "w", encoding="utf-8") as f:
        json.dump(query_results, f, ensure_ascii=False, indent=2)
    print(f"  Query report saved to {query_path}")

    # Step 7: Generate outputs
    print(f"\n[Step 7] Generating output files...")
    generate_extraction_reports(all_results, OUTPUT_DIR)

    # Visualization
    graph_data = {
        "nodes": store.get_all_nodes(),
        "edges": store.get_all_edges(),
        "metadata": {
            **store.get_stats(),
            "doc_count": len(all_results),
            "generated_at": datetime.now().isoformat(),
        },
    }
    generate_html_preview(graph_data, OUTPUT_DIR / "graph_preview.html")
    generate_markdown_preview(graph_data, OUTPUT_DIR / "graph_preview.md")

    # Copy to frontend-accessible location
    frontend_kg_path = ROOT / "test" / "lad_test" / "kg_graph.json"
    store.save(str(frontend_kg_path))
    print(f"  Graph also saved to {frontend_kg_path} (for frontend access)")

    # Summary
    print(f"\n{'='*60}")
    print("Pipeline Complete!")
    print(f"{'='*60}")
    stats = store.get_stats()
    print(f"  Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    print(f"  Documents processed: {len(all_results)}")
    print(f"\nOutput files:")
    print(f"  {graph_path}")
    print(f"  {OUTPUT_DIR / 'graph_preview.html'}")
    print(f"  {OUTPUT_DIR / 'graph_preview.md'}")
    print(f"  {OUTPUT_DIR / 'extraction_report.md'}")
    print(f"  {OUTPUT_DIR / 'query_report.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
