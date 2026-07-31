"""Simplified split housing sized from gear and bearing envelopes."""

from __future__ import annotations

import cadquery as cq
from pydantic import BaseModel, model_validator


class HousingParameters(BaseModel):
    """Dimensions for the global-coordinate lower housing and cover."""

    length_mm: float
    width_mm: float
    height_mm: float
    wall_thickness_mm: float = 6.0
    centre_distance_mm: float
    input_seat_diameter_mm: float
    output_seat_diameter_mm: float

    @model_validator(mode="after")
    def validate_dimensions(self) -> "HousingParameters":
        """Require space for a positive hollow cavity and two shaft seats."""
        if min(
            self.length_mm,
            self.width_mm,
            self.height_mm,
            self.wall_thickness_mm,
            self.input_seat_diameter_mm,
            self.output_seat_diameter_mm,
        ) <= 0:
            raise ValueError("housing dimensions must be positive")
        if 2 * self.wall_thickness_mm >= min(self.width_mm, self.height_mm):
            raise ValueError("housing wall leaves no internal cavity")
        return self


def _outer_half(parameters: HousingParameters, upper: bool) -> cq.Workplane:
    """Build one solid outer half centred between the two shafts."""
    half_height = parameters.height_mm / 2.0
    z_centre = half_height / 2.0 if upper else -half_height / 2.0
    return (
        cq.Workplane("XY")
        .box(
            parameters.length_mm,
            parameters.width_mm,
            half_height,
            centered=(True, True, True),
        )
        .translate((0, parameters.centre_distance_mm / 2.0, z_centre))
    )


def _cavity(parameters: HousingParameters, upper: bool) -> cq.Workplane:
    """Build a cutter that leaves side and top/bottom walls."""
    wall = parameters.wall_thickness_mm
    half_height = parameters.height_mm / 2.0
    cavity_height = half_height
    z_centre = (
        half_height / 2.0 - wall if upper else -half_height / 2.0 + wall
    )
    return (
        cq.Workplane("XY")
        .box(
            parameters.length_mm - 2 * wall,
            parameters.width_mm - 2 * wall,
            cavity_height,
            centered=(True, True, True),
        )
        .translate((0, parameters.centre_distance_mm / 2.0, z_centre))
    )


def _shaft_seat_cutters(parameters: HousingParameters) -> cq.Workplane:
    """Build two X-axis through cylinders at the shaft split plane."""
    length = parameters.length_mm + 2.0
    plane = cq.Plane(
        origin=(-length / 2.0, 0, 0),
        xDir=(0, 1, 0),
        normal=(1, 0, 0),
    )
    first = (
        cq.Workplane(plane)
        .circle(parameters.input_seat_diameter_mm / 2.0)
        .extrude(length)
    )
    return first.union(
        cq.Workplane(
            cq.Plane(
                origin=(-length / 2.0, parameters.centre_distance_mm, 0),
                xDir=(0, 1, 0),
                normal=(1, 0, 0),
            )
        )
        .circle(parameters.output_seat_diameter_mm / 2.0)
        .extrude(length)
    )


def build_lower_housing(parameters: HousingParameters) -> cq.Workplane:
    """Build the hollow lower half with shaft seats and a simple base flange."""
    shell = _outer_half(parameters, upper=False).cut(
        _cavity(parameters, upper=False)
    )
    shell = shell.cut(_shaft_seat_cutters(parameters))
    wall = parameters.wall_thickness_mm
    base = (
        cq.Workplane("XY")
        .box(
            parameters.length_mm + 20.0,
            parameters.width_mm + 20.0,
            wall,
            centered=(True, True, True),
        )
        .translate(
            (
                0,
                parameters.centre_distance_mm / 2.0,
                -parameters.height_mm / 2.0 - wall / 2.0,
            )
        )
    )
    return shell.union(base)


def build_housing_cover(parameters: HousingParameters) -> cq.Workplane:
    """Build the hollow upper cover with matching split-plane shaft seats."""
    return (
        _outer_half(parameters, upper=True)
        .cut(_cavity(parameters, upper=True))
        .cut(_shaft_seat_cutters(parameters))
    )

