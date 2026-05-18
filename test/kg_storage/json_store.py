"""
JSON Store - Local JSON-based Knowledge Graph Storage (Member 2)

Implements GraphStore using dict/in-memory structures with JSON persistence.
"""

import json
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .graph_store import GraphStore


class JsonGraphStore(GraphStore):
    """JSON-based knowledge graph storage."""

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}  # id -> node
        self._edges: List[Dict[str, Any]] = []
        self._adjacency: Dict[str, List[int]] = defaultdict(list)  # node_id -> [edge_indices]
        self._name_index: Dict[str, List[str]] = defaultdict(list)  # lowercase name -> [node_ids]
        self._type_index: Dict[str, List[str]] = defaultdict(list)  # type -> [node_ids]

    def add_nodes(self, nodes: List[Dict[str, Any]]) -> int:
        added = 0
        for node in nodes:
            nid = node.get("id", "")
            if not nid:
                continue
            if nid not in self._nodes:
                self._nodes[nid] = node.copy()
                name = node.get("name", "").lower()
                if name:
                    self._name_index[name].append(nid)
                ntype = node.get("type", "")
                if ntype:
                    self._type_index[ntype].append(nid)
                added += 1
            else:
                # Update existing node (merge)
                existing = self._nodes[nid]
                for k, v in node.items():
                    if k not in existing or (v and not existing.get(k)):
                        existing[k] = v
        return added

    def add_edges(self, edges: List[Dict[str, Any]]) -> int:
        added = 0
        for edge in edges:
            src = edge.get("source_id", "")
            tgt = edge.get("target_id", "")
            rel = edge.get("relation", "")
            if not src or not tgt or not rel:
                continue

            # Check for duplicate
            is_dup = False
            for idx in self._adjacency.get(src, []):
                existing = self._edges[idx]
                if existing.get("target_id") == tgt and existing.get("relation") == rel:
                    # Keep higher confidence
                    if edge.get("confidence", 0) > existing.get("confidence", 0):
                        self._edges[idx] = edge.copy()
                    is_dup = True
                    break

            if not is_dup:
                idx = len(self._edges)
                self._edges.append(edge.copy())
                self._adjacency[src].append(idx)
                self._adjacency[tgt].append(idx)  # undirected traversal
                added += 1

        return added

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str, relation: str = None) -> List[Dict[str, Any]]:
        neighbors = []
        seen = set()
        for idx in self._adjacency.get(node_id, []):
            edge = self._edges[idx]
            if relation and edge.get("relation") != relation:
                continue
            # Find the other end
            other_id = edge.get("target_id") if edge.get("source_id") == node_id else edge.get("source_id")
            if other_id and other_id not in seen:
                seen.add(other_id)
                node = self._nodes.get(other_id, {})
                neighbors.append({
                    **node,
                    "_edge_relation": edge.get("relation"),
                    "_edge_confidence": edge.get("confidence", 0),
                    "_edge_evidence": edge.get("evidence", ""),
                })
        return neighbors

    def find_path(self, source_id: str, target_id: str, max_hops: int = 2) -> List[List[str]]:
        """BFS path search."""
        if source_id == target_id:
            return [[source_id]]

        paths = []
        queue = [[source_id]]
        visited = {source_id}

        for _ in range(max_hops):
            next_queue = []
            for path in queue:
                current = path[-1]
                for idx in self._adjacency.get(current, []):
                    edge = self._edges[idx]
                    other_id = edge.get("target_id") if edge.get("source_id") == current else edge.get("source_id")
                    if not other_id or other_id in visited:
                        continue
                    new_path = path + [other_id]
                    if other_id == target_id:
                        paths.append(new_path)
                    else:
                        next_queue.append(new_path)
                        visited.add(other_id)
            queue = next_queue
            if paths:
                break

        return paths

    def search_by_name(self, name: str, fuzzy: bool = True) -> List[Dict[str, Any]]:
        name_lower = name.lower().strip()
        results = []

        # Exact match
        for nid in self._name_index.get(name_lower, []):
            results.append(self._nodes[nid])

        if not results and fuzzy:
            # Fuzzy match
            for indexed_name, nids in self._name_index.items():
                ratio = SequenceMatcher(None, name_lower, indexed_name).ratio()
                if ratio >= 0.6:
                    for nid in nids:
                        node = self._nodes[nid].copy()
                        node["_match_score"] = ratio
                        results.append(node)

            # Substring match
            if not results:
                for indexed_name, nids in self._name_index.items():
                    if name_lower in indexed_name or indexed_name in name_lower:
                        for nid in nids:
                            node = self._nodes[nid].copy()
                            node["_match_score"] = 0.7
                            results.append(node)

        # Sort by match score
        results.sort(key=lambda x: x.get("_match_score", 1.0), reverse=True)
        return results

    def search_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        return [self._nodes[nid] for nid in self._type_index.get(entity_type, []) if nid in self._nodes]

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        return list(self._nodes.values())

    def get_all_edges(self) -> List[Dict[str, Any]]:
        return list(self._edges)

    def get_stats(self) -> Dict[str, Any]:
        from collections import Counter
        type_counts = Counter(n.get("type", "Unknown") for n in self._nodes.values())
        rel_counts = Counter(e.get("relation", "Unknown") for e in self._edges)
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "node_types": dict(type_counts.most_common()),
            "edge_types": dict(rel_counts.most_common()),
        }

    def save(self, path: str) -> None:
        data = {
            "nodes": list(self._nodes.values()),
            "edges": self._edges,
            "metadata": {
                **self.get_stats(),
                "generated_at": __import__("datetime").datetime.now().isoformat(),
            },
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()
        self._name_index.clear()
        self._type_index.clear()
        self.add_nodes(data.get("nodes", []))
        self.add_edges(data.get("edges", []))
