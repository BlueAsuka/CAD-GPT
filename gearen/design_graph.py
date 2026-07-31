"""Serializable design-graph wrapper for requirements and product topology."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from gearen.models import GearboxRequirement


NODE_TYPES = {
    "DesignTask",
    "Requirement",
    "Gearbox",
    "InputShaft",
    "OutputShaft",
    "Pinion",
    "GearWheel",
    "GearMesh",
    "Bearing",
    "Key",
    "Housing",
    "HousingCover",
}

EDGE_TYPES = {
    "has_requirement",
    "contains",
    "mounted_on",
    "meshes_with",
    "supports",
    "keyed_to",
    "integral_with",
    "parallel_to",
    "transmits_power_to",
    "contained_in",
}


class DesignGraph:
    """Hide NetworkX details behind a small serializable graph API."""

    def __init__(self) -> None:
        """Create an empty directed multigraph."""
        self._graph = nx.MultiDiGraph()

    def add_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
        source: str = "generated",
        status: str = "provisional",
        geometry_type: str | None = None,
        geometry_parameters: dict[str, Any] | None = None,
    ) -> bool:
        """Add a typed node once; return False when its identifier already exists."""
        if node_type not in NODE_TYPES:
            raise ValueError(f"unsupported node type: {node_type}")
        if self._graph.has_node(node_id):
            return False
        self._graph.add_node(
            node_id,
            id=node_id,
            node_type=node_type,
            name=name,
            attributes=attributes or {},
            source=source,
            status=status,
            geometry_type=geometry_type,
            geometry_parameters=geometry_parameters or {},
        )
        return True

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> bool:
        """Add a typed edge once for a source-target-type combination."""
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"unsupported edge type: {edge_type}")
        if source_id not in self._graph or target_id not in self._graph:
            raise KeyError(f"edge endpoints must exist: {source_id}, {target_id}")
        edge_data = self._graph.get_edge_data(source_id, target_id, default={})
        if any(data.get("edge_type") == edge_type for data in edge_data.values()):
            return False
        self._graph.add_edge(
            source_id,
            target_id,
            edge_type=edge_type,
            attributes=attributes or {},
        )
        return True

    def has_node(self, node_id: str) -> bool:
        """Return whether a stable node identifier exists."""
        return self._graph.has_node(node_id)

    def has_node_type(self, node_type: str) -> bool:
        """Return whether at least one node has the requested type."""
        return bool(self.nodes_by_type(node_type))

    def nodes_by_type(self, node_type: str) -> list[dict[str, Any]]:
        """Return copied node payloads matching a type."""
        return [
            dict(data)
            for _, data in self._graph.nodes(data=True)
            if data["node_type"] == node_type
        ]

    def edges_by_type(self, edge_type: str) -> list[dict[str, Any]]:
        """Return source, target, and copied payload for matching edges."""
        return [
            {"source": source, "target": target, **dict(data)}
            for source, target, data in self._graph.edges(data=True)
            if data["edge_type"] == edge_type
        ]

    def node(self, node_id: str) -> dict[str, Any]:
        """Return a copied node payload by identifier."""
        if node_id not in self._graph:
            raise KeyError(node_id)
        return dict(self._graph.nodes[node_id])

    def update_node(self, node_id: str, **changes: Any) -> None:
        """Update serializable node fields without exposing the underlying graph."""
        if node_id not in self._graph:
            raise KeyError(node_id)
        self._graph.nodes[node_id].update(changes)

    def copy(self) -> "DesignGraph":
        """Return an independent copy suitable for product-graph expansion."""
        duplicate = DesignGraph()
        duplicate._graph = self._graph.copy()
        return duplicate

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> 'DesignGraph':
        '''Rebuild a graph from its exported JSON representation.'''
        graph = cls()
        for raw_node in payload.get('nodes', []):
            node = dict(raw_node)
            node_id = node.pop('id')
            node_type = node.pop('node_type')
            name = node.pop('name')
            graph.add_node(node_id, node_type, name, **node)
        for raw_edge in payload.get('edges', []):
            edge = dict(raw_edge)
            source = edge.pop('source')
            target = edge.pop('target')
            edge_type = edge.pop('edge_type')
            graph.add_edge(source, target, edge_type, **edge)
        return graph

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        """Return deterministic node and edge lists suitable for JSON."""
        nodes = [
            dict(data)
            for _, data in sorted(self._graph.nodes(data=True), key=lambda item: item[0])
        ]
        edges = [
            {"source": source, "target": target, **dict(data)}
            for source, target, _, data in sorted(
                self._graph.edges(keys=True, data=True),
                key=lambda item: (item[0], item[1], item[3]["edge_type"]),
            )
        ]
        return {"nodes": nodes, "edges": edges}

    def export_json(self, path: Path) -> None:
        """Export the graph as human-readable UTF-8 JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def export_graphml(self, path: Path) -> None:
        """Export GraphML after encoding nested attributes as JSON strings."""
        graph = nx.MultiDiGraph()
        for node_id, data in self._graph.nodes(data=True):
            graph.add_node(node_id, **self._graphml_values(data))
        for source, target, key, data in self._graph.edges(keys=True, data=True):
            graph.add_edge(source, target, key=key, **self._graphml_values(data))
        path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(graph, path, encoding="utf-8")

    def validate_basic_structure(self) -> list[str]:
        """Return basic serialization and endpoint issues; an empty list passes."""
        issues: list[str] = []
        if not self.has_node_type("DesignTask"):
            issues.append("missing DesignTask node")
        try:
            json.dumps(self.to_dict(), ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            issues.append(f"graph is not JSON serializable: {exc}")
        return issues

    @staticmethod
    def _graphml_values(data: dict[str, Any]) -> dict[str, str | int | float | bool]:
        """Convert nested or null values to GraphML-compatible scalars."""
        converted: dict[str, str | int | float | bool] = {}
        for key, value in data.items():
            if isinstance(value, (dict, list, tuple)) or value is None:
                converted[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (str, int, float, bool)):
                converted[key] = value
            else:
                converted[key] = str(value)
        return converted


def build_requirement_graph(requirement: GearboxRequirement) -> DesignGraph:
    """Build a graph linking one design task to every structured requirement."""
    graph = DesignGraph()
    graph.add_node(
        "design_task",
        "DesignTask",
        requirement.title,
        attributes={"objective": requirement.objective},
        source="user",
        status="parsed",
    )
    ignored = {"title", "objective", "assumptions", "unresolved_requirements"}
    for field_name, field_value in requirement:
        if field_name in ignored:
            continue
        node_id = f"requirement_{field_name}"
        graph.add_node(
            node_id,
            "Requirement",
            field_name,
            attributes=field_value.model_dump(mode="json"),
            source=field_value.source,
            status="resolved" if field_value.value is not None else "unresolved",
        )
        graph.add_edge("design_task", node_id, "has_requirement")
    for index, unresolved in enumerate(requirement.unresolved_requirements, start=1):
        node_id = f"requirement_unresolved_{index}"
        graph.add_node(
            node_id,
            "Requirement",
            unresolved,
            attributes={"value": None},
            source="inferred",
            status="unresolved",
        )
        graph.add_edge("design_task", node_id, "has_requirement")
    return graph
