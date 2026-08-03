"""Graph-driven single-stage spur gearbox demo using CadQuery.

Purpose
-------
Demonstrate a small Graph -> layout solver -> CAD generator -> STEP assembly
pipeline. The graph contains fully specified component parameters and semantic
relations such as ``mounted_on``, ``meshes_with`` and ``supports``.

The spur gear teeth are intentionally simplified trapezoidal teeth. Replace
``build_spur_gear`` with an involute-gear generator before engineering use.

Install
-------
    pip install cadquery

Run
---
    python graph_to_cad_gearbox.py

Outputs
-------
    output/single_stage_gearbox.step
    output/parts/*.step
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import cadquery as cq


# ---------------------------------------------------------------------------
# 1. INPUT GRAPH
# ---------------------------------------------------------------------------
# Positions are deliberately NOT assigned to most components. They are inferred
# from graph relations:
#   - meshes_with: computes the shaft centre distance
#   - mounted_on: inherits the shaft axis and uses an axial position
#   - supports: inherits the shaft axis and uses a bearing axial position
GEARBOX_GRAPH: dict[str, Any] = {
    "graph_id": "single_stage_spur_gearbox_v1",
    "units": "mm",
    "nodes": [
        {
            "id": "shaft_input",
            "type": "shaft",
            "parameters": {"diameter": 24.0, "length": 220.0},
        },
        {
            "id": "shaft_output",
            "type": "shaft",
            "parameters": {"diameter": 36.0, "length": 220.0},
        },
        {
            "id": "gear_pinion",
            "type": "spur_gear",
            "parameters": {
                "module": 2.5,
                "teeth": 20,
                "face_width": 28.0,
                "bore": 24.2,
            },
        },
        {
            "id": "gear_wheel",
            "type": "spur_gear",
            "parameters": {
                "module": 2.5,
                "teeth": 60,
                "face_width": 28.0,
                "bore": 36.2,
            },
        },
        {
            "id": "bearing_input_left",
            "type": "bearing",
            "parameters": {"inner_diameter": 24.2, "outer_diameter": 52.0, "width": 15.0},
        },
        {
            "id": "bearing_input_right",
            "type": "bearing",
            "parameters": {"inner_diameter": 24.2, "outer_diameter": 52.0, "width": 15.0},
        },
        {
            "id": "bearing_output_left",
            "type": "bearing",
            "parameters": {"inner_diameter": 36.2, "outer_diameter": 72.0, "width": 17.0},
        },
        {
            "id": "bearing_output_right",
            "type": "bearing",
            "parameters": {"inner_diameter": 36.2, "outer_diameter": 72.0, "width": 17.0},
        },
        {
            "id": "housing_lower",
            "type": "housing_lower",
            "parameters": {
                "wall": 10.0,
                "bottom": 12.0,
                "gear_clearance": 14.0,
                "axial_clearance": 20.0,
            },
        },
        {
            "id": "housing_lid",
            "type": "housing_lid",
            "parameters": {"thickness": 10.0},
        },
    ],
    "edges": [
        {
            "source": "gear_pinion",
            "target": "shaft_input",
            "relation": "mounted_on",
            "attributes": {"axial_position": 0.0},
        },
        {
            "source": "gear_wheel",
            "target": "shaft_output",
            "relation": "mounted_on",
            "attributes": {"axial_position": 0.0},
        },
        {
            "source": "gear_pinion",
            "target": "gear_wheel",
            "relation": "meshes_with",
            "attributes": {"backlash": 0.15},
        },
        {
            "source": "shaft_input",
            "target": "shaft_output",
            "relation": "parallel_to",
            "attributes": {},
        },
        {
            "source": "bearing_input_left",
            "target": "shaft_input",
            "relation": "supports",
            "attributes": {"axial_position": -72.0},
        },
        {
            "source": "bearing_input_right",
            "target": "shaft_input",
            "relation": "supports",
            "attributes": {"axial_position": 72.0},
        },
        {
            "source": "bearing_output_left",
            "target": "shaft_output",
            "relation": "supports",
            "attributes": {"axial_position": -72.0},
        },
        {
            "source": "bearing_output_right",
            "target": "shaft_output",
            "relation": "supports",
            "attributes": {"axial_position": 72.0},
        },
    ],
}


# ---------------------------------------------------------------------------
# 2. INTERNAL CAD-COMPILER DATA STRUCTURES
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Pose:
    """Rigid placement for this demo.

    All rotating components use the global X-axis as their rotational axis.
    x is therefore the axial coordinate; y/z locate the shaft axis.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rotation_x_deg: float = 0.0


@dataclass
class CompiledPart:
    node_id: str
    node_type: str
    shape: cq.Workplane
    pose: Pose


@dataclass(frozen=True)
class HousingEnvelope:
    length_x: float
    width_y: float
    height_z: float
    center_y: float
    center_z: float
    top_z: float
    shaft_hole_diameter: float
    shaft_axis_ys_world: tuple[float, ...]


# ---------------------------------------------------------------------------
# 3. GRAPH UTILITIES AND VALIDATION
# ---------------------------------------------------------------------------
def index_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = {node["id"]: node for node in graph["nodes"]}
    if len(nodes) != len(graph["nodes"]):
        raise ValueError("Node IDs must be unique.")
    return nodes


def edges_of(graph: dict[str, Any], relation: str) -> list[dict[str, Any]]:
    return [edge for edge in graph["edges"] if edge["relation"] == relation]


def validate_graph(graph: dict[str, Any]) -> None:
    nodes = index_nodes(graph)

    for edge in graph["edges"]:
        if edge["source"] not in nodes or edge["target"] not in nodes:
            raise ValueError(f"Edge references an unknown node: {edge}")

    mesh_edges = edges_of(graph, "meshes_with")
    if len(mesh_edges) != 1:
        raise ValueError("This demo requires exactly one gear mesh.")

    gear_a = nodes[mesh_edges[0]["source"]]
    gear_b = nodes[mesh_edges[0]["target"]]
    if gear_a["type"] != "spur_gear" or gear_b["type"] != "spur_gear":
        raise ValueError("meshes_with must connect two spur gears.")

    module_a = float(gear_a["parameters"]["module"])
    module_b = float(gear_b["parameters"]["module"])
    if not math.isclose(module_a, module_b, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("Meshing spur gears must have the same module.")


# ---------------------------------------------------------------------------
# 4. GRAPH RELATION -> ASSEMBLY LAYOUT
# ---------------------------------------------------------------------------
def gear_pitch_radius(node: dict[str, Any]) -> float:
    p = node["parameters"]
    return float(p["module"]) * int(p["teeth"]) / 2.0


def gear_outer_radius(node: dict[str, Any]) -> float:
    p = node["parameters"]
    return float(p["module"]) * (int(p["teeth"]) + 2) / 2.0


def solve_layout(
    graph: dict[str, Any],
) -> tuple[dict[str, Pose], HousingEnvelope]:
    """Resolve semantic graph edges into deterministic component poses."""

    nodes = index_nodes(graph)
    poses: dict[str, Pose] = {}

    # A. The input shaft is the datum axis.
    poses["shaft_input"] = Pose(x=0.0, y=0.0, z=0.0)

    # B. meshes_with determines centre distance and therefore output-shaft axis.
    mesh = edges_of(graph, "meshes_with")[0]
    gear_a = nodes[mesh["source"]]
    gear_b = nodes[mesh["target"]]
    backlash = float(mesh.get("attributes", {}).get("backlash", 0.0))
    centre_distance = gear_pitch_radius(gear_a) + gear_pitch_radius(gear_b) + backlash
    poses["shaft_output"] = Pose(x=0.0, y=centre_distance, z=0.0)

    # C. mounted_on makes each gear inherit its shaft axis.
    for edge in edges_of(graph, "mounted_on"):
        gear_id = edge["source"]
        shaft_id = edge["target"]
        shaft_pose = poses[shaft_id]
        axial_x = float(edge.get("attributes", {}).get("axial_position", 0.0))

        # Rotate the wheel by half a tooth pitch to avoid tooth-tip coincidence in
        # this simplified tooth model. A production solver would calculate exact
        # phase from involute contact geometry.
        phase = 0.0
        if gear_id == mesh["target"]:
            tooth_count = int(nodes[gear_id]["parameters"]["teeth"])
            phase = 180.0 / tooth_count

        poses[gear_id] = Pose(
            x=axial_x,
            y=shaft_pose.y,
            z=shaft_pose.z,
            rotation_x_deg=phase,
        )

    # D. supports makes each bearing inherit the supported shaft axis.
    for edge in edges_of(graph, "supports"):
        bearing_id = edge["source"]
        shaft_id = edge["target"]
        shaft_pose = poses[shaft_id]
        axial_x = float(edge["attributes"]["axial_position"])
        poses[bearing_id] = Pose(x=axial_x, y=shaft_pose.y, z=shaft_pose.z)

    # E. Compute a housing envelope from gear and bearing extents.
    gear_ids = [node_id for node_id, node in nodes.items() if node["type"] == "spur_gear"]
    min_y = min(poses[g].y - gear_outer_radius(nodes[g]) for g in gear_ids)
    max_y = max(poses[g].y + gear_outer_radius(nodes[g]) for g in gear_ids)
    max_r = max(gear_outer_radius(nodes[g]) for g in gear_ids)

    housing_node = nodes["housing_lower"]
    hp = housing_node["parameters"]
    clearance = float(hp["gear_clearance"])
    axial_clearance = float(hp["axial_clearance"])
    wall = float(hp["wall"])

    bearing_extents = [
        abs(poses[node_id].x) + float(node["parameters"]["width"]) / 2.0
        for node_id, node in nodes.items()
        if node["type"] == "bearing"
    ]
    max_axial_extent = max(bearing_extents)

    length_x = 2.0 * (max_axial_extent + axial_clearance + wall)
    width_y = (max_y - min_y) + 2.0 * (clearance + wall)
    height_z = 2.0 * (max_r + clearance + wall)
    center_y = (min_y + max_y) / 2.0
    center_z = 0.0
    top_z = center_z + height_z / 2.0

    max_bearing_od = max(
        float(node["parameters"]["outer_diameter"])
        for node in nodes.values()
        if node["type"] == "bearing"
    )

    envelope = HousingEnvelope(
        length_x=length_x,
        width_y=width_y,
        height_z=height_z,
        center_y=center_y,
        center_z=center_z,
        top_z=top_z,
        shaft_hole_diameter=max_bearing_od + 4.0,
        shaft_axis_ys_world=(poses["shaft_input"].y, poses["shaft_output"].y),
    )

    poses["housing_lower"] = Pose(y=center_y, z=center_z)
    lid_thickness = float(nodes["housing_lid"]["parameters"]["thickness"])
    poses["housing_lid"] = Pose(y=center_y, z=top_z + lid_thickness / 2.0)

    return poses, envelope


# ---------------------------------------------------------------------------
# 5. PARAMETRIC CAD GENERATORS
# ---------------------------------------------------------------------------
def along_x_cylinder(diameter: float, length: float) -> cq.Workplane:
    """Create a cylinder centred at x=0, with its axis along global X."""
    return (
        cq.Workplane("YZ")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((-length / 2.0, 0.0, 0.0))
    )


def build_shaft(parameters: dict[str, Any], _: HousingEnvelope) -> cq.Workplane:
    diameter = float(parameters["diameter"])
    length = float(parameters["length"])
    shaft = along_x_cylinder(diameter, length)

    # Small end chamfers. If an installed CadQuery/OCCT build rejects this
    # selection, remove the two chamfer calls without affecting the graph logic.
    try:
        shaft = shaft.edges("%Circle").chamfer(1.0)
    except Exception:
        pass
    return shaft


def polar_point(radius: float, angle_rad: float) -> tuple[float, float]:
    """Return coordinates in the local YZ sketch plane."""
    return radius * math.cos(angle_rad), radius * math.sin(angle_rad)


def build_spur_gear(parameters: dict[str, Any], _: HousingEnvelope) -> cq.Workplane:
    """Build a simplified toothed wheel without external gear libraries."""
    module = float(parameters["module"])
    teeth = int(parameters["teeth"])
    face_width = float(parameters["face_width"])
    bore = float(parameters["bore"])

    pitch_radius = module * teeth / 2.0
    outer_radius = pitch_radius + module
    root_radius = max(pitch_radius - 1.25 * module, bore / 2.0 + 2.0)

    gear = along_x_cylinder(2.0 * root_radius, face_width)

    tooth_pitch = 2.0 * math.pi / teeth
    root_half_angle = 0.34 * tooth_pitch
    tip_half_angle = 0.16 * tooth_pitch

    for tooth_index in range(teeth):
        theta = tooth_index * tooth_pitch
        polygon = [
            polar_point(root_radius, theta - root_half_angle),
            polar_point(outer_radius, theta - tip_half_angle),
            polar_point(outer_radius, theta + tip_half_angle),
            polar_point(root_radius, theta + root_half_angle),
        ]
        tooth = (
            cq.Workplane("YZ")
            .polyline(polygon)
            .close()
            .extrude(face_width)
            .translate((-face_width / 2.0, 0.0, 0.0))
        )
        gear = gear.union(tooth)

    bore_tool = along_x_cylinder(bore, face_width + 4.0)
    return gear.cut(bore_tool)


def build_bearing(parameters: dict[str, Any], _: HousingEnvelope) -> cq.Workplane:
    inner_d = float(parameters["inner_diameter"])
    outer_d = float(parameters["outer_diameter"])
    width = float(parameters["width"])
    outer = along_x_cylinder(outer_d, width)
    inner = along_x_cylinder(inner_d, width + 2.0)
    return outer.cut(inner)


def build_housing_lower(
    parameters: dict[str, Any], envelope: HousingEnvelope
) -> cq.Workplane:
    wall = float(parameters["wall"])
    bottom = float(parameters["bottom"])

    outer = cq.Workplane("XY").box(
        envelope.length_x,
        envelope.width_y,
        envelope.height_z,
        centered=(True, True, True),
    )

    # Open-top cavity, retaining the bottom and four walls.
    inner_h = envelope.height_z - bottom + 20.0
    outer_bottom_z = -envelope.height_z / 2.0
    inner_center_z = outer_bottom_z + bottom + inner_h / 2.0
    inner = (
        cq.Workplane("XY")
        .box(
            envelope.length_x - 2.0 * wall,
            envelope.width_y - 2.0 * wall,
            inner_h,
            centered=(True, True, True),
        )
        .translate((0.0, 0.0, inner_center_z))
    )
    housing = outer.cut(inner)

    # Two large side openings along X. Their Y offsets are applied later by
    # creating cutters in the housing-local coordinate frame.
    shaft_axis_ys_local = [
        y_world - envelope.center_y
        for y_world in envelope.shaft_axis_ys_world
    ]
    for shaft_y_local in shaft_axis_ys_local:
        cutter = along_x_cylinder(
            envelope.shaft_hole_diameter,
            envelope.length_x + 4.0,
        ).translate((0.0, shaft_y_local, 0.0))
        housing = housing.cut(cutter)

    return housing


def build_housing_lid(
    parameters: dict[str, Any], envelope: HousingEnvelope
) -> cq.Workplane:
    thickness = float(parameters["thickness"])
    lid = cq.Workplane("XY").box(
        envelope.length_x,
        envelope.width_y,
        thickness,
        centered=(True, True, True),
    )

    # Four simple mounting holes.
    hole_offset_x = envelope.length_x / 2.0 - 18.0
    hole_offset_y = envelope.width_y / 2.0 - 18.0
    hole_points = [
        (-hole_offset_x, -hole_offset_y),
        (-hole_offset_x, hole_offset_y),
        (hole_offset_x, -hole_offset_y),
        (hole_offset_x, hole_offset_y),
    ]
    return lid.faces(">Z").workplane().pushPoints(hole_points).hole(8.0)


Generator = Callable[[dict[str, Any], HousingEnvelope], cq.Workplane]
GENERATOR_REGISTRY: dict[str, Generator] = {
    "shaft": build_shaft,
    "spur_gear": build_spur_gear,
    "bearing": build_bearing,
    "housing_lower": build_housing_lower,
    "housing_lid": build_housing_lid,
}


# ---------------------------------------------------------------------------
# 6. CAD CORE: GENERATE, PLACE, ASSEMBLE AND EXPORT
# ---------------------------------------------------------------------------
def apply_pose(shape: cq.Workplane, pose: Pose) -> cq.Workplane:
    placed = shape
    if pose.rotation_x_deg:
        placed = placed.rotate(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            pose.rotation_x_deg,
        )
    return placed.translate((pose.x, pose.y, pose.z))


def compile_graph_to_cad(
    graph: dict[str, Any],
) -> tuple[cq.Assembly, dict[str, CompiledPart]]:
    validate_graph(graph)
    nodes = index_nodes(graph)
    poses, envelope = solve_layout(graph)

    parts: dict[str, CompiledPart] = {}
    assembly = cq.Assembly(name=graph["graph_id"])

    colors = {
        "shaft": cq.Color(0.55, 0.58, 0.62),
        "spur_gear": cq.Color(0.90, 0.67, 0.18),
        "bearing": cq.Color(0.25, 0.28, 0.32),
        "housing_lower": cq.Color(0.25, 0.48, 0.72),
        "housing_lid": cq.Color(0.38, 0.62, 0.82),
    }

    for node in graph["nodes"]:
        node_id = node["id"]
        node_type = node["type"]

        if node_type not in GENERATOR_REGISTRY:
            raise KeyError(f"No CAD generator registered for type: {node_type}")
        if node_id not in poses:
            raise KeyError(f"Layout solver produced no pose for: {node_id}")

        local_shape = GENERATOR_REGISTRY[node_type](node["parameters"], envelope)
        world_shape = apply_pose(local_shape, poses[node_id])

        compiled = CompiledPart(
            node_id=node_id,
            node_type=node_type,
            shape=world_shape,
            pose=poses[node_id],
        )
        parts[node_id] = compiled
        assembly.add(
            world_shape,
            name=node_id,
            color=colors[node_type],
        )

    return assembly, parts


def export_results(
    assembly: cq.Assembly,
    parts: dict[str, CompiledPart],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    parts_dir = output_dir / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    # Assembly STEP preserves the component structure and colors supported by
    # CadQuery's assembly exporter.
    assembly.export(str(output_dir / "single_stage_gearbox.step"))

    for part in parts.values():
        cq.exporters.export(
            part.shape,
            str(parts_dir / f"{part.node_id}.step"),
        )


def print_compilation_summary(
    graph: dict[str, Any], parts: dict[str, CompiledPart]
) -> None:
    nodes = index_nodes(graph)
    pinion = nodes["gear_pinion"]
    wheel = nodes["gear_wheel"]
    ratio = wheel["parameters"]["teeth"] / pinion["parameters"]["teeth"]

    print(f"Graph: {graph['graph_id']}")
    print(f"Transmission ratio: {ratio:.3f}:1")
    print("Resolved component poses:")
    for node_id, part in parts.items():
        p = part.pose
        print(
            f"  {node_id:24s} type={part.node_type:14s} "
            f"position=({p.x:7.2f}, {p.y:7.2f}, {p.z:7.2f}) mm "
            f"rotation_x={p.rotation_x_deg:7.2f} deg"
        )


if __name__ == "__main__":
    output_dir = Path(__file__).resolve().parent / "output"

    assembly, compiled_parts = compile_graph_to_cad(GEARBOX_GRAPH)
    export_results(assembly, compiled_parts, output_dir)
    print_compilation_summary(GEARBOX_GRAPH, compiled_parts)

    # Also save the exact input graph beside the CAD output for traceability.
    with (output_dir / "gearbox_graph.json").open("w", encoding="utf-8") as file:
        json.dump(GEARBOX_GRAPH, file, ensure_ascii=False, indent=2)

    print(f"\nExported to: {output_dir}")
