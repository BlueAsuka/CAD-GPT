"""Tests for actual CadQuery shapes, assembly naming, and STEP export."""

import cadquery as cq

from gearen.cad.assembly import build_gearbox_assembly, export_parts
from gearen.cad.gear import GearParameters, build_simplified_spur_gear
from gearen.calculations import derive_operating_parameters
from gearen.candidate_search import generate_candidates, select_candidate
from gearen.layout import SingleStageLayoutSolver
from gearen.requirement_parser import RuleBasedRequirementParser


def _candidate_and_layout():
    requirement = RuleBasedRequirementParser().parse(
        "单级圆柱齿轮减速器，功率10kW，传动比3，输入转速1440rpm"
    )
    operating = derive_operating_parameters(requirement)
    candidate = select_candidate(generate_candidates(operating))
    layout = SingleStageLayoutSolver().solve(
        candidate, operating, life_data_available=False
    )
    return candidate, layout


def test_simplified_gear_is_valid_nonempty_shape() -> None:
    """Return a real CadQuery solid with positive bounds."""
    gear = build_simplified_spur_gear(
        GearParameters(
            module_mm=2,
            teeth=20,
            face_width_mm=20,
            bore_diameter_mm=20,
        )
    )
    assert isinstance(gear, cq.Workplane)
    assert not gear.val().isNull()
    bounds = gear.val().BoundingBox()
    assert min(bounds.xlen, bounds.ylen, bounds.zlen) > 0


def test_assembly_has_all_stable_part_names() -> None:
    """Build every documented assembly component as a valid shape."""
    candidate, layout = _candidate_and_layout()
    assembly, parts = build_gearbox_assembly(candidate, layout)
    assert assembly.name == "gearbox_assembly"
    expected = {
        "pinion",
        "gear_wheel",
        "input_shaft",
        "output_shaft",
        "input_bearing_left",
        "input_bearing_right",
        "output_bearing_left",
        "output_bearing_right",
        "output_key",
        "housing_lower",
        "housing_cover",
    }
    assert set(parts) == expected
    assert all(not part.val().isNull() for part in parts.values())


def test_step_export(tmp_path) -> None:
    """Write actual STEP files for each major part."""
    candidate, layout = _candidate_and_layout()
    _, parts = build_gearbox_assembly(candidate, layout)
    files = export_parts(parts, tmp_path)
    assert len(files) == 11
    assert all(path.exists() and path.stat().st_size > 100 for path in files)

