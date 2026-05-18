"""
Query Engine (Member 2)

Provides high-level query interface over a GraphStore.
"""

from typing import Any, Dict, List, Optional, Set

from .graph_store import GraphStore


class QueryEngine:
    """High-level query interface for knowledge graph."""

    def __init__(self, store: GraphStore):
        self.store = store

    def find_entity(self, name: str) -> List[Dict[str, Any]]:
        """Find entities by name (fuzzy match)."""
        return self.store.search_by_name(name, fuzzy=True)

    def get_entity_relations(self, entity_id: str, relation: str = None) -> Dict[str, Any]:
        """Get all relations for an entity (one-hop)."""
        node = self.store.get_node(entity_id)
        if not node:
            return {"found": False, "entity_id": entity_id, "neighbors": []}

        neighbors = self.store.get_neighbors(entity_id, relation=relation)
        return {
            "found": True,
            "entity": node,
            "neighbors": neighbors,
            "neighbor_count": len(neighbors),
        }

    def check_relation(
        self, source_id: str, target_id: str, max_hops: int = 2
    ) -> Dict[str, Any]:
        """Check if relation exists between two entities."""
        paths = self.store.find_path(source_id, target_id, max_hops)
        direct = any(len(p) == 2 for p in paths)
        return {
            "source_id": source_id,
            "target_id": target_id,
            "direct_relation": direct,
            "path_count": len(paths),
            "paths": paths,
            "min_hops": min(len(p) - 1 for p in paths) if paths else -1,
        }

    def search_candidates(
        self, query: str, max_results: int = 10
    ) -> Dict[str, Any]:
        """Search for entities and their relations matching a query."""
        # Split query into keywords
        keywords = query.lower().split()
        candidates: Dict[str, float] = {}  # node_id -> score

        for kw in keywords:
            if len(kw) < 2:
                continue
            matches = self.store.search_by_name(kw, fuzzy=True)
            for m in matches:
                nid = m.get("id", "")
                score = m.get("_match_score", 1.0)
                candidates[nid] = max(candidates.get(nid, 0), score)

        # Sort by score
        sorted_ids = sorted(candidates.keys(), key=lambda x: candidates[x], reverse=True)
        top_ids = sorted_ids[:max_results]

        results = []
        for nid in top_ids:
            node = self.store.get_node(nid)
            if node:
                neighbors = self.store.get_neighbors(nid)
                results.append({
                    "entity": node,
                    "score": candidates[nid],
                    "neighbors": [
                        {"id": n.get("id"), "name": n.get("name"), "type": n.get("type"),
                         "relation": n.get("_edge_relation")}
                        for n in neighbors[:5]
                    ],
                })

        return {
            "query": query,
            "candidate_count": len(results),
            "candidates": results,
        }

    def get_entity_context(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get entity with its neighborhood context."""
        node = self.store.get_node(entity_id)
        if not node:
            return {"found": False}

        neighbors = self.store.get_neighbors(entity_id)
        context = {
            "found": True,
            "entity": node,
            "direct_neighbors": [],
        }

        for n in neighbors:
            neighbor_info = {
                "id": n.get("id"),
                "name": n.get("name"),
                "type": n.get("type"),
                "relation": n.get("_edge_relation"),
                "confidence": n.get("_edge_confidence", 0),
            }
            context["direct_neighbors"].append(neighbor_info)

        context["neighbor_count"] = len(context["direct_neighbors"])
        return context

    def get_graph_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the graph."""
        stats = self.store.get_stats()
        return {
            "total_nodes": stats.get("total_nodes", 0),
            "total_edges": stats.get("total_edges", 0),
            "node_types": stats.get("node_types", {}),
            "edge_types": stats.get("edge_types", {}),
            "density": (
                stats.get("total_edges", 0) /
                max(stats.get("total_nodes", 1) * (stats.get("total_nodes", 1) - 1), 1)
            ),
        }
