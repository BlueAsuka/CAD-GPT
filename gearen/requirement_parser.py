"""Rule-based Chinese requirement parsing with no external API dependency."""

from __future__ import annotations

import re
from typing import Protocol

from gearen.calculations import calculate_output_speed
from gearen.models import GearboxRequirement, RequirementValue


class RequirementParser(Protocol):
    """Interface for parsers that return validated structured requirements."""

    def parse(self, text: str) -> GearboxRequirement:
        """Parse natural-language input into a gearbox requirement."""


def _value(
    value: float | int | str | None,
    unit: str | None,
    source: str,
    hardness: str,
    original: str | None,
    confidence: float,
) -> RequirementValue:
    """Build a provenance-rich requirement value without hiding defaults."""
    return RequirementValue(
        value=value,
        unit=unit,
        source=source,  # type: ignore[arg-type]
        hardness=hardness,  # type: ignore[arg-type]
        confidence=confidence,
        locked=source == "explicit",
        original_text=original,
    )


def _match_number(text: str, pattern: str) -> tuple[float | None, str | None]:
    """Extract the first decimal number and its complete matching text."""
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None, None
    return float(match.group(1)), match.group(0)


class RuleBasedRequirementParser:
    """Parse the supported Chinese gearbox phrases with explicit regex rules."""

    def parse(self, text: str) -> GearboxRequirement:
        """Parse a Chinese single-stage gearbox requirement."""
        normalized = self._normalize(text)
        requirement = GearboxRequirement(
            title=self._title(normalized),
            objective=self._objective(normalized),
        )
        self._parse_numeric_values(normalized, requirement)
        self._parse_topology(normalized, requirement)
        self._parse_environment(normalized, requirement)
        self._derive_kinematics(requirement)
        requirement.unresolved_requirements = self._unresolved(normalized, requirement)
        return requirement

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize punctuation while preserving the original engineering text."""
        return (
            text.strip()
            .replace("：", ":")
            .replace("，", ",")
            .replace("＋", "+")
            .replace("－", "-")
            .replace("℃", "°C")
        )

    @staticmethod
    def _title(text: str) -> str:
        """Use the explicit design-task line as the title when present."""
        match = re.search(r"设计任务\s*:\s*([^\r\n。]+)", text)
        return match.group(1).strip() if match else "单级圆柱齿轮减速器概念设计"

    @staticmethod
    def _objective(text: str) -> str:
        """Keep the first task sentence as a human-readable objective."""
        first_line = text.splitlines()[0].strip() if text.splitlines() else text
        return re.sub(r"^设计任务\s*:\s*", "", first_line).rstrip("。")

    def _parse_numeric_values(
        self, text: str, requirement: GearboxRequirement
    ) -> None:
        """Extract power, ratio, speed, and calendar life."""
        specs = [
            (
                "transmitted_power",
                r"(?:传递功率|功率)\s*[:为]?\s*([+]?\d+(?:\.\d+)?)\s*(?:kW|千瓦)",
                "kW",
            ),
            (
                "transmission_ratio",
                r"传动比\s*[:为]?\s*([+]?\d+(?:\.\d+)?)",
                "ratio",
            ),
            (
                "input_speed",
                r"(?:输入轴?转速|输入转速)\s*[:为]?\s*([+]?\d+(?:\.\d+)?)\s*(?:rpm|转/分)",
                "rpm",
            ),
            (
                "calendar_life_years",
                r"(?:使用寿命|寿命)\s*[:为]?\s*([+]?\d+(?:\.\d+)?)\s*年",
                "year",
            ),
        ]
        specs.append(
            (
                'operating_hours',
                r'(?:总工作小时|工作寿命|累计工作时间)\s*[:为]?\s*'
                r'([+]?\d+(?:\.\d+)?)\s*(?:h|小时)',
                'hour',
            )
        )
        for field_name, pattern, unit in specs:
            number, original = _match_number(text, pattern)
            if number is not None:
                setattr(
                    requirement,
                    field_name,
                    _value(number, unit, "explicit", "hard", original, 0.99),
                )

        output, original = _match_number(
            text,
            r"(?:输出轴?转速|输出转速)\s*[:为]?\s*([+]?\d+(?:\.\d+)?)\s*(?:rpm|转/分)",
        )
        if output is not None:
            requirement.output_speed = _value(
                output, "rpm", "explicit", "hard", original, 0.99
            )

    @staticmethod
    def _parse_topology(text: str, requirement: GearboxRequirement) -> None:
        """Extract supported and explicitly unsupported topology terms."""
        stage_map = {"单级": 1, "一级": 1, "两级": 2, "二级": 2, "三级": 3}
        for phrase, count in stage_map.items():
            if phrase in text:
                requirement.stage_count = _value(
                    count, "count", "explicit", "hard", phrase, 0.99
                )
                break

        families = [
            ("行星", "planetary"),
            ("锥齿轮", "bevel"),
            ("蜗杆", "worm"),
            ("斜齿轮", "helical"),
            ("圆柱齿轮", "cylindrical"),
        ]
        for phrase, family in families:
            if phrase in text:
                requirement.gear_family = _value(
                    family, None, "explicit", "hard", phrase, 0.99
                )
                break

        if "平行轴" in text:
            requirement.shaft_axis_relation = _value(
                "parallel", None, "explicit", "hard", "平行轴", 0.99
            )
        elif requirement.gear_family.value == "cylindrical":
            requirement.shaft_axis_relation = _value(
                "parallel", None, "inferred", "soft", "圆柱齿轮", 0.90
            )

    @staticmethod
    def _parse_environment(text: str, requirement: GearboxRequirement) -> None:
        """Extract indoor/outdoor and a signed Celsius temperature range."""
        if "室内" in text:
            requirement.indoor_or_outdoor = _value(
                "indoor", None, "explicit", "hard", "室内", 0.99
            )
        elif "室外" in text:
            requirement.indoor_or_outdoor = _value(
                "outdoor", None, "explicit", "hard", "室外", 0.99
            )

        pattern = (
            r"([+-]?\d+(?:\.\d+)?)\s*(?:°\s*C|C)"
            r"\s*(?:至|到|~|～|-)\s*([+-]?\d+(?:\.\d+)?)\s*(?:°\s*C|C)"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            requirement.minimum_temperature = _value(
                float(match.group(1)), "degC", "explicit", "hard", match.group(0), 0.99
            )
            requirement.maximum_temperature = _value(
                float(match.group(2)), "degC", "explicit", "hard", match.group(0), 0.99
            )

    @staticmethod
    def _derive_kinematics(requirement: GearboxRequirement) -> None:
        """Calculate output speed only when it was not explicitly supplied."""
        if (
            requirement.output_speed.value is not None
            and requirement.transmission_ratio.value is not None
        ):
            return
        speed = requirement.input_speed.as_float()
        ratio = requirement.transmission_ratio.as_float()
        output = requirement.output_speed.as_float()
        if speed is not None and ratio is not None:
            calculated = calculate_output_speed(speed, ratio)
            requirement.output_speed = _value(
                calculated,
                "rpm",
                "calculated",
                "hard",
                "input_speed / transmission_ratio",
                1.0,
            )

        elif ratio is None and speed is not None and output is not None:
            requirement.transmission_ratio = _value(
                speed / output,
                'ratio',
                'calculated',
                'hard',
                'input_speed / output_speed',
                1.0,
            )

    @staticmethod
    def _unresolved(text: str, requirement: GearboxRequirement) -> list[str]:
        """List missing data that blocks detailed checks but not concept design."""
        unresolved: list[str] = []
        if not re.search(r"每天.*小时|日工作.*小时", text):
            unresolved.append("每天工作小时")
        if not re.search(r"每年.*(?:天|日)|年工作.*(?:天|日)", text):
            unresolved.append("每年工作天数")
        if "载荷谱" not in text:
            unresolved.append("载荷谱")
        if not re.search(r"冲击(?:程度|载荷)|轻微冲击|中等冲击|严重冲击", text):
            unresolved.append("冲击程度")
        if requirement.operating_hours.value is None:
            unresolved.append("总工作小时")
        return unresolved


class LLMRequirementParser:
    """Reserved interface for a future JSON-only LLM parser.

    The MVP intentionally does not call an LLM. Mechanical calculations and CAD
    generation remain deterministic even when this parser is implemented later.
    """

    def parse(self, text: str) -> GearboxRequirement:
        """Raise a clear error because no provider integration is configured."""
        raise NotImplementedError(
            "LLM parsing is optional and not implemented; use RuleBasedRequirementParser"
        )
