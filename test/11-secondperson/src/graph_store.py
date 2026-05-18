"""
Graph Store - Abstract Interface (Member 2)

Defines the interface for knowledge graph storage backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set


class GraphStore(ABC):
    """Abstract base class for knowledge graph storage."""

    @abstractmethod
    def add_nodes(self, nodes: List[Dict[str, Any]]) -> int:
        """Add nodes to the graph. Returns count added."""
        pass

    @abstractmethod
    def add_edges(self, edges: List[Dict[str, Any]]) -> int:
        """Add edges to the graph. Returns count added."""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID."""
        pass

    @abstractmethod
    def get_neighbors(self, node_id: str, relation: str = None) -> List[Dict[str, Any]]:
        """Get one-hop neighbors of a node, optionally filtered by relation."""
        pass

    @abstractmethod
    def find_path(self, source_id: str, target_id: str, max_hops: int = 2) -> List[List[str]]:
        """Find paths between two nodes (up to max_hops)."""
        pass

    @abstractmethod
    def search_by_name(self, name: str, fuzzy: bool = True) -> List[Dict[str, Any]]:
        """Search nodes by name (exact or fuzzy)."""
        pass

    @abstractmethod
    def search_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Get all nodes of a given type."""
        pass

    @abstractmethod
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes."""
        pass

    @abstractmethod
    def get_all_edges(self) -> List[Dict[str, Any]]:
        """Get all edges."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist graph to storage."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load graph from storage."""
        pass
