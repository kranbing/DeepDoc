"""
Neo4j Store - Stub Interface (Member 2)

Optional Neo4j backend. Requires neo4j Python driver.
This is a placeholder - not a hard dependency.
"""

from typing import Any, Dict, List, Optional

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

from .graph_store import GraphStore


class Neo4jGraphStore(GraphStore):
    """Neo4j-based knowledge graph storage (optional)."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = ""):
        if not HAS_NEO4J:
            raise ImportError(
                "neo4j Python driver not installed. "
                "Install with: pip install neo4j"
            )
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self._driver:
            self._driver.close()

    def add_nodes(self, nodes: List[Dict[str, Any]]) -> int:
        added = 0
        with self._driver.session() as session:
            for node in nodes:
                nid = node.get("id", "")
                ntype = node.get("type", "Entity")
                props = {k: v for k, v in node.items() if k not in ("id", "type") and v}
                query = (
                    f"MERGE (n:{ntype} {{id: $id}}) "
                    f"SET n += $props RETURN n"
                )
                session.run(query, id=nid, props=props)
                added += 1
        return added

    def add_edges(self, edges: List[Dict[str, Any]]) -> int:
        added = 0
        with self._driver.session() as session:
            for edge in edges:
                src = edge.get("source_id", "")
                tgt = edge.get("target_id", "")
                rel = edge.get("relation", "RELATED")
                props = {k: v for k, v in edge.items()
                         if k not in ("source_id", "target_id", "relation") and v}
                query = (
                    f"MATCH (a {{id: $src}}), (b {{id: $tgt}}) "
                    f"MERGE (a)-[r:{rel}]->(b) "
                    f"SET r += $props RETURN r"
                )
                session.run(query, src=src, tgt=tgt, props=props)
                added += 1
        return added

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run("MATCH (n {id: $id}) RETURN n", id=node_id)
            record = result.single()
            return dict(record["n"]) if record else None

    def get_neighbors(self, node_id: str, relation: str = None) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            if relation:
                query = (
                    f"MATCH (n {{id: $id}})-[r:{relation}]-(m) "
                    f"RETURN m, type(r) as rel"
                )
            else:
                query = (
                    "MATCH (n {id: $id})-[r]-(m) "
                    "RETURN m, type(r) as rel"
                )
            result = session.run(query, id=node_id)
            return [
                {**dict(record["m"]), "_edge_relation": record["rel"]}
                for record in result
            ]

    def find_path(self, source_id: str, target_id: str, max_hops: int = 2) -> List[List[str]]:
        with self._driver.session() as session:
            query = (
                "MATCH path = (a {id: $src})-[*1..{max_hops}]-(b {id: $tgt}) "
                "RETURN [n IN nodes(path) | n.id] as path LIMIT 5"
            ).format(max_hops=max_hops)
            result = session.run(query, src=source_id, tgt=target_id)
            return [record["path"] for record in result]

    def search_by_name(self, name: str, fuzzy: bool = True) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            if fuzzy:
                query = "MATCH (n) WHERE toLower(n.name) CONTAINS toLower($name) RETURN n LIMIT 20"
            else:
                query = "MATCH (n {name: $name}) RETURN n"
            result = session.run(query, name=name)
            return [dict(record["n"]) for record in result]

    def search_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(f"MATCH (n:{entity_type}) RETURN n")
            return [dict(record["n"]) for record in result]

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run("MATCH (n) RETURN n")
            return [dict(record["n"]) for record in result]

    def get_all_edges(self) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run("MATCH (a)-[r]->(b) RETURN a.id as src, b.id as tgt, type(r) as rel, r")
            return [
                {"source_id": r["src"], "target_id": r["tgt"], "relation": r["rel"], **dict(r["r"])}
                for r in result
            ]

    def get_stats(self) -> Dict[str, Any]:
        with self._driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) as c").single()["c"]
            edges = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()["c"]
            return {"total_nodes": nodes, "total_edges": edges}

    def save(self, path: str) -> None:
        # Neo4j persists automatically; this exports to JSON
        import json
        data = {
            "nodes": self.get_all_nodes(),
            "edges": self.get_all_edges(),
            "metadata": self.get_stats(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> None:
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.add_nodes(data.get("nodes", []))
        self.add_edges(data.get("edges", []))
