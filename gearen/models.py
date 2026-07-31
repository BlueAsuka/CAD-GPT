"""Serializable data models shared by the gearbox design pipeline."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SourceType = Literal["explicit", "inferred", "default", "calculated"]
HardnessType = Literal["hard", "soft"]
DesignStatus = Literal[
    "passed", "failed", "warning", "blocked", "provisional", "candidate"
]


class RequirementValue(BaseModel):
    """A requirement value together with provenance and decision metadata."""

    value: float | int | str | None = None
    unit: str | None = None
    source: SourceType = "explicit"
    hardness: HardnessType = "hard"
    confidence: float | None = None
    locked: bool = False
    original_text: str | None = None

    @field_validator("confidence")
    @classmethod
    def confidence_is_probability(cls, value: float | None) -> float | None:
        """Require confidence values to be probabilities."""
        if value is not None and not 0.0 <= value <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        return value

    def as_float(self) -> float | None:
        """Return a numeric value as float, or None when it is unavailable."""
        if self.value is None or isinstance(self.value, str):
            return None
        return float(self.value)


class GearboxRequirement(BaseModel):
    """Structured requirements supported by the single-stage MVP."""

    title: str = "单级圆柱齿轮减速器概念设计"
    objective: str = ""
    transmitted_power: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="kW")
    )
    transmission_ratio: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="ratio")
    )
    input_speed: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="rpm")
    )
    output_speed: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="rpm")
    )
    stage_count: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="count")
    )
    gear_family: RequirementValue = Field(default_factory=RequirementValue)
    shaft_axis_relation: RequirementValue = Field(default_factory=RequirementValue)
    calendar_life_years: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="year")
    )
    operating_hours: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="hour")
    )
    indoor_or_outdoor: RequirementValue = Field(default_factory=RequirementValue)
    minimum_temperature: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="degC")
    )
    maximum_temperature: RequirementValue = Field(
        default_factory=lambda: RequirementValue(unit="degC")
    )
    assumptions: list[str] = Field(default_factory=list)
    unresolved_requirements: list[str] = Field(default_factory=list)


class RequirementReview(BaseModel):
    """Result of checking whether a requirement can enter concept design."""

    is_valid: bool
    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    assumptions: dict[str, float | int | str] = Field(default_factory=dict)
    unresolved_requirements: list[str] = Field(default_factory=list)


class OperatingParameters(BaseModel):
    """Deterministically derived operating values with explicit engineering units."""

    power_kw: float
    input_speed_rpm: float
    output_speed_rpm: float
    target_ratio: float
    efficiency: float
    pressure_angle_deg: float
    input_torque_Nm: float
    ideal_output_torque_Nm: float
    estimated_output_torque_Nm: float


class GearCandidate(BaseModel):
    """One enumerated spur-gear parameter candidate."""

    z1: int
    z2: int
    module_mm: float
    face_width_mm: float
    pressure_angle_deg: float
    actual_ratio: float
    ratio_error: float
    pitch_diameter_pinion_mm: float
    pitch_diameter_wheel_mm: float
    outside_diameter_pinion_mm: float
    outside_diameter_wheel_mm: float
    centre_distance_mm: float
    input_torque_Nm: float
    output_torque_Nm: float
    tangential_force_N: float
    radial_force_N: float
    score: float
    warnings: list[str] = Field(default_factory=list)
    status: DesignStatus = "candidate"


class ShaftSegment(BaseModel):
    """A cylindrical segment of a provisional stepped shaft."""

    name: str
    diameter_mm: float
    length_mm: float


class ShaftDesign(BaseModel):
    """Concept-level shaft sizing and its stepped geometry."""

    component_id: str
    minimum_diameter_mm: float
    selected_diameter_mm: float
    allowable_shear_stress_MPa: float
    safety_factor: float
    segments: list[ShaftSegment]
    status: DesignStatus = "provisional"


class BearingSelection(BaseModel):
    """A simplified catalog bearing selection."""

    component_id: str
    designation: str
    bore_diameter_mm: float
    outer_diameter_mm: float
    width_mm: float
    selection_status: DesignStatus = "provisional"
    life_check_status: DesignStatus = "blocked"
    reason: str


class KeyDesign(BaseModel):
    """A provisional parallel-key selection."""

    component_id: str = "output_key"
    width_mm: float
    height_mm: float
    length_mm: float
    status: DesignStatus = "provisional"


class ComponentPlacement(BaseModel):
    """A deterministic component pose and approximate envelope."""

    component_id: str
    origin: tuple[float, float, float]
    axis: tuple[float, float, float]
    rotation_deg: float = 0.0
    length_axis: str = "X"
    mating_reference: str | None = None
    placement_reason: str
    estimated_bounding_box: tuple[float, float, float]


class LayoutResult(BaseModel):
    """Spatial solution for shafts, gears, bearings, key, and housing."""

    coordinate_convention: str = "X=axial, Y=shaft centre distance, Z=vertical"
    centre_distance_mm: float
    placements: list[ComponentPlacement]
    input_shaft: ShaftDesign
    output_shaft: ShaftDesign
    bearings: list[BearingSelection]
    output_key: KeyDesign

    def placement(self, component_id: str) -> ComponentPlacement:
        """Return a placement by its stable component identifier."""
        for item in self.placements:
            if item.component_id == component_id:
                return item
        raise KeyError(component_id)


class ValidationItem(BaseModel):
    """One transparent validation check."""

    check_id: str
    category: str
    status: DesignStatus
    message: str
    details: dict[str, float | int | str | bool] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    """Collection and summary of validation checks."""

    checks: list[ValidationItem]
    summary: dict[str, int]
    overall_status: DesignStatus


class PipelineStage(str, Enum):
    """Fixed stages of the gearbox-specific pipeline."""

    PARSE_REQUIREMENT = "parse_requirement"
    VALIDATE_REQUIREMENT = "validate_requirement"
    BUILD_GRAPH = "build_graph"
    GENERATE_TOPOLOGY = "generate_topology"
    CALCULATE_PARAMETERS = "calculate_parameters"
    SEARCH_CANDIDATES = "search_candidates"
    SOLVE_LAYOUT = "solve_layout"
    GENERATE_CAD = "generate_cad"
    VALIDATE_DESIGN = "validate_design"
    COMPLETE = "complete"
    NEED_USER_INPUT = "need_user_input"
    FAILED = "failed"


class PipelineResult(BaseModel):
    """Top-level result returned by a complete pipeline run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    output_dir: Path
    stage: PipelineStage
    requirement: GearboxRequirement
    requirement_review: RequirementReview
    operating_parameters: OperatingParameters | None = None
    candidate_count: int = 0
    selected_candidate: GearCandidate | None = None
    layout: LayoutResult | None = None
    cad_files: list[Path] = Field(default_factory=list)
    validation_report: ValidationReport | None = None

