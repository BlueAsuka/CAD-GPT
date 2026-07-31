"""Transparent concept-design checks with honest engineering status labels."""

from __future__ import annotations

import math
from collections import Counter

import cadquery as cq

from gearen.calculations import calculate_centre_distance
from gearen.design_graph import DesignGraph
from gearen.models import (
    GearCandidate,
    GearboxRequirement,
    LayoutResult,
    RequirementReview,
    ValidationItem,
    ValidationReport,
)


def _check(
    check_id: str,
    category: str,
    condition: bool,
    pass_message: str,
    fail_message: str,
    **details,
) -> ValidationItem:
    """Create a passed/failed check without obscuring its boolean condition."""
    return ValidationItem(
        check_id=check_id,
        category=category,
        status="passed" if condition else "failed",
        message=pass_message if condition else fail_message,
        details=details,
    )


def _status_item(
    check_id: str, category: str, status: str, message: str
) -> ValidationItem:
    """Create a non-binary blocked, warning, or provisional check."""
    return ValidationItem(
        check_id=check_id,
        category=category,
        status=status,  # type: ignore[arg-type]
        message=message,
    )


def validate_design(
    requirement: GearboxRequirement,
    review: RequirementReview,
    product_graph: DesignGraph,
    candidate: GearCandidate,
    layout: LayoutResult,
    cad_parts: dict[str, cq.Workplane] | None = None,
) -> ValidationReport:
    """Run requirement, graph, parameter, layout, and optional geometry checks."""
    checks: list[ValidationItem] = []
    checks.extend(_requirement_checks(requirement))
    checks.extend(_graph_checks(product_graph))
    checks.extend(_parameter_checks(product_graph, candidate))
    checks.extend(_layout_checks(candidate, layout))
    if cad_parts is not None:
        checks.extend(_geometry_checks(cad_parts))
    checks.extend(_engineering_limit_checks(review, layout))

    summary = dict(Counter(item.status for item in checks))
    overall = _overall_status(summary)
    return ValidationReport(checks=checks, summary=summary, overall_status=overall)


def _requirement_checks(requirement: GearboxRequirement) -> list[ValidationItem]:
    """Check the values required by the supported design scope."""
    values = [
        ("requirement_power", requirement.transmitted_power.value is not None,
         "传递功率已提供", "缺少传递功率"),
        ("requirement_input_speed", requirement.input_speed.value is not None,
         "输入转速已提供", "缺少输入转速"),
        ("requirement_ratio", requirement.transmission_ratio.value is not None,
         "传动比已提供或计算", "缺少传动比"),
        ("requirement_single_stage", requirement.stage_count.as_float() == 1,
         "级数为单级", "级数不是单级"),
        ("requirement_cylindrical", requirement.gear_family.value == "cylindrical",
         "齿轮族为圆柱齿轮", "齿轮族不是圆柱齿轮"),
    ]
    return [
        _check(check_id, "requirement", condition, passed, failed)
        for check_id, condition, passed, failed in values
    ]


def _graph_checks(graph: DesignGraph) -> list[ValidationItem]:
    """Check component cardinality, mounting, support, key, and power path."""
    expected_counts = {
        "InputShaft": 1,
        "OutputShaft": 1,
        "Pinion": 1,
        "GearWheel": 1,
        "GearMesh": 1,
        "Bearing": 4,
        "Key": 1,
    }
    checks = [
        _check(
            f"graph_count_{node_type.lower()}",
            "graph",
            len(graph.nodes_by_type(node_type)) == count,
            f"{node_type}数量为{count}",
            f"{node_type}数量不等于{count}",
        )
        for node_type, count in expected_counts.items()
    ]
    mounted = graph.edges_by_type("mounted_on")
    supports = graph.edges_by_type("supports")
    checks.extend(
        [
            _check(
                "graph_pinion_mount",
                "graph",
                _has_edge(mounted, "pinion", "input_shaft"),
                "小齿轮安装在输入轴",
                "小齿轮缺少输入轴安装关系",
            ),
            _check(
                "graph_wheel_mount",
                "graph",
                _has_edge(mounted, "gear_wheel", "output_shaft"),
                "大齿轮安装在输出轴",
                "大齿轮缺少输出轴安装关系",
            ),
            _check(
                "graph_bearing_supports",
                "graph",
                _target_count(supports, "input_shaft") == 2
                and _target_count(supports, "output_shaft") == 2,
                "每根轴由两个轴承支持",
                "轴承支持数量不满足每轴两个",
            ),
            _check(
                "graph_output_key",
                "graph",
                _has_edge(graph.edges_by_type("keyed_to"), "output_key", "gear_wheel"),
                "输出齿轮具有键连接",
                "输出齿轮缺少键连接",
            ),
            _check(
                "graph_power_path",
                "graph",
                _power_path_exists(graph),
                "存在输入轴到输出轴的显式功率路径",
                "缺少完整功率路径",
            ),
        ]
    )
    return checks


def _has_edge(edges: list[dict], source: str, target: str) -> bool:
    """Return whether an edge list contains one source-target pair."""
    return any(e["source"] == source and e["target"] == target for e in edges)


def _target_count(edges: list[dict], target: str) -> int:
    """Count relations that point to one target component."""
    return sum(edge["target"] == target for edge in edges)


def _power_path_exists(graph: DesignGraph) -> bool:
    """Check the exact four-component MVP power path."""
    edges = graph.edges_by_type("transmits_power_to")
    return all(
        _has_edge(edges, source, target)
        for source, target in [
            ("input_shaft", "pinion"),
            ("pinion", "gear_wheel"),
            ("gear_wheel", "output_shaft"),
        ]
    )


def _parameter_checks(
    graph: DesignGraph, candidate: GearCandidate
) -> list[ValidationItem]:
    """Check ratio, common gear parameters, centre distance, loads, and sizes."""
    pinion = graph.node("pinion")["geometry_parameters"]
    wheel = graph.node("gear_wheel")["geometry_parameters"]
    calculated_centre = calculate_centre_distance(
        candidate.pitch_diameter_pinion_mm,
        candidate.pitch_diameter_wheel_mm,
    )
    finite_loads = all(
        math.isfinite(value)
        for value in [
            candidate.input_torque_Nm,
            candidate.output_torque_Nm,
            candidate.tangential_force_N,
            candidate.radial_force_N,
        ]
    )
    positive_sizes = all(
        value > 0
        for value in [
            candidate.module_mm,
            candidate.face_width_mm,
            candidate.pitch_diameter_pinion_mm,
            candidate.pitch_diameter_wheel_mm,
            candidate.centre_distance_mm,
        ]
    )
    return [
        _check("parameter_ratio", "parameter", candidate.ratio_error <= 0.01,
               "传动比误差在1%以内", "传动比误差超过1%",
               ratio_error=candidate.ratio_error),
        _check("parameter_module", "parameter",
               pinion.get("module_mm") == wheel.get("module_mm") == candidate.module_mm,
               "齿轮模数一致", "齿轮模数不一致"),
        _check("parameter_pressure_angle", "parameter",
               pinion.get("pressure_angle_deg") == wheel.get("pressure_angle_deg")
               == candidate.pressure_angle_deg,
               "压力角一致", "压力角不一致"),
        _check("parameter_centre_distance", "parameter",
               math.isclose(calculated_centre, candidate.centre_distance_mm,
                            rel_tol=1e-9, abs_tol=1e-9),
               "中心距计算一致", "中心距计算不一致"),
        _check("parameter_finite_loads", "parameter", finite_loads,
               "力和扭矩为有限值", "力或扭矩存在非有限值"),
        _check("parameter_positive_sizes", "parameter", positive_sizes,
               "主要尺寸均为正值", "存在非正主要尺寸"),
    ]


def _layout_checks(
    candidate: GearCandidate, layout: LayoutResult
) -> list[ValidationItem]:
    """Check parallel axes, shaft separation, gear alignment, and supports."""
    input_shaft = layout.placement("input_shaft")
    output_shaft = layout.placement("output_shaft")
    pinion = layout.placement("pinion")
    wheel = layout.placement("gear_wheel")
    straddles = all(
        layout.placement(f"{prefix}_bearing_left").origin[0]
        < layout.placement(gear_name).origin[0]
        < layout.placement(f"{prefix}_bearing_right").origin[0]
        for prefix, gear_name in [("input", "pinion"), ("output", "gear_wheel")]
    )
    return [
        _check("layout_parallel", "layout",
               input_shaft.axis == output_shaft.axis == (1.0, 0.0, 0.0),
               "两根轴平行于X轴", "两根轴不平行"),
        _check("layout_centre_distance", "layout",
               math.isclose(output_shaft.origin[1] - input_shaft.origin[1],
                            candidate.centre_distance_mm, abs_tol=1e-9),
               "轴间距等于齿轮中心距", "轴间距与齿轮中心距不一致"),
        _check("layout_gear_alignment", "layout",
               math.isclose(pinion.origin[0], wheel.origin[0], abs_tol=1e-9),
               "两齿轮X方向对齐", "两齿轮X方向未对齐"),
        _check("layout_bearing_sides", "layout", straddles,
               "轴承位于各自齿轮两侧", "轴承未夹持齿轮两侧"),
    ]


def _geometry_checks(parts: dict[str, cq.Workplane]) -> list[ValidationItem]:
    """Check shape existence, bounds, housing envelope, and shaft separation."""
    nonempty = True
    valid_bounds = True
    for part in parts.values():
        shape = part.val()
        nonempty &= not shape.isNull()
        box = shape.BoundingBox()
        valid_bounds &= all(
            math.isfinite(value) and value > 0
            for value in (box.xlen, box.ylen, box.zlen)
        )
    envelope_ok = _housing_encloses_parts(parts)
    shafts_separate = _intersection_volume(
        parts["input_shaft"], parts["output_shaft"]
    ) < 1e-6
    return [
        _check("geometry_nonempty", "geometry", nonempty,
               "所有CadQuery Shape非空", "存在空CadQuery Shape"),
        _check("geometry_bounds", "geometry", valid_bounds,
               "所有包围盒有效", "存在无效包围盒"),
        _check("geometry_housing_envelope", "geometry", envelope_ok,
               "箱体总包络覆盖内部零件", "箱体总包络未覆盖内部零件"),
        _check("geometry_unexpected_overlap", "geometry", shafts_separate,
               "两根平行轴无非预期实体交叠", "两根平行轴发生非预期交叠"),
    ]


def _housing_encloses_parts(parts: dict[str, cq.Workplane]) -> bool:
    """Compare combined housing bounds with gears, bearings, key, and shafts."""
    lower = parts["housing_lower"].val().BoundingBox()
    cover = parts["housing_cover"].val().BoundingBox()
    limits = (
        min(lower.xmin, cover.xmin), max(lower.xmax, cover.xmax),
        min(lower.ymin, cover.ymin), max(lower.ymax, cover.ymax),
        min(lower.zmin, cover.zmin), max(lower.zmax, cover.zmax),
    )
    for name, part in parts.items():
        if name.startswith("housing_"):
            continue
        box = part.val().BoundingBox()
        if not (
            limits[0] <= box.xmin <= box.xmax <= limits[1]
            and limits[2] <= box.ymin <= box.ymax <= limits[3]
            and limits[4] <= box.zmin <= box.zmax <= limits[5]
        ):
            return False
    return True


def _intersection_volume(first: cq.Workplane, second: cq.Workplane) -> float:
    """Return exact common volume for an obvious-overlap check."""
    common = first.val().intersect(second.val())
    return 0.0 if common.isNull() else common.Volume()


def _engineering_limit_checks(
    review: RequirementReview, layout: LayoutResult
) -> list[ValidationItem]:
    """Expose analyses intentionally absent from this concept-level MVP."""
    life_blocked = any(
        bearing.life_check_status == "blocked" for bearing in layout.bearings
    )
    return [
        _status_item(
            "bearing_life",
            "engineering_limit",
            "blocked" if life_blocked else "provisional",
            "缺少工作小时和载荷谱，轴承额定寿命校核被阻塞"
            if life_blocked
            else "轴承寿命仍需按实际载荷进行校核",
        ),
        _status_item("shaft_strength", "engineering_limit", "provisional",
                     "轴径仅按扭矩初估，尚未校核弯扭合成、疲劳和挠度"),
        _status_item("key_strength", "engineering_limit", "provisional",
                     "平键为尺寸表概念选型，尚未校核挤压和剪切"),
        _status_item("gear_strength", "engineering_limit", "blocked",
                     "缺少材料、载荷谱和工况系数，未执行ISO 6336强度校核"),
        _status_item("cad_fidelity", "engineering_limit", "provisional",
                     "齿轮为齿顶圆包络，不是精确渐开线齿面"),
        _status_item("preview", "engineering_limit", "warning",
                     "无头CLI未生成交互预览；STEP/STL已导出供外部查看"),
    ]


def _overall_status(summary: dict[str, int]) -> str:
    """Reduce check counts to one conservative overall status."""
    if summary.get("failed", 0):
        return "failed"
    if summary.get("blocked", 0):
        return "blocked"
    if summary.get("warning", 0):
        return "warning"
    if summary.get("provisional", 0):
        return "provisional"
    return "passed"

