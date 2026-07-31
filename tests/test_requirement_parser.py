"""Tests for deterministic Chinese requirement extraction."""

from gearen.requirement_parser import RuleBasedRequirementParser
from gearen.requirement_validator import validate_requirement


EXAMPLE = """设计任务：设计一个单级圆柱齿轮减速器，用于一个工作机。
设计要求：
a. 传递功率：10 kW
b. 传动比：3
c. 输入轴转速：1440 rpm
d. 使用寿命：10年
e. 工作环境：室内，温度范围-10°C至+40°C
"""


def test_chinese_requirement_values() -> None:
    """Extract all values from the documented Chinese example."""
    result = RuleBasedRequirementParser().parse(EXAMPLE)
    assert result.transmitted_power.value == 10
    assert result.transmission_ratio.value == 3
    assert result.input_speed.value == 1440
    assert result.output_speed.value == 480
    assert result.output_speed.source == "calculated"
    assert result.calendar_life_years.value == 10
    assert result.minimum_temperature.value == -10
    assert result.maximum_temperature.value == 40
    assert result.stage_count.value == 1
    assert result.gear_family.value == "cylindrical"
    assert result.shaft_axis_relation.value == "parallel"


def test_missing_operating_duty_is_non_blocking() -> None:
    """Keep concept design valid while recording missing duty information."""
    requirement = RuleBasedRequirementParser().parse(EXAMPLE)
    review = validate_requirement(requirement)
    assert review.is_valid
    assert "总工作小时" in review.unresolved_requirements
    assert "载荷谱" in review.unresolved_requirements


def test_unsupported_topology_blocks_design() -> None:
    """Reject an explicitly requested topology outside the MVP scope."""
    requirement = RuleBasedRequirementParser().parse(
        "设计一个两级行星减速器，功率10kW，传动比3，输入转速1440rpm"
    )
    review = validate_requirement(requirement)
    assert not review.is_valid
    assert len(review.blocking_issues) == 2

