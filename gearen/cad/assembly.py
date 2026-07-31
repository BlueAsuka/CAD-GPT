"""Build, name, and export the deterministic CadQuery gearbox assembly."""

from __future__ import annotations

from pathlib import Path

import cadquery as cq

from gearen.cad.bearing import build_simplified_bearing
from gearen.cad.gear import GearParameters, build_simplified_spur_gear
from gearen.cad.housing import (
    HousingParameters,
    build_housing_cover,
    build_lower_housing,
)
from gearen.cad.key import build_parallel_key
from gearen.cad.shaft import build_stepped_shaft
from gearen.models import GearCandidate, LayoutResult, ShaftDesign


PART_ORDER = (
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
)


def build_gearbox_parts(
    candidate: GearCandidate, layout: LayoutResult
) -> dict[str, cq.Workplane]:
    """Build every stable-name part in its global assembly position."""
    parts: dict[str, cq.Workplane] = {}
    input_bore = _gear_seat_diameter(layout.input_shaft)
    output_bore = _gear_seat_diameter(layout.output_shaft)
    parts["pinion"] = _translated(
        build_simplified_spur_gear(
            GearParameters(
                module_mm=candidate.module_mm,
                teeth=candidate.z1,
                face_width_mm=candidate.face_width_mm,
                bore_diameter_mm=input_bore,
            )
        ),
        layout.placement("pinion").origin,
    )
    parts["gear_wheel"] = _translated(
        build_simplified_spur_gear(
            GearParameters(
                module_mm=candidate.module_mm,
                teeth=candidate.z2,
                face_width_mm=candidate.face_width_mm,
                bore_diameter_mm=output_bore,
            )
        ),
        layout.placement("gear_wheel").origin,
    )
    parts["input_shaft"] = _translated(
        build_stepped_shaft(layout.input_shaft),
        layout.placement("input_shaft").origin,
    )
    parts["output_shaft"] = _translated(
        build_stepped_shaft(layout.output_shaft),
        layout.placement("output_shaft").origin,
    )
    for bearing in layout.bearings:
        parts[bearing.component_id] = _translated(
            build_simplified_bearing(bearing),
            layout.placement(bearing.component_id).origin,
        )
    parts["output_key"] = _translated(
        build_parallel_key(layout.output_key),
        layout.placement("output_key").origin,
    )
    parts.update(_housing_parts(candidate, layout))
    return parts


def _gear_seat_diameter(shaft: ShaftDesign) -> float:
    """Return the explicitly named gear-seat diameter from a shaft design."""
    for segment in shaft.segments:
        if segment.name == "gear_seat":
            return segment.diameter_mm
    raise ValueError(f"{shaft.component_id} has no gear_seat segment")


def _housing_parts(
    candidate: GearCandidate, layout: LayoutResult
) -> dict[str, cq.Workplane]:
    """Build both housing halves in shared global coordinates."""
    envelope = layout.placement("housing_lower").estimated_bounding_box
    bearing_map = {item.component_id: item for item in layout.bearings}
    parameters = HousingParameters(
        length_mm=envelope[0],
        width_mm=envelope[1],
        height_mm=envelope[2],
        centre_distance_mm=candidate.centre_distance_mm,
        input_seat_diameter_mm=max(
            bearing_map["input_bearing_left"].outer_diameter_mm,
            bearing_map["input_bearing_right"].outer_diameter_mm,
        )
        + 4.0,
        output_seat_diameter_mm=max(
            bearing_map["output_bearing_left"].outer_diameter_mm,
            bearing_map["output_bearing_right"].outer_diameter_mm,
        )
        + 4.0,
    )
    return {
        "housing_lower": build_lower_housing(parameters),
        "housing_cover": build_housing_cover(parameters),
    }


def _translated(
    part: cq.Workplane, origin: tuple[float, float, float]
) -> cq.Workplane:
    """Translate a local builder result to its solved global origin."""
    return part.translate(origin)


def build_gearbox_assembly(
    candidate: GearCandidate, layout: LayoutResult
) -> tuple[cq.Assembly, dict[str, cq.Workplane]]:
    """Build a named CadQuery assembly and return it with its reusable parts."""
    parts = build_gearbox_parts(candidate, layout)
    assembly = cq.Assembly(name="gearbox_assembly")
    colors = {
        "pinion": cq.Color(0.88, 0.65, 0.12),
        "gear_wheel": cq.Color(0.95, 0.75, 0.20),
        "input_shaft": cq.Color(0.55, 0.58, 0.62),
        "output_shaft": cq.Color(0.55, 0.58, 0.62),
        "housing_lower": cq.Color(0.25, 0.45, 0.65, 0.65),
        "housing_cover": cq.Color(0.35, 0.58, 0.78, 0.45),
    }
    for name in PART_ORDER:
        default_color = cq.Color(0.35, 0.35, 0.38)
        assembly.add(parts[name], name=name, color=colors.get(name, default_color))
    return assembly, parts


def export_parts(parts: dict[str, cq.Workplane], output_dir: Path) -> list[Path]:
    """Export every stable-name part as an individual STEP file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name in PART_ORDER:
        path = output_dir / f"{name}.step"
        cq.exporters.export(parts[name], str(path))
        paths.append(path)
    return paths


def export_assembly(
    assembly: cq.Assembly,
    parts: dict[str, cq.Workplane],
    output_dir: Path,
) -> list[Path]:
    """Export named assembly STEP and a merged visualisation STL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    step_path = output_dir / "gearbox_assembly.step"
    stl_path = output_dir / "gearbox_assembly.stl"
    assembly.export(str(step_path))
    shapes = [parts[name].val() for name in PART_ORDER]
    merged = cq.Compound.makeCompound(shapes)
    cq.exporters.export(merged, str(stl_path), tolerance=0.1, angularTolerance=0.2)
    return [step_path, stl_path]


def export_all(
    candidate: GearCandidate, layout: LayoutResult, output_dir: Path
) -> tuple[cq.Assembly, dict[str, cq.Workplane], list[Path]]:
    """Build once and export all individual and assembly CAD artifacts."""
    assembly, parts = build_gearbox_assembly(candidate, layout)
    files = export_parts(parts, output_dir)
    files.extend(export_assembly(assembly, parts, output_dir))
    return assembly, parts, files
