"""Tests for honest blocked/provisional statuses and geometry validation."""

from gearen.cad.assembly import build_gearbox_assembly
from gearen.calculations import derive_operating_parameters
from gearen.candidate_search import generate_candidates, select_candidate
from gearen.design_graph import build_requirement_graph
from gearen.grammar_rules import apply_graph_grammar
from gearen.layout import SingleStageLayoutSolver
from gearen.requirement_parser import RuleBasedRequirementParser
from gearen.requirement_validator import validate_requirement
from gearen.validation import validate_design


def test_validation_passes_structure_but_blocks_unavailable_life_check() -> None:
    """Distinguish valid concept geometry from unavailable industrial checks."""
    requirement = RuleBasedRequirementParser().parse(
        "单级圆柱齿轮减速器，功率10kW，传动比3，输入转速1440rpm"
    )
    review = validate_requirement(requirement)
    requirement_graph = build_requirement_graph(requirement)
    graph, _ = apply_graph_grammar(requirement_graph, requirement)
    operating = derive_operating_parameters(requirement)
    candidate = select_candidate(generate_candidates(operating))
    graph.update_node(
        "pinion",
        geometry_parameters={
            "module_mm": candidate.module_mm,
            "pressure_angle_deg": candidate.pressure_angle_deg,
        },
    )
    graph.update_node(
        "gear_wheel",
        geometry_parameters={
            "module_mm": candidate.module_mm,
            "pressure_angle_deg": candidate.pressure_angle_deg,
        },
    )
    layout = SingleStageLayoutSolver().solve(
        candidate, operating, life_data_available=False
    )
    _, parts = build_gearbox_assembly(candidate, layout)
    report = validate_design(
        requirement, review, graph, candidate, layout, parts
    )
    assert report.summary.get("failed", 0) == 0
    assert report.summary["blocked"] >= 1
    bearing_life = next(
        item for item in report.checks if item.check_id == "bearing_life"
    )
    assert bearing_life.status == "blocked"

