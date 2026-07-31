"""Tests for deterministic parallel-shaft layout and catalog selections."""

import pytest

from gearen.calculations import derive_operating_parameters
from gearen.candidate_search import generate_candidates, select_candidate
from gearen.layout import SingleStageLayoutSolver
from gearen.requirement_parser import RuleBasedRequirementParser


def _layout():
    requirement = RuleBasedRequirementParser().parse(
        "单级圆柱齿轮减速器，功率10kW，传动比3，输入转速1440rpm"
    )
    operating = derive_operating_parameters(requirement)
    candidate = select_candidate(generate_candidates(operating))
    return candidate, SingleStageLayoutSolver().solve(
        candidate, operating, life_data_available=False
    )


def test_parallel_shaft_coordinates_and_gear_alignment() -> None:
    """Use X as both shaft axes and Y as exact centre-distance direction."""
    candidate, layout = _layout()
    input_shaft = layout.placement("input_shaft")
    output_shaft = layout.placement("output_shaft")
    pinion = layout.placement("pinion")
    wheel = layout.placement("gear_wheel")
    assert input_shaft.axis == output_shaft.axis == (1, 0, 0)
    assert output_shaft.origin[1] == pytest.approx(candidate.centre_distance_mm)
    assert pinion.origin[0] == wheel.origin[0]


def test_bearings_straddle_gears_and_life_is_blocked() -> None:
    """Place two supports around each gear and expose missing life inputs."""
    _, layout = _layout()
    for prefix in ("input", "output"):
        left = layout.placement(f"{prefix}_bearing_left")
        right = layout.placement(f"{prefix}_bearing_right")
        gear = layout.placement("pinion" if prefix == "input" else "gear_wheel")
        assert left.origin[0] < gear.origin[0] < right.origin[0]
    assert all(item.life_check_status == "blocked" for item in layout.bearings)

