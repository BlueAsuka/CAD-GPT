"""Tests for standard-module loading and transparent candidate ranking."""

from gearen.calculations import derive_operating_parameters
from gearen.candidate_search import (
    generate_candidates,
    load_standard_modules,
    select_candidate,
)
from gearen.requirement_parser import RuleBasedRequirementParser


def _operating():
    requirement = RuleBasedRequirementParser().parse(
        "单级圆柱齿轮减速器，功率10kW，传动比3，输入转速1440rpm"
    )
    return derive_operating_parameters(requirement)


def test_standard_modules_are_read_from_data() -> None:
    """Load the documented catalog rather than a hard-coded sole result."""
    modules = load_standard_modules()
    assert modules == [1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6]


def test_candidate_search_enumerates_and_ranks() -> None:
    """Find multiple valid tooth/module/width combinations."""
    candidates = generate_candidates(_operating())
    assert len(candidates) > 100
    selected = select_candidate(candidates)
    assert 18 <= selected.z1 <= 40
    assert selected.z1 < selected.z2 <= 160
    assert selected.ratio_error <= 0.01
    assert selected.status == "provisional"

