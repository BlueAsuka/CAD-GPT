"""Compile the complete one-stage gearbox design graph to CadQuery CAD.

The graph is semantically complete but several secondary components have no
dimensions. This compiler uses graph constraints for the drivetrain and clearly
records the concept-model defaults used for underspecified hardware.

Install:  python -m pip install -r requirements-cadquery.txt
Run:      python complete_graph_to_cad.py
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import cadquery as cq
except ModuleNotFoundError as exc:
    raise SystemExit(
        "CadQuery is required. Run: python -m pip install -r requirements-cadquery.txt"
    ) from exc


ROOT = Path(__file__).resolve().parent
DEFAULT_GRAPH = ROOT / "example" / "graph" / "single_stage_gearbox_complete_graph.json"


@dataclass(frozen=True)
class Pose:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rx: float = 0.0


@dataclass(frozen=True)
class Design:
    center_distance: float
    housing_length: float
    housing_width: float
    lower_height: float
    upper_height: float
    center_y: float
    wall: float
    bottom: float
    clearance: float
    axes_y: dict[str, float]
    bearing_x: dict[str, float]
    bearing_od: dict[str, float]


@dataclass
class Instance:
    node_id: str
    name: str
    shape: cq.Workplane
    pose: Pose
    color: cq.Color


COLORS = {
    "housing": cq.Color(0.26, 0.52, 0.76),
    "shaft": cq.Color(0.58, 0.61, 0.65),
    "gear": cq.Color(0.92, 0.66, 0.16),
    "bearing": cq.Color(0.25, 0.28, 0.33),
    "seal": cq.Color(0.12, 0.12, 0.14),
    "gasket": cq.Color(0.72, 0.25, 0.18),
    "fastener": cq.Color(0.48, 0.50, 0.54),
    "service": cq.Color(0.80, 0.48, 0.12),
}


def properties(item: dict[str, Any]) -> dict[str, Any]:
    return item.get("properties", item.get("parameters", {}))


def nodes_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = {node["id"]: node for node in graph["nodes"]}
    if len(nodes) != len(graph["nodes"]):
        raise ValueError("Node IDs must be unique")
    return nodes


def edges(graph: dict[str, Any], relation: str) -> list[dict[str, Any]]:
    return [edge for edge in graph["edges"] if edge["relation"] == relation]


def edge_properties(edge: dict[str, Any]) -> dict[str, Any]:
    return edge.get("properties", edge.get("attributes", {}))


def validate(graph: dict[str, Any]) -> None:
    nodes = nodes_by_id(graph)
    for edge in graph["edges"]:
        if edge["source"] not in nodes or edge["target"] not in nodes:
            raise ValueError(f"Edge references an unknown node: {edge}")

    meshes = edges(graph, "meshes_with")
    if len(meshes) != 1:
        raise ValueError("Exactly one meshes_with relation is required")
    gears = [nodes[meshes[0][key]] for key in ("source", "target")]
    if any(node["type"] != "gear" for node in gears):
        raise ValueError("meshes_with must connect two gear nodes")
    modules = [float(properties(node)["module"]) for node in gears]
    if not math.isclose(*modules, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("Meshing gears must have the same module")


def pitch_radius(node: dict[str, Any]) -> float:
    p = properties(node)
    return float(p["module"]) * int(p["teeth"]) / 2.0


def outer_radius(node: dict[str, Any]) -> float:
    p = properties(node)
    return float(p["module"]) * (int(p["teeth"]) + 2) / 2.0


def mounted_shaft(graph: dict[str, Any], gear_id: str, nodes: dict[str, dict[str, Any]]) -> str:
    matches = [
        edge["target"]
        for edge in edges(graph, "mounted_on")
        if edge["source"] == gear_id and nodes[edge["target"]]["type"] == "shaft"
    ]
    if len(matches) != 1:
        raise ValueError(f"{gear_id} must be mounted on exactly one shaft")
    return matches[0]


def solve_design(graph: dict[str, Any]) -> tuple[Design, dict[str, Pose]]:
    nodes = nodes_by_id(graph)
    mesh = edges(graph, "meshes_with")[0]
    gear_a, gear_b = nodes[mesh["source"]], nodes[mesh["target"]]
    shaft_a = mounted_shaft(graph, gear_a["id"], nodes)
    shaft_b = mounted_shaft(graph, gear_b["id"], nodes)

    calculated_center = pitch_radius(gear_a) + pitch_radius(gear_b)
    center_node = nodes.get("C_center_distance")
    center = float(properties(center_node)["value"]) if center_node else calculated_center
    if not math.isclose(center, calculated_center, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError(
            f"Hard center distance {center:g} conflicts with gear geometry "
            f"({calculated_center:g} mm)"
        )

    axes_y = {shaft_a: -center / 2.0, shaft_b: center / 2.0}
    poses = {shaft_id: Pose(y=y) for shaft_id, y in axes_y.items()}

    for edge in edges(graph, "mounted_on"):
        if edge["source"] not in (gear_a["id"], gear_b["id"]):
            continue
        shaft = edge["target"]
        x = float(edge_properties(edge).get("axial_position", 0.0))
        phase = 0.0 if edge["source"] == gear_a["id"] else 180.0 / int(properties(gear_b)["teeth"])
        poses[edge["source"]] = Pose(x=x, y=axes_y[shaft], rx=phase)

    bearing_x: dict[str, float] = {}
    bearing_od: dict[str, float] = {}
    for edge in edges(graph, "supports"):
        bearing, shaft = edge["source"], edge["target"]
        x = float(edge_properties(edge)["axial_position"])
        bearing_x[bearing] = x
        bearing_od[shaft] = max(
            bearing_od.get(shaft, 0.0),
            float(properties(nodes[bearing])["outer_diameter"]),
        )
        poses[bearing] = Pose(x=x, y=axes_y[shaft])

    housing = properties(nodes["housing_lower"])
    wall = float(housing["wall"])
    bottom = float(housing["bottom"])
    clearance_node = nodes.get("C_housing_clearance")
    clearance = float(
        properties(clearance_node).get(
            "minimum_gear_clearance", housing.get("gear_clearance", 14.0)
        )
    )
    lid_wall = float(properties(nodes["housing_lid"])["thickness"])

    gear_bounds = [
        (poses[g["id"]].y - outer_radius(g), poses[g["id"]].y + outer_radius(g))
        for g in (gear_a, gear_b)
    ]
    min_y = min(bound[0] for bound in gear_bounds)
    max_y = max(bound[1] for bound in gear_bounds)
    center_y = (min_y + max_y) / 2.0
    housing_width = max_y - min_y + 2.0 * (clearance + wall)
    max_radius = max(outer_radius(gear_a), outer_radius(gear_b))

    bearing_extent = max(
        abs(bearing_x[node_id]) + float(properties(nodes[node_id])["width"]) / 2.0
        for node_id in bearing_x
    )
    housing_length = 2.0 * (bearing_extent + wall + 6.0)

    design = Design(
        center_distance=center,
        housing_length=housing_length,
        housing_width=housing_width,
        lower_height=max_radius + clearance + bottom,
        upper_height=max_radius + clearance + lid_wall,
        center_y=center_y,
        wall=wall,
        bottom=bottom,
        clearance=clearance,
        axes_y=axes_y,
        bearing_x=bearing_x,
        bearing_od=bearing_od,
    )
    poses["housing_lower"] = Pose(y=center_y)
    poses["housing_lid"] = Pose(y=center_y)
    return design, poses


def x_cylinder(diameter: float, length: float) -> cq.Workplane:
    return (
        cq.Workplane("YZ")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((-length / 2.0, 0.0, 0.0))
    )


def z_cylinder(diameter: float, length: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )


def x_tube(outer_d: float, inner_d: float, length: float) -> cq.Workplane:
    return x_cylinder(outer_d, length).cut(x_cylinder(inner_d, length + 2.0))


def parse_key_size(value: str) -> tuple[float, float]:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*", value)
    if not match:
        raise ValueError(f"Unsupported key size: {value!r}")
    return float(match.group(1)), float(match.group(2))


def metric_diameter(specification: str) -> float:
    match = re.search(r"M(\d+(?:\.\d+)?)", specification, re.IGNORECASE)
    if not match:
        raise ValueError(f"Unsupported fastener specification: {specification!r}")
    return float(match.group(1))


def place(shape: cq.Workplane, pose: Pose) -> cq.Workplane:
    if pose.rx:
        shape = shape.rotate((0, 0, 0), (1, 0, 0), pose.rx)
    return shape.translate((pose.x, pose.y, pose.z))


def build_shaft(p: dict[str, Any], key: tuple[float, float], key_length: float) -> cq.Workplane:
    diameter, length = float(p["diameter"]), float(p["length"])
    shape = x_cylinder(diameter, length)
    key_w, key_h = key
    keyway = (
        cq.Workplane("XY")
        .box(key_length + 2.0, key_w + 0.2, key_h / 2.0 + 0.2)
        .translate((0.0, 0.0, diameter / 2.0 - key_h / 4.0))
    )
    return shape.cut(keyway)


def build_gear(p: dict[str, Any], key: tuple[float, float]) -> cq.Workplane:
    module, teeth = float(p["module"]), int(p["teeth"])
    width, bore = float(p["face_width"]), float(p["bore"])
    pitch = module * teeth / 2.0
    root = max(pitch - 1.25 * module, bore / 2.0 + 2.0)
    outer = pitch + module
    points: list[tuple[float, float]] = []
    tooth_angle = 2.0 * math.pi / teeth
    for index in range(teeth):
        angle = index * tooth_angle
        for offset, radius in (
            (-0.45, root),
            (-0.22, outer),
            (0.22, outer),
            (0.45, root),
        ):
            theta = angle + offset * tooth_angle
            points.append((radius * math.cos(theta), radius * math.sin(theta)))
    shape = (
        cq.Workplane("YZ")
        .polyline(points)
        .close()
        .extrude(width)
        .translate((-width / 2.0, 0.0, 0.0))
        .cut(x_cylinder(bore, width + 2.0))
    )
    key_w, key_h = key
    keyway = (
        cq.Workplane("XY")
        .box(width + 2.0, key_w + 0.2, key_h / 2.0 + 0.4)
        .translate((0.0, 0.0, bore / 2.0 + key_h / 4.0))
    )
    return shape.cut(keyway)


def shaft_openings(shape: cq.Workplane, design: Design) -> cq.Workplane:
    for shaft_id, y_world in design.axes_y.items():
        cutter = x_cylinder(
            design.bearing_od[shaft_id] + 0.4, design.housing_length + 24.0
        ).translate((0.0, y_world - design.center_y, 0.0))
        shape = shape.cut(cutter)
    return shape


def build_housing_lower(design: Design) -> cq.Workplane:
    length, width, height = (
        design.housing_length,
        design.housing_width,
        design.lower_height,
    )
    shape = cq.Workplane("XY").box(length, width, height).translate((0, 0, -height / 2))
    flange = cq.Workplane("XY").box(length + 20, width + 20, 8).translate((0, 0, -4))
    shape = shape.union(flange)
    inner_depth = height - design.bottom
    cavity = (
        cq.Workplane("XY")
        .box(length - 2 * design.wall, width - 2 * design.wall, inner_depth + 1)
        .translate((0, 0, 0.5 - inner_depth / 2))
    )
    shape = shape.cut(cavity)

    foot_z = -height - 4.0
    foot_points = [
        (sx * (length / 2 - 28), sy * (width / 2 + 10))
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]
    for x, y in foot_points:
        foot = cq.Workplane("XY").box(44, 38, 12).translate((x, y, foot_z))
        hole = z_cylinder(12, 18).translate((x, y, foot_z))
        shape = shape.union(foot).cut(hole)
    return shaft_openings(shape, design)


def build_housing_lid(design: Design) -> cq.Workplane:
    length, width, height = (
        design.housing_length,
        design.housing_width,
        design.upper_height,
    )
    shape = cq.Workplane("XY").box(length, width, height).translate((0, 0, height / 2))
    flange = cq.Workplane("XY").box(length + 20, width + 20, 8).translate((0, 0, 4))
    shape = shape.union(flange)
    top_wall = float(height - (max(height - 10.0, 1.0)))
    inner_depth = height - top_wall
    cavity = (
        cq.Workplane("XY")
        .box(length - 2 * design.wall, width - 2 * design.wall, inner_depth + 1)
        .translate((0, 0, inner_depth / 2 - 0.5))
    )
    shape = shape.cut(cavity)
    inspection = (
        cq.Workplane("XY")
        .box(76, 62, top_wall + 4)
        .translate((0, 0, height - top_wall / 2))
    )
    return shaft_openings(shape.cut(inspection), design)


def rectangular_gasket(length: float, width: float, opening_x: float, opening_y: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(length, width, 1.0)
        .cut(cq.Workplane("XY").box(opening_x, opening_y, 2.0))
    )


def end_cover(outer_d: float, bore: float | None, thickness: float = 7.0) -> cq.Workplane:
    shape = x_cylinder(outer_d, thickness)
    if bore is not None:
        shape = shape.cut(x_cylinder(bore, thickness + 2.0))
    bolt_radius = outer_d * 0.38
    for angle in range(0, 360, 90):
        theta = math.radians(angle)
        hole = x_cylinder(6.6, thickness + 2).translate(
            (0, bolt_radius * math.cos(theta), bolt_radius * math.sin(theta))
        )
        shape = shape.cut(hole)
    return shape


def perimeter_points(length: float, width: float) -> list[tuple[float, float]]:
    xs = (-length / 2 + 18, -length / 6, length / 6, length / 2 - 18)
    ys = (-width / 2 + 18, width / 2 - 18)
    points = [(x, y) for y in ys for x in xs]
    points += [(-length / 2 + 18, -width / 6), (-length / 2 + 18, width / 6)]
    points += [(length / 2 - 18, -width / 6), (length / 2 - 18, width / 6)]
    return points


def compile_graph(
    graph: dict[str, Any],
) -> tuple[cq.Assembly, dict[str, cq.Workplane], dict[str, Any]]:
    validate(graph)
    nodes = nodes_by_id(graph)
    design, poses = solve_design(graph)
    mesh = edges(graph, "meshes_with")[0]
    gear_ids = (mesh["source"], mesh["target"])
    shaft_for_gear = {
        gear_id: mounted_shaft(graph, gear_id, nodes) for gear_id in gear_ids
    }
    key_for_gear = {
        gear_id: next(
            edge["source"]
            for edge in edges(graph, "fitted_in")
            if edge["target"] == gear_id
        )
        for gear_id in gear_ids
    }

    instances: list[Instance] = []
    unique_parts: dict[str, cq.Workplane] = {}

    def add(node_id: str, shape: cq.Workplane, pose: Pose, color: cq.Color, suffix: str = "") -> None:
        name = node_id if not suffix else f"{node_id}_{suffix}"
        instances.append(Instance(node_id, name, shape, pose, color))
        unique_parts.setdefault(node_id, shape)

    add("housing_lower", build_housing_lower(design), poses["housing_lower"], COLORS["housing"])
    add("housing_lid", build_housing_lid(design), poses["housing_lid"], COLORS["housing"])
    joint_gasket = rectangular_gasket(
        design.housing_length + 20,
        design.housing_width + 20,
        design.housing_length - 2 * design.wall,
        design.housing_width - 2 * design.wall,
    )
    add("housing_joint_gasket", joint_gasket, Pose(y=design.center_y, z=0.25), COLORS["gasket"])

    for gear_id in gear_ids:
        gear_node = nodes[gear_id]
        shaft_id = shaft_for_gear[gear_id]
        shaft_node = nodes[shaft_id]
        key_id = key_for_gear[gear_id]
        key_size = parse_key_size(properties(nodes[key_id])["size"])
        face_width = float(properties(gear_node)["face_width"])
        add(
            shaft_id,
            build_shaft(properties(shaft_node), key_size, face_width),
            poses[shaft_id],
            COLORS["shaft"],
        )
        add(gear_id, build_gear(properties(gear_node), key_size), poses[gear_id], COLORS["gear"])
        key_shape = cq.Workplane("XY").box(face_width, key_size[0], key_size[1])
        shaft_d = float(properties(shaft_node)["diameter"])
        add(
            key_id,
            key_shape,
            Pose(poses[gear_id].x, poses[gear_id].y, shaft_d / 2.0, poses[gear_id].rx),
            COLORS["fastener"],
        )

    support_edges = edges(graph, "supports")
    for edge in support_edges:
        node = nodes[edge["source"]]
        p = properties(node)
        bearing = x_tube(float(p["outer_diameter"]), float(p["bore"]), float(p["width"]))
        add(node["id"], bearing, poses[node["id"]], COLORS["bearing"])

    for gear_id in gear_ids:
        shaft_id = shaft_for_gear[gear_id]
        cluster = nodes[shaft_id]["cluster"]
        gear_p = properties(nodes[gear_id])
        gear_pose = poses[gear_id]
        right_bearing = next(
            edge["source"]
            for edge in support_edges
            if edge["target"] == shaft_id and edge_properties(edge)["axial_position"] > 0
        )
        bp = properties(nodes[right_bearing])
        gear_edge = gear_pose.x + float(gear_p["face_width"]) / 2.0
        bearing_edge = poses[right_bearing].x - float(bp["width"]) / 2.0
        spacer_length = bearing_edge - gear_edge
        shaft_d = float(properties(nodes[shaft_id])["diameter"])
        spacer_id = f"{cluster}_spacer"
        spacer = x_tube(shaft_d + 8.0, shaft_d + 0.4, spacer_length)
        add(
            spacer_id,
            spacer,
            Pose((gear_edge + bearing_edge) / 2.0, poses[shaft_id].y),
            COLORS["fastener"],
        )
        retainer_id = f"{cluster}_retainer"
        retainer = x_tube(shaft_d + 10.0, shaft_d + 0.4, 5.0)
        add(
            retainer_id,
            retainer,
            Pose(poses[right_bearing].x + float(bp["width"]) / 2.0 + 2.5, poses[shaft_id].y),
            COLORS["fastener"],
        )

        bearing_od = design.bearing_od[shaft_id]
        cover_od = bearing_od + 28.0
        through_id, blind_id = f"{cluster}_through_cover", f"{cluster}_blind_cover"
        left_x, right_x = -design.housing_length / 2.0 - 3.5, design.housing_length / 2.0 + 3.5
        add(
            through_id,
            end_cover(cover_od, shaft_d + 3.0),
            Pose(left_x, poses[shaft_id].y),
            COLORS["housing"],
        )
        add(
            blind_id,
            end_cover(cover_od, None),
            Pose(right_x, poses[shaft_id].y),
            COLORS["housing"],
        )
        seal_id = f"{cluster}_radial_seal"
        seal = x_tube(shaft_d + 18.0, shaft_d + 0.3, 7.0)
        add(seal_id, seal, Pose(left_x, poses[shaft_id].y), COLORS["seal"])

        gasket_id = f"{cluster}_cover_gasket_pattern"
        gasket = x_tube(cover_od, bearing_od + 1.0, 1.0)
        add(gasket_id, gasket, Pose(-design.housing_length / 2.0 - 0.5, poses[shaft_id].y), COLORS["gasket"], "01")
        add(gasket_id, gasket, Pose(design.housing_length / 2.0 + 0.5, poses[shaft_id].y), COLORS["gasket"], "02")

        fastener_id = f"{cluster}_cover_fastener_pattern"
        screw_d = metric_diameter(properties(nodes[fastener_id])["specification"])
        screw = x_cylinder(screw_d, 16.0)
        radius = cover_od * 0.38
        index = 1
        for x in (left_x, right_x):
            for angle in range(0, 360, 90):
                theta = math.radians(angle)
                add(
                    fastener_id,
                    screw,
                    Pose(x, poses[shaft_id].y + radius * math.cos(theta), radius * math.sin(theta)),
                    COLORS["fastener"],
                    f"{index:02d}",
                )
                index += 1

    bolt_node = nodes["housing_bolt_pattern"]
    bolt_d = metric_diameter(properties(bolt_node)["specification"])
    housing_bolt = z_cylinder(bolt_d, 22.0)
    for index, (x, y) in enumerate(
        perimeter_points(design.housing_length + 20, design.housing_width + 20), 1
    ):
        add(
            "housing_bolt_pattern",
            housing_bolt,
            Pose(x, y + design.center_y, 0),
            COLORS["fastener"],
            f"{index:02d}",
        )

    dowel_p = properties(nodes["housing_dowel_pattern"])
    dowel = z_cylinder(float(dowel_p["diameter"]), 16.0)
    for index, sign in enumerate((-1, 1), 1):
        add(
            "housing_dowel_pattern",
            dowel,
            Pose(
                sign * (design.housing_length / 2 - 30),
                design.center_y + sign * (design.housing_width / 2 - 25),
                0,
            ),
            COLORS["fastener"],
            f"{index:02d}",
        )

    inspection_z = design.upper_height + 2.5
    cover = cq.Workplane("XY").box(88, 74, 5.0)
    gasket = rectangular_gasket(86, 72, 68, 54)
    add("inspection_cover", cover, Pose(y=design.center_y, z=inspection_z), COLORS["housing"])
    add("inspection_gasket", gasket, Pose(y=design.center_y, z=design.upper_height + 0.5), COLORS["gasket"])
    inspection_screw = z_cylinder(6.0, 12.0)
    inspection_points = [(-34, -26), (0, -26), (34, -26), (-34, 26), (0, 26), (34, 26)]
    for index, (x, y) in enumerate(inspection_points, 1):
        add(
            "inspection_fastener_pattern",
            inspection_screw,
            Pose(x, design.center_y + y, design.upper_height + 3),
            COLORS["fastener"],
            f"{index:02d}",
        )

    plug = z_cylinder(12, 14)
    add("breather_plug", plug, Pose(-25, design.center_y, design.upper_height + 9), COLORS["service"])
    add("oil_fill_plug", plug, Pose(25, design.center_y, design.upper_height + 9), COLORS["service"])
    level = x_cylinder(14, 12).rotate((0, 0, 0), (0, 0, 1), 90)
    add(
        "oil_level_indicator",
        level,
        Pose(0, design.center_y + design.housing_width / 2 + 5, -design.lower_height * 0.45),
        COLORS["service"],
    )
    add(
        "drain_plug",
        plug,
        Pose(0, design.center_y, -design.lower_height - 6),
        COLORS["service"],
    )

    assembly = cq.Assembly(name=graph["graph_id"])
    for item in instances:
        assembly.add(place(item.shape, item.pose), name=item.name, color=item.color)

    compiled = set(unique_parts)
    feature_nodes = {"mounting_foot_pattern"}
    semantic_types = {"system", "assembly", "constraint", "external_interface", "lubrication_region"}
    semantic_nodes = {
        node["id"] for node in graph["nodes"] if node["type"] in semantic_types
    }
    unhandled = {
        node["id"] for node in graph["nodes"]
    } - compiled - feature_nodes - semantic_nodes
    if unhandled:
        raise ValueError(f"Unhandled physical graph nodes: {sorted(unhandled)}")

    report = {
        "graph_id": graph["graph_id"],
        "units": graph.get("units", "mm"),
        "derived_design": asdict(design),
        "compiled_nodes": sorted(compiled),
        "instance_count": len(instances),
        "realized_as_features": sorted(feature_nodes),
        "non_geometric_nodes": sorted(semantic_nodes),
        "concept_defaults": [
            "Spur teeth use a trapezoidal approximation, not an involute profile.",
            "Backlash is metadata; the hard 100 mm center-distance constraint controls layout.",
            "Cover, gasket, seal, spacer, retainer, fastener, foot, inspection, and service dimensions are derived defaults.",
            "Bearings and seals are simplified envelopes rather than catalog geometry.",
            "Threads, fillets, tolerances, fits, lubrication passages, and manufacturing details are omitted.",
        ],
    }
    return assembly, unique_parts, report


def export(
    assembly: cq.Assembly,
    parts: dict[str, cq.Workplane],
    report: dict[str, Any],
    output_dir: Path,
    write_glb: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    parts_dir = output_dir / "parts"
    parts_dir.mkdir(exist_ok=True)
    assembly.export(str(output_dir / "single_stage_gearbox_complete.step"))
    if write_glb:
        assembly.export(str(output_dir / "single_stage_gearbox_complete.glb"))
    for node_id, shape in parts.items():
        cq.exporters.export(shape, str(parts_dir / f"{node_id}.step"))
    (output_dir / "build_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", nargs="?", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "output" / "complete_gearbox")
    parser.add_argument("--glb", action="store_true", help="also export a browser-viewable GLB")
    args = parser.parse_args()

    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    assembly, parts, report = compile_graph(graph)
    export(assembly, parts, report, args.output, args.glb)
    design = report["derived_design"]
    print(f"Graph: {graph['graph_id']}")
    print(f"Center distance: {design['center_distance']:.3f} mm")
    print(f"Generated: {len(parts)} unique parts, {report['instance_count']} assembly instances")
    print(f"Output: {args.output.resolve()}")
    print("Concept defaults and skipped semantic nodes are listed in build_report.json")


if __name__ == "__main__":
    main()
