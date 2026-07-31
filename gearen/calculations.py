"""Pure mechanical calculations using the project's documented internal units."""

from __future__ import annotations

import math

from gearen.models import GearboxRequirement, OperatingParameters, ShaftDesign, ShaftSegment


def _positive(value: float, name: str) -> None:
    """Reject non-finite and non-positive physical inputs."""
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")


def calculate_output_speed(input_speed_rpm: float, ratio: float) -> float:
    """Return output speed in rpm from input speed in rpm and reduction ratio."""
    _positive(input_speed_rpm, "input_speed_rpm")
    _positive(ratio, "ratio")
    return input_speed_rpm / ratio


def calculate_input_torque(power_kw: float, input_speed_rpm: float) -> float:
    """Return input torque in N·m using T=9550*P/n (kW and rpm)."""
    _positive(power_kw, "power_kw")
    _positive(input_speed_rpm, "input_speed_rpm")
    return 9550.0 * power_kw / input_speed_rpm


def calculate_ideal_output_torque(input_torque_Nm: float, ratio: float) -> float:
    """Return lossless output torque in N·m."""
    _positive(input_torque_Nm, "input_torque_Nm")
    _positive(ratio, "ratio")
    return input_torque_Nm * ratio


def calculate_estimated_output_torque(
    input_torque_Nm: float, ratio: float, efficiency: float
) -> float:
    """Return estimated output torque in N·m including 0<efficiency<=1."""
    _positive(input_torque_Nm, "input_torque_Nm")
    _positive(ratio, "ratio")
    if not math.isfinite(efficiency) or not 0 < efficiency <= 1:
        raise ValueError("efficiency must be finite and in (0, 1]")
    return input_torque_Nm * ratio * efficiency


def calculate_pitch_diameter(module_mm: float, teeth: int) -> float:
    """Return spur-gear pitch diameter in mm using d=m*z."""
    _positive(module_mm, "module_mm")
    if teeth <= 0:
        raise ValueError("teeth must be greater than zero")
    return module_mm * teeth


def calculate_outside_diameter(module_mm: float, teeth: int) -> float:
    """Return standard full-depth spur-gear outside diameter in mm, da=m*(z+2)."""
    _positive(module_mm, "module_mm")
    if teeth <= 0:
        raise ValueError("teeth must be greater than zero")
    return module_mm * (teeth + 2)


def calculate_centre_distance(
    pitch_diameter_1_mm: float, pitch_diameter_2_mm: float
) -> float:
    """Return centre distance in mm for two external gears."""
    _positive(pitch_diameter_1_mm, "pitch_diameter_1_mm")
    _positive(pitch_diameter_2_mm, "pitch_diameter_2_mm")
    return (pitch_diameter_1_mm + pitch_diameter_2_mm) / 2.0


def calculate_tangential_force(
    torque_Nm: float, pitch_diameter_mm: float
) -> float:
    """Return pitch-circle tangential force in N using Ft=2T/d.

    Torque is in N·m; pitch diameter is converted from mm to m.
    """
    _positive(torque_Nm, "torque_Nm")
    _positive(pitch_diameter_mm, "pitch_diameter_mm")
    return 2.0 * torque_Nm / (pitch_diameter_mm / 1000.0)


def calculate_radial_force(
    tangential_force_N: float, pressure_angle_deg: float
) -> float:
    """Return radial force in N for a spur gear, Fr=Ft*tan(alpha)."""
    _positive(tangential_force_N, "tangential_force_N")
    if not math.isfinite(pressure_angle_deg) or not 0 < pressure_angle_deg < 90:
        raise ValueError("pressure_angle_deg must be in (0, 90)")
    return tangential_force_N * math.tan(math.radians(pressure_angle_deg))


def derive_operating_parameters(
    requirement: GearboxRequirement,
    efficiency: float = 0.97,
    pressure_angle_deg: float = 20.0,
) -> OperatingParameters:
    """Derive the operating parameters required by candidate enumeration."""
    power = requirement.transmitted_power.as_float()
    speed = requirement.input_speed.as_float()
    ratio = requirement.transmission_ratio.as_float()
    if power is None or speed is None or ratio is None:
        raise ValueError("power, input speed, and transmission ratio are required")
    input_torque = calculate_input_torque(power, speed)
    return OperatingParameters(
        power_kw=power,
        input_speed_rpm=speed,
        output_speed_rpm=calculate_output_speed(speed, ratio),
        target_ratio=ratio,
        efficiency=efficiency,
        pressure_angle_deg=pressure_angle_deg,
        input_torque_Nm=input_torque,
        ideal_output_torque_Nm=calculate_ideal_output_torque(input_torque, ratio),
        estimated_output_torque_Nm=calculate_estimated_output_torque(
            input_torque, ratio, efficiency
        ),
    )


def estimate_shaft_diameter(
    component_id: str,
    torque_Nm: float,
    safety_factor: float = 2.0,
    allowable_shear_stress_MPa: float = 40.0,
) -> ShaftDesign:
    """Estimate a solid shaft diameter from torsion and return simple segments.

    Uses d=(16*T_design/(pi*tau_allow))^(1/3), with torque converted to N·mm.
    This is a provisional torsion-only estimate, not a complete shaft design.
    """
    _positive(torque_Nm, "torque_Nm")
    _positive(safety_factor, "safety_factor")
    _positive(allowable_shear_stress_MPa, "allowable_shear_stress_MPa")
    design_torque_Nmm = torque_Nm * 1000.0 * safety_factor
    minimum = (
        16.0 * design_torque_Nmm / (math.pi * allowable_shear_stress_MPa)
    ) ** (1.0 / 3.0)
    selected = math.ceil(minimum / 5.0) * 5.0
    segments = [
        ShaftSegment(name="input_end", diameter_mm=selected * 0.8, length_mm=30.0),
        ShaftSegment(name="bearing_left", diameter_mm=selected, length_mm=20.0),
        ShaftSegment(name="gear_seat", diameter_mm=selected * 1.1, length_mm=45.0),
        ShaftSegment(name="bearing_right", diameter_mm=selected, length_mm=20.0),
        ShaftSegment(name="output_end", diameter_mm=selected * 0.8, length_mm=30.0),
    ]
    return ShaftDesign(
        component_id=component_id,
        minimum_diameter_mm=minimum,
        selected_diameter_mm=selected,
        allowable_shear_stress_MPa=allowable_shear_stress_MPa,
        safety_factor=safety_factor,
        segments=segments,
    )

