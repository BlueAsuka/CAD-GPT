"""Simplified spur-gear geometry and a clear backend extension boundary."""

from __future__ import annotations

from typing import Protocol

import cadquery as cq
from pydantic import BaseModel, model_validator


class GearParameters(BaseModel):
    """Parameters required by a gear geometry backend, in millimetres."""

    module_mm: float
    teeth: int
    face_width_mm: float
    bore_diameter_mm: float
    hub_diameter_mm: float | None = None
    hub_width_mm: float | None = None

    @model_validator(mode="after")
    def positive_and_nested_diameters(self) -> "GearParameters":
        """Reject non-physical values and a bore larger than the gear."""
        values = [
            self.module_mm,
            self.face_width_mm,
            self.bore_diameter_mm,
            float(self.teeth),
        ]
        if any(value <= 0 for value in values):
            raise ValueError("gear dimensions and tooth count must be positive")
        outside = self.module_mm * (self.teeth + 2)
        if self.bore_diameter_mm >= outside:
            raise ValueError("gear bore must be smaller than outside diameter")
        return self


class GearGeometryBackend(Protocol):
    """Interface implemented by deterministic gear geometry backends."""

    def build(self, parameters: GearParameters) -> cq.Workplane:
        """Build a CadQuery gear aligned with the positive X axis."""


def _yz_plane(x_position: float = 0.0) -> cq.Plane:
    """Return a plane whose normal is the global positive X direction."""
    return cq.Plane(
        origin=(x_position, 0, 0),
        xDir=(0, 1, 0),
        normal=(1, 0, 0),
    )


class SimplifiedGearBackend:
    """Build a concept gear from an outside-diameter disc and axial hub.

    The result is deliberately not an involute tooth form. It is suitable for
    envelope, layout, file-export, and assembly-pipeline validation only.
    """

    def build(self, parameters: GearParameters) -> cq.Workplane:
        """Build the simplified external gear with a through bore and hub."""
        outside_radius = parameters.module_mm * (parameters.teeth + 2) / 2.0
        hub_diameter = parameters.hub_diameter_mm or max(
            parameters.bore_diameter_mm * 1.8,
            min(outside_radius, parameters.bore_diameter_mm * 2.5),
        )
        hub_width = parameters.hub_width_mm or parameters.face_width_mm * 1.4
        hub_start = -(hub_width - parameters.face_width_mm) / 2.0

        body = (
            cq.Workplane(_yz_plane())
            .circle(outside_radius)
            .extrude(parameters.face_width_mm)
        )
        hub = (
            cq.Workplane(_yz_plane(hub_start))
            .circle(hub_diameter / 2.0)
            .extrude(hub_width)
        )
        bore = (
            cq.Workplane(_yz_plane(hub_start - 1.0))
            .circle(parameters.bore_diameter_mm / 2.0)
            .extrude(hub_width + 2.0)
        )
        return body.union(hub).cut(bore)


class InvoluteGearBackend:
    """Reserved exact-tooth backend with the same stable build interface."""

    def build(self, parameters: GearParameters) -> cq.Workplane:
        """Explain that an exact involute implementation is outside this MVP."""
        raise NotImplementedError(
            "Exact involute teeth require a dedicated verified profile backend"
        )


def build_simplified_spur_gear(
    parameters: GearParameters,
) -> cq.Workplane:
    """Build the MVP non-involute spur-gear envelope."""
    return SimplifiedGearBackend().build(parameters)

