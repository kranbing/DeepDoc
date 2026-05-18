"""
Query Demo (Member 2)

Demonstrates querying the knowledge graph.
Run: python test/kg_storage/query_demo.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "test"))

from kg_storage.json_store import JsonGraphStore
from kg_storage.query_engine import QueryEngine


def main():
    # Load graph
    graph_path = ROOT / "test" / "kg_output" / "kg_graph.json"
    if not graph_path.exists():
        print(f"Graph not found: {graph_path}")
        print("Run run_kg_pipeline.py first.")
        sys.exit(1)

    store = JsonGraphStore()
    store.load(str(graph_path))
    engine = QueryEngine(store)

    print("=" * 60)
    print("Knowledge Graph Query Demo")
    print("=" * 60)

    # 1. Graph summary
    summary = engine.get_graph_summary()
    print(f"\n[Graph Summary]")
    print(f"  Nodes: {summary['total_nodes']}")
    print(f"  Edges: {summary['total_edges']}")
    print(f"  Node types: {summary['node_types']}")
    print(f"  Edge types: {summary['edge_types']}")

    # 2. Find entities
    print(f"\n[Search: 'BERT']")
    results = engine.find_entity("BERT")
    for r in results[:3]:
        print(f"  Found: {r.get('name')} ({r.get('type')}) id={r.get('id')}")

    # 3. One-hop query
    if results:
        entity_id = results[0]["id"]
        print(f"\n[One-hop neighbors of '{results[0].get('name')}']")
        relations = engine.get_entity_relations(entity_id)
        for n in relations.get("neighbors", [])[:5]:
            print(f"  --[{n.get('_edge_relation')}]--> {n.get('name')} ({n.get('type')})")

    # 4. Search candidates
    print(f"\n[Search candidates: 'question answering']")
    candidates = engine.search_candidates("question answering")
    for c in candidates.get("candidates", [])[:3]:
        print(f"  {c['entity'].get('name')} (score={c['score']:.2f})")
        for n in c.get("neighbors", [])[:2]:
            print(f"    --[{n.get('relation')}]--> {n.get('name')}")

    # 5. Two-entity path
    nodes = store.get_all_nodes()
    methods = [n for n in nodes if n.get("type") == "Method"]
    datasets = [n for n in nodes if n.get("type") == "Dataset"]
    if methods and datasets:
        src = methods[0]["id"]
        tgt = datasets[0]["id"]
        print(f"\n[Path query: '{methods[0].get('name')}' -> '{datasets[0].get('name')}']")
        path_result = engine.check_relation(src, tgt)
        print(f"  Direct relation: {path_result['direct_relation']}")
        print(f"  Paths found: {path_result['path_count']}")
        if path_result['paths']:
            print(f"  Shortest path: {' -> '.join(path_result['paths'][0])}")

    # 6. Save query report
    output_dir = ROOT / "test" / "kg_output"
    report = {
        "graph_summary": summary,
        "search_bert": {"count": len(results), "top_results": [
            {"name": r.get("name"), "type": r.get("type")} for r in results[:5]
        ]},
        "search_qa_candidates": {
            "count": candidates.get("candidate_count", 0),
            "top": [
                {"name": c["entity"].get("name"), "score": c.get("score", 0)}
                for c in candidates.get("candidates", [])[:5]
            ],
        },
    }
    report_path = output_dir / "query_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nQuery report saved to {report_path}")


if __name__ == "__main__":
    main()
