"""Schema for LLM-extracted gearbox design requirements.

This module represents the requirement-extraction layer of the CAD pipeline:

    source text / image
        -> LLM extraction
        -> DesignRequirement (this module)
        -> deterministic compilation
        -> gearbox engineering requirements
        -> component synthesis and CAD generation

The schema keeps the source language for traceability while normalizing common
gearbox concepts, units, identifiers, constraint semantics, assumptions, and
unresolved items. It remains backward compatible with the older string-list
representation used for qualitative requirements and source files.
"""

from __future__ import annotations

import hashlib
import re
from enum import Enum
from pathlib import PurePath
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Shared configuration and enums
# ---------------------------------------------------------------------------


class StrictModel(BaseModel):
    """Strict base model for every schema object."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=False,
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class RequirementSource(str, Enum):
    EXPLICIT = "explicit"
    LLM_INFERENCE = "llm_inference"
    ENGINEERING_DEFAULT = "engineering_default"
    CALCULATION = "calculation"
    STANDARD = "standard"
    CATALOG = "catalog"
    UNKNOWN = "unknown"


class ConstraintQualifier(str, Enum):
    GIVEN = "given"
    TARGET = "target"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    RANGE = "range"
    FIXED = "fixed"
    PREFERRED = "preferred"
    DERIVED = "derived"


class ConstraintHardness(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    ASSUMPTION = "assumption"


class RequirementPriority(str, Enum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"


class RequirementStatus(str, Enum):
    SPECIFIED = "specified"
    QUALITATIVE = "qualitative"
    UNSPECIFIED = "unspecified"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class Importance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def _alias_map(groups: dict[str, tuple[str, ...]]) -> dict[str, str]:
    return {
        alias: canonical
        for canonical, aliases in groups.items()
        for alias in aliases
    }


UNIT_ALIASES: dict[str, str] = _alias_map({
    "kW": ("kw", "千瓦"),
    "W": ("w",),
    "MW": ("mw",),
    "rpm": ("rpm", "r/min", "rev/min", "转/分", "转每分"),
    "N*m": ("n.m", "n·m", "nm"),
    "year": ("年", "years", "year"),
    "h": ("小时", "hour", "hours", "h"),
    "degC": ("℃", "°c", "c", "degc"),
    "mm": ("毫米", "mm"),
    "cm": ("厘米", "cm"),
    "m": ("米", "m"),
    "kg": ("kg", "公斤"),
    "dB": ("db",),
    "dBA": ("dba",),
    "dimensionless": ("dimensionless", "无量纲", "-"),
})

QUANTITATIVE_ALIASES: dict[str, str] = _alias_map({
    "input_power": ("传递功率", "输入功率", "额定功率", "power", "input power"),
    "total_transmission_ratio": ("传动比", "总传动比", "减速比", "速比", "gear ratio"),
    "input_speed": ("输入轴转速", "输入转速", "input speed"),
    "output_speed": ("输出轴转速", "输出转速", "output speed"),
    "output_torque": ("输出扭矩",),
    "torque": ("扭矩",),
    "design_life_duration": ("使用寿命", "设计寿命", "寿命"),
    "maximum_length": ("最大长度",),
    "maximum_width": ("最大宽度",),
    "maximum_height": ("最大高度",),
    "efficiency": ("效率",),
    "noise_level": ("噪声",),
})

ENVIRONMENT_ALIASES: dict[str, str] = _alias_map({
    "ambient_temperature": ("温度", "环境温度", "工作温度", "ambient temperature"),
    "humidity": ("湿度",),
    "dust_exposure": ("粉尘",),
    "corrosion_exposure": ("腐蚀",),
    "installation_environment": ("室内", "室外"),
})

FUNCTIONAL_DEFAULTS: dict[str, tuple[str, str]] = {
    "input_power": ("实现功率传递", "power_transmission"),
    "total_transmission_ratio": ("满足指定传动比", "speed_reduction"),
    "input_speed": ("匹配输入轴转速", "input_speed_compatibility"),
    "design_life_duration": ("具备足够使用寿命", "design_life"),
}

HIGH_IMPACT_ASSUMPTION_TERMS = (
    "连续",
    "冲击",
    "脉动",
    "负载",
    "启停",
    "润滑",
    "寿命",
    "可靠",
    "载荷",
)


UNRESOLVED_NOTE_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("负载", "载荷", "负载曲线"), "operating_conditions.load_profile", "请补充工作机的具体负载特性（如负载类型、负载曲线和冲击情况）。"),
    (("功率来源", "输出轴", "用途"), "system_context.power_flow", "请明确输入轴的功率来源和输出轴所驱动的工作机。"),
    (("每天", "运行时间", "工作时间", "负载周期"), "operating_conditions.duty_cycle", "请说明每天运行时间、年运行天数以及是否连续运行。"),
    (("尺寸", "空间", "外形"), "spatial_constraints.maximum_envelope", "请提供减速器允许的最大外形尺寸或安装空间。"),
    (("直齿", "斜齿"), "architecture_constraints.gear_type", "请确认采用直齿还是斜齿圆柱齿轮。"),
    (("传动比误差", "速比误差", "允许误差"), "performance_requirements.total_transmission_ratio.tolerance", "请给出传动比允许误差。"),
)


def normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    cleaned = unit.strip()
    return UNIT_ALIASES.get(cleaned.lower(), UNIT_ALIASES.get(cleaned, cleaned))


def normalize_lookup_text(text: str) -> str:
    return re.sub(r"[\s:_：()（）\-]+", "", text).lower()


def infer_semantic_key(name: str, aliases: dict[str, str]) -> str | None:
    normalized = normalize_lookup_text(name)
    for alias, semantic_key in aliases.items():
        alias_normalized = normalize_lookup_text(alias)
        if normalized == alias_normalized or alias_normalized in normalized:
            return semantic_key
    return None


def infer_quantitative_qualifier(semantic_key: str | None) -> ConstraintQualifier:
    return {
        "total_transmission_ratio": ConstraintQualifier.TARGET,
        "design_life_duration": ConstraintQualifier.MINIMUM,
    }.get(semantic_key, ConstraintQualifier.GIVEN)


def _legacy_object(value: Any, field: str) -> Any:
    return {field: value} if isinstance(value, str) else value


def _with_explicit_confidence(requirement: Any) -> Any:
    if requirement.source == RequirementSource.EXPLICIT and requirement.confidence is None:
        requirement.confidence = 1.0
    return requirement


def stable_extraction_id(title: str, objective: str, source_paths: list[str]) -> str:
    payload = "|".join([title, objective, *source_paths]).encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest()[:10].upper()
    return f"REQ-EXT-{digest}"


def normalize_source_path(path: str) -> str:
    return PurePath(path.replace("\\", "/")).as_posix()


# ---------------------------------------------------------------------------
# Reusable value objects
# ---------------------------------------------------------------------------


class RangeValue(StrictModel):
    minimum: float = Field(description="Lower bound of the range")
    maximum: float = Field(description="Upper bound of the range")
    unit: str | None = Field(default=None, description="Normalized unit")

    @model_validator(mode="after")
    def normalize_and_validate(self) -> "RangeValue":
        if self.minimum > self.maximum:
            raise ValueError("minimum must not be greater than maximum")
        self.unit = normalize_unit(self.unit)
        return self


class Tolerance(StrictModel):
    type: Literal["absolute", "relative"]
    value: float = Field(ge=0)
    unit: str | None = None

    @model_validator(mode="after")
    def normalize_and_validate(self) -> "Tolerance":
        self.unit = normalize_unit(self.unit)
        if self.type == "relative" and self.unit is not None:
            raise ValueError("relative tolerance must not define a unit")
        if self.type == "absolute" and self.unit is None:
            raise ValueError("absolute tolerance requires a unit")
        return self


class SourceReference(StrictModel):
    path: str
    source_type: Literal["text", "image", "pdf", "cad", "spreadsheet", "other"] = "text"
    document_role: Literal[
        "primary_requirement",
        "supporting_reference",
        "standard",
        "catalog",
        "other",
    ] = "primary_requirement"
    page: int | None = Field(default=None, ge=1)

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_string(cls, value: Any) -> Any:
        return _legacy_object(value, "path")

    @model_validator(mode="after")
    def normalize_path(self) -> "SourceReference":
        self.path = normalize_source_path(self.path)
        return self


# ---------------------------------------------------------------------------
# Requirement objects
# ---------------------------------------------------------------------------


class _StatementRequirement(StrictModel):
    id: str | None = None
    statement: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_string(cls, value: Any) -> Any:
        return _legacy_object(value, "statement")


class _SemanticStatementRequirement(_StatementRequirement):
    semantic_key: str | None = None


class FunctionalRequirement(_SemanticStatementRequirement):
    priority: RequirementPriority = RequirementPriority.MUST
    source: RequirementSource = RequirementSource.EXPLICIT
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def normalize_fields(self) -> "FunctionalRequirement":
        return _with_explicit_confidence(self)


class QuantitativeRequirement(StrictModel):
    id: str | None = None
    name: str = Field(min_length=1)
    semantic_key: str | None = None
    value: float | int | str | RangeValue
    unit: str | None = None
    qualifier: ConstraintQualifier | None = None
    hardness: ConstraintHardness = ConstraintHardness.HARD
    tolerance: Tolerance | None = None
    source: RequirementSource = RequirementSource.EXPLICIT
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    locked: bool = False
    original_text: str | None = None

    @model_validator(mode="after")
    def normalize_and_validate(self) -> "QuantitativeRequirement":
        self.semantic_key = self.semantic_key or infer_semantic_key(
            self.name, QUANTITATIVE_ALIASES
        )
        self.unit = normalize_unit(self.unit)

        if self.semantic_key == "total_transmission_ratio" and self.unit is None:
            self.unit = "dimensionless"
        if self.semantic_key == "design_life_duration" and self.unit is None:
            self.unit = "year"

        if isinstance(self.value, RangeValue):
            self.qualifier = ConstraintQualifier.RANGE
            if self.unit is None:
                self.unit = self.value.unit
            elif self.value.unit not in (None, self.unit):
                raise ValueError("unit conflicts with RangeValue.unit")
            self.value.unit = self.unit
        elif self.qualifier is None or (
            self.qualifier == ConstraintQualifier.GIVEN
            and self.semantic_key in {"total_transmission_ratio", "design_life_duration"}
        ):
            self.qualifier = infer_quantitative_qualifier(self.semantic_key)

        if self.source == RequirementSource.EXPLICIT:
            if self.confidence is None:
                self.confidence = 1.0
            if self.hardness == ConstraintHardness.HARD:
                self.locked = True

        if self.tolerance and self.qualifier != ConstraintQualifier.TARGET:
            raise ValueError("tolerance is only valid for qualifier='target'")
        return self


class EnvironmentalRequirement(_SemanticStatementRequirement):
    parsed_value: float | int | str | bool | RangeValue | None = None
    unit: str | None = None
    qualifier: ConstraintQualifier | None = None
    hardness: ConstraintHardness = ConstraintHardness.HARD
    source: RequirementSource = RequirementSource.EXPLICIT
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def normalize_fields(self) -> "EnvironmentalRequirement":
        self.semantic_key = self.semantic_key or infer_semantic_key(
            self.statement, ENVIRONMENT_ALIASES
        )
        self.unit = normalize_unit(self.unit)
        if isinstance(self.parsed_value, RangeValue):
            self.qualifier = ConstraintQualifier.RANGE
            if self.unit is None:
                self.unit = self.parsed_value.unit
            self.parsed_value.unit = self.unit
        return _with_explicit_confidence(self)


class LifecycleRequirement(_SemanticStatementRequirement):
    status: RequirementStatus = RequirementStatus.QUALITATIVE
    priority: RequirementPriority = RequirementPriority.MUST
    source: RequirementSource = RequirementSource.EXPLICIT
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def normalize_fields(self) -> "LifecycleRequirement":
        return _with_explicit_confidence(self)


class OtherConstraint(_SemanticStatementRequirement):
    hardness: ConstraintHardness = ConstraintHardness.HARD
    source: RequirementSource = RequirementSource.EXPLICIT
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class Assumption(_StatementRequirement):
    category: str | None = None
    source: Literal["llm_inference", "engineering_default"] = "llm_inference"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    requires_confirmation: bool = False
    design_impact: str | None = None

    @model_validator(mode="after")
    def normalize_confirmation(self) -> "Assumption":
        if any(term in self.statement for term in HIGH_IMPACT_ASSUMPTION_TERMS):
            self.requires_confirmation = True
        return self


class UnresolvedItem(StrictModel):
    id: str | None = None
    field: str
    question: str = Field(min_length=1)
    importance: Importance = Importance.MEDIUM
    blocking: bool = False
    reason: str | None = None


class CompletenessSummary(StrictModel):
    overall_status: Literal["complete", "incomplete", "conflicting"] = "incomplete"
    ready_for_conceptual_design: bool = True
    ready_for_preliminary_design: bool = False
    ready_for_detailed_design: bool = False
    blocking_item_count: int = Field(default=0, ge=0)
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Root extraction document
# ---------------------------------------------------------------------------


class DesignRequirement(StrictModel):
    """LLM-extracted requirements for downstream engineering compilation."""

    schema_version: str = "0.3.0"
    document_type: Literal["requirement_extraction"] = "requirement_extraction"
    extraction_id: str | None = None

    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    application: str | None = None

    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    quantitative_requirements: list[QuantitativeRequirement] = Field(default_factory=list)
    environmental_requirements: list[EnvironmentalRequirement] = Field(default_factory=list)
    lifecycle_requirements: list[LifecycleRequirement] = Field(default_factory=list)
    other_constraints: list[OtherConstraint] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    unresolved_items: list[UnresolvedItem] = Field(default_factory=list)
    completeness: CompletenessSummary | None = None
    source_files: list[SourceReference] = Field(default_factory=list)

    _ID_PREFIXES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("functional_requirements", "FR"),
        ("quantitative_requirements", "QR"),
        ("environmental_requirements", "ER"),
        ("lifecycle_requirements", "LR"),
        ("other_constraints", "OC"),
        ("assumptions", "ASM"),
        ("unresolved_items", "UNR"),
    )

    @model_validator(mode="after")
    def normalize_document(self) -> "DesignRequirement":
        self._add_default_functional_requirements()
        self._create_unresolved_items_from_notes()
        self._assign_ids()
        self.extraction_id = self.extraction_id or stable_extraction_id(
            self.title,
            self.objective,
            [source.path for source in self.source_files],
        )
        self._synchronize_completeness()
        return self

    def _add_default_functional_requirements(self) -> None:
        existing_keys = {item.semantic_key for item in self.functional_requirements}
        quantitative_keys = {
            item.semantic_key for item in self.quantitative_requirements if item.semantic_key
        }
        for semantic_key, (statement, functional_key) in FUNCTIONAL_DEFAULTS.items():
            if semantic_key in quantitative_keys and functional_key not in existing_keys:
                self.functional_requirements.append(
                    FunctionalRequirement(
                        statement=statement,
                        semantic_key=functional_key,
                        source=RequirementSource.CALCULATION,
                        confidence=1.0,
                    )
                )
                existing_keys.add(functional_key)

    def _create_unresolved_items_from_notes(self) -> None:
        if self.completeness is None or not self.completeness.notes:
            return
        existing_fields = {item.field for item in self.unresolved_items}
        for note in self.completeness.notes:
            field = "requirements.unspecified"
            question = f"请补充以下信息：{note.rstrip('。')}。"
            for terms, candidate_field, candidate_question in UNRESOLVED_NOTE_RULES:
                if any(term in note for term in terms):
                    field = candidate_field
                    question = candidate_question
                    break
            if field not in existing_fields:
                self.unresolved_items.append(
                    UnresolvedItem(
                        field=field,
                        question=question,
                        importance=Importance.HIGH,
                        blocking=True,
                        reason=note,
                    )
                )
                existing_fields.add(field)

    def _assign_ids(self) -> None:
        used: set[str] = set()
        for field_name, prefix in self._ID_PREFIXES:
            items = getattr(self, field_name)
            next_index = 1
            for item in items:
                if item.id:
                    if item.id in used:
                        raise ValueError(f"duplicate requirement ID: {item.id}")
                    used.add(item.id)
                    continue
                while f"{prefix}-{next_index:03d}" in used:
                    next_index += 1
                item.id = f"{prefix}-{next_index:03d}"
                used.add(item.id)
                next_index += 1

    def _synchronize_completeness(self) -> None:
        self.completeness = self.completeness or CompletenessSummary()
        self.completeness.blocking_item_count = sum(
            item.blocking for item in self.unresolved_items
        )
        if self.unresolved_items:
            self.completeness.overall_status = "incomplete"
            self.completeness.ready_for_detailed_design = False
        elif self.completeness.overall_status != "conflicting":
            self.completeness.overall_status = "complete"
            self.completeness.ready_for_preliminary_design = True
            self.completeness.ready_for_detailed_design = True

__all__ = [
    "Assumption",
    "CompletenessSummary",
    "ConstraintHardness",
    "ConstraintQualifier",
    "DesignRequirement",
    "EnvironmentalRequirement",
    "FunctionalRequirement",
    "Importance",
    "LifecycleRequirement",
    "OtherConstraint",
    "QuantitativeRequirement",
    "RangeValue",
    "RequirementPriority",
    "RequirementSource",
    "RequirementStatus",
    "SourceReference",
    "Tolerance",
    "UnresolvedItem",
]
