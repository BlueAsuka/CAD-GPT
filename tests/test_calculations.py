"""Tests for unit-explicit deterministic mechanical calculations."""

import pytest

from gearen.calculations import (
    calculate_centre_distance,
    calculate_input_torque,
    calculate_output_speed,
    calculate_pitch_diameter,
    calculate_radial_force,
    calculate_tangential_force,
)


def test_documented_speed_and_torque() -> None:
    """Match the expected operating values for 10 kW at 1440 rpm."""
    assert calculate_output_speed(1440, 3) == 480
    assert calculate_input_torque(10, 1440) == pytest.approx(66.3194, rel=1e-4)


def test_gear_geometry_and_forces() -> None:
    """Calculate centre distance and positive mesh loads."""
    d1 = calculate_pitch_diameter(3, 20)
    d2 = calculate_pitch_diameter(3, 60)
    assert calculate_centre_distance(d1, d2) == 120
    force = calculate_tangential_force(66.3194, d1)
    assert force > 0
    assert calculate_radial_force(force, 20) > 0


@pytest.mark.parametrize(
    ("function", "args"),
    [
        (calculate_output_speed, (1440, 0)),
        (calculate_input_torque, (10, 0)),
        (calculate_pitch_diameter, (-1, 20)),
    ],
)
def test_invalid_inputs_raise(function, args) -> None:
    """Reject divide-by-zero and non-physical values."""
    with pytest.raises(ValueError):
        function(*args)

