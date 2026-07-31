"""MVP scope checks and centralized concept-design assumptions."""

from __future__ import annotations

from gearen.models import GearboxRequirement, RequirementReview, RequirementValue


DEFAULT_ASSUMPTIONS: dict[str, float | int | str] = {
    "pressure_angle_deg": 20.0,
    "efficiency": 0.97,
    "gear_type": "spur",
    "shaft_axis_relation": "parallel",
    "design_status": "provisional",
    "shaft_safety_factor": 2.0,
    "allowable_shaft_shear_stress_MPa": 40.0,
}

NON_BLOCKING_REQUIREMENTS = [
    "工作小时",
    "载荷谱",
    "材料",
    "允许尺寸",
    "噪声",
    "润滑方式",
]


def _missing(value: RequirementValue) -> bool:
    """Return whether a structured requirement has no value."""
    return value.value is None


def validate_requirement(requirement: GearboxRequirement) -> RequirementReview:
    """Validate mandatory values and the deliberately narrow MVP scope."""
    blocking: list[str] = []
    warnings: list[str] = []

    if _missing(requirement.transmitted_power):
        blocking.append("缺少传递功率")
    if _missing(requirement.input_speed):
        blocking.append("缺少输入转速")
    if _missing(requirement.transmission_ratio) and _missing(requirement.output_speed):
        blocking.append("同时缺少传动比和输出转速")

    stage_count = requirement.stage_count.as_float()
    if stage_count is None:
        requirement.stage_count = RequirementValue(
            value=1,
            unit='count',
            source='default',
            hardness='soft',
            confidence=0.8,
            original_text='MVP default',
        )
        warnings.append("未明确级数；概念设计默认单级")
    elif stage_count != 1:
        blocking.append(f"当前MVP仅支持单级，输入要求为{stage_count:g}级")

    family = requirement.gear_family.value
    if family is None:
        requirement.gear_family = RequirementValue(
            value='cylindrical',
            source='default',
            hardness='soft',
            confidence=0.8,
            original_text='MVP default',
        )
        warnings.append("未明确齿轮类型；概念设计默认直齿圆柱齿轮")
    elif family != "cylindrical":
        blocking.append(f"当前MVP不支持齿轮类型：{family}")

    relation = requirement.shaft_axis_relation.value
    if relation is None:
        requirement.shaft_axis_relation = RequirementValue(
            value='parallel',
            source='default',
            hardness='soft',
            confidence=0.8,
            original_text='MVP default',
        )
        relation = 'parallel'
    if relation not in (None, "parallel"):
        blocking.append(f"当前MVP仅支持平行轴，输入要求为：{relation}")

    for item in NON_BLOCKING_REQUIREMENTS:
        if not any(item in unresolved for unresolved in requirement.unresolved_requirements):
            if item in {"工作小时", "载荷谱"}:
                continue
        warnings.append(f"未提供{item}；相关详细校核将保持provisional或blocked")

    unresolved = list(dict.fromkeys(requirement.unresolved_requirements))
    if requirement.operating_hours.value is None and "总工作小时" not in unresolved:
        unresolved.append("总工作小时")

    for item in NON_BLOCKING_REQUIREMENTS:
        if not any(item in existing for existing in unresolved):
            unresolved.append(item)

    assumptions = dict(DEFAULT_ASSUMPTIONS)
    requirement.assumptions = [
        f"{key}={value}" for key, value in DEFAULT_ASSUMPTIONS.items()
    ]
    return RequirementReview(
        is_valid=not blocking,
        blocking_issues=blocking,
        warnings=list(dict.fromkeys(warnings)),
        assumptions=assumptions,
        unresolved_requirements=unresolved,
    )
