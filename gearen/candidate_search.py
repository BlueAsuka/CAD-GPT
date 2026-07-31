"""Transparent enumeration and ranking of MVP spur-gear candidates."""

from __future__ import annotations

import json
from pathlib import Path

from gearen.calculations import (
    calculate_centre_distance,
    calculate_outside_diameter,
    calculate_pitch_diameter,
    calculate_radial_force,
    calculate_tangential_force,
)
from gearen.models import GearCandidate, OperatingParameters


DATA_DIR = Path(__file__).parent / "data"


def load_standard_modules(path: Path | None = None) -> list[float]:
    """Load and validate positive standard modules in mm from JSON."""
    module_path = path or DATA_DIR / "standard_modules.json"
    data = json.loads(module_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("standard module catalog must be a non-empty list")
    modules = [float(value) for value in data]
    if any(value <= 0 for value in modules):
        raise ValueError("standard modules must be greater than zero")
    return sorted(set(modules))


def score_candidate(
    *,
    ratio_error: float,
    centre_distance_mm: float,
    module_mm: float,
    face_width_mm: float,
    input_torque_Nm: float,
) -> tuple[float, list[str]]:
    """Return a readable heuristic score and warnings; lower is preferred.

    score = ratio error penalty + size penalty + module penalty
            + face-width penalty + warning penalty.
    It is only an MVP ranking heuristic, not a strength optimum.
    """
    warnings: list[str] = []
    recommended_module = 2.0 if input_torque_Nm > 50.0 else 1.5
    if module_mm < recommended_module:
        warnings.append("模数低于扭矩启发式建议值，需进行齿根强度校核")
    if face_width_mm < 10.0 * module_mm and input_torque_Nm > 50.0:
        warnings.append("齿宽较窄，需进行载荷分布和强度校核")

    ratio_error_penalty = ratio_error * 10_000.0
    size_penalty = centre_distance_mm / 100.0
    module_penalty = abs(module_mm - recommended_module) * 3.0
    face_width_penalty = face_width_mm / 200.0
    warning_penalty = len(warnings) * 25.0
    score = (
        ratio_error_penalty
        + size_penalty
        + module_penalty
        + face_width_penalty
        + warning_penalty
    )
    return score, warnings


def generate_candidates(
    operating: OperatingParameters,
    *,
    ratio_tolerance: float = 0.01,
    module_path: Path | None = None,
) -> list[GearCandidate]:
    """Enumerate teeth, standard module, and 8m/10m/12m face-width candidates."""
    if not 0 < ratio_tolerance < 1:
        raise ValueError("ratio_tolerance must be in (0, 1)")
    candidates: list[GearCandidate] = []
    for z1 in range(18, 41):
        for z2 in range(z1 + 1, 161):
            actual_ratio = z2 / z1
            ratio_error = abs(actual_ratio - operating.target_ratio) / operating.target_ratio
            if ratio_error > ratio_tolerance:
                continue
            for module_mm in load_standard_modules(module_path):
                candidates.extend(
                    _module_candidates(
                        z1, z2, module_mm, actual_ratio, ratio_error, operating
                    )
                )
    return sorted(
        candidates,
        key=lambda item: (
            item.score,
            item.ratio_error,
            item.centre_distance_mm,
            item.z1,
        ),
    )


def _module_candidates(
    z1: int,
    z2: int,
    module_mm: float,
    actual_ratio: float,
    ratio_error: float,
    operating: OperatingParameters,
) -> list[GearCandidate]:
    """Build the three face-width variants for one tooth/module combination."""
    pitch_1 = calculate_pitch_diameter(module_mm, z1)
    pitch_2 = calculate_pitch_diameter(module_mm, z2)
    centre_distance = calculate_centre_distance(pitch_1, pitch_2)
    tangential = calculate_tangential_force(operating.input_torque_Nm, pitch_1)
    radial = calculate_radial_force(tangential, operating.pressure_angle_deg)
    candidates: list[GearCandidate] = []
    for width_factor in (8.0, 10.0, 12.0):
        face_width = width_factor * module_mm
        score, warnings = score_candidate(
            ratio_error=ratio_error,
            centre_distance_mm=centre_distance,
            module_mm=module_mm,
            face_width_mm=face_width,
            input_torque_Nm=operating.input_torque_Nm,
        )
        candidates.append(
            GearCandidate(
                z1=z1,
                z2=z2,
                module_mm=module_mm,
                face_width_mm=face_width,
                pressure_angle_deg=operating.pressure_angle_deg,
                actual_ratio=actual_ratio,
                ratio_error=ratio_error,
                pitch_diameter_pinion_mm=pitch_1,
                pitch_diameter_wheel_mm=pitch_2,
                outside_diameter_pinion_mm=calculate_outside_diameter(module_mm, z1),
                outside_diameter_wheel_mm=calculate_outside_diameter(module_mm, z2),
                centre_distance_mm=centre_distance,
                input_torque_Nm=operating.input_torque_Nm,
                output_torque_Nm=operating.estimated_output_torque_Nm,
                tangential_force_N=tangential,
                radial_force_N=radial,
                score=score,
                warnings=warnings,
            )
        )
    return candidates


def select_candidate(candidates: list[GearCandidate]) -> GearCandidate:
    """Select the first ranked candidate and mark it provisional."""
    if not candidates:
        raise ValueError("no gear candidate satisfies the ratio tolerance")
    return candidates[0].model_copy(update={"status": "provisional"})

