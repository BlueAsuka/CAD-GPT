"""CadQuery builder for a simple coaxial stepped shaft."""

from __future__ import annotations

import cadquery as cq

from gearen.models import ShaftDesign


def _yz_plane(x_position: float) -> cq.Plane:
    """Return an X-normal work plane at an axial coordinate."""
    return cq.Plane(
        origin=(x_position, 0, 0),
        xDir=(0, 1, 0),
        normal=(1, 0, 0),
    )


def build_stepped_shaft(design: ShaftDesign) -> cq.Workplane:
    """Build contiguous X-axis cylinders from the provisional shaft segments."""
    if not design.segments:
        raise ValueError("shaft design must contain at least one segment")
    result: cq.Workplane | None = None
    x_position = 0.0
    for segment in design.segments:
        cylinder = (
            cq.Workplane(_yz_plane(x_position))
            .circle(segment.diameter_mm / 2.0)
            .extrude(segment.length_mm)
        )
        result = cylinder if result is None else result.union(cylinder)
        x_position += segment.length_mm
    assert result is not None
    return result

