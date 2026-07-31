"""Tests for requirement graph and fixed topology grammar."""

import json

from gearen.design_graph import build_requirement_graph
from gearen.grammar_rules import apply_graph_grammar
from gearen.requirement_parser import RuleBasedRequirementParser


TEXT = "设计一个单级圆柱齿轮减速器，功率10kW，传动比3，输入转速1440rpm"


def _graphs():
    requirement = RuleBasedRequirementParser().parse(TEXT)
    requirement_graph = build_requirement_graph(requirement)
    product_graph, results = apply_graph_grammar(requirement_graph, requirement)
    return requirement_graph, product_graph, results


def test_requirement_graph_is_serializable() -> None:
    """Represent the task and its structured fields without CAD objects."""
    requirement_graph, _, _ = _graphs()
    assert len(requirement_graph.nodes_by_type("DesignTask")) == 1
    assert len(requirement_graph.nodes_by_type("Requirement")) >= 13
    assert not requirement_graph.validate_basic_structure()
    json.dumps(requirement_graph.to_dict())


def test_product_graph_has_complete_topology() -> None:
    """Generate the exact component counts required by the MVP."""
    _, graph, results = _graphs()
    assert len(results) == 10
    assert len(graph.nodes_by_type("InputShaft")) == 1
    assert len(graph.nodes_by_type("OutputShaft")) == 1
    assert len(graph.nodes_by_type("Pinion")) == 1
    assert len(graph.nodes_by_type("GearWheel")) == 1
    assert len(graph.nodes_by_type("GearMesh")) == 1
    assert len(graph.nodes_by_type("Bearing")) == 4
    assert len(graph.nodes_by_type("Key")) == 1
    assert len(graph.edges_by_type("transmits_power_to")) == 3
    assert graph.node("gearbox")["status"] == "topology_complete"


def test_graph_exports_json_and_graphml(tmp_path) -> None:
    """Write both required graph interchange formats."""
    requirement_graph, product_graph, _ = _graphs()
    json_path = tmp_path / "requirement_graph.json"
    graphml_path = tmp_path / "product_graph.graphml"
    requirement_graph.export_json(json_path)
    product_graph.export_graphml(graphml_path)
    assert json_path.stat().st_size > 0
    assert graphml_path.stat().st_size > 0
