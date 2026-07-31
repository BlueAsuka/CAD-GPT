"""CadQuery builder for the provisional parallel key."""

from __future__ import annotations

import cadquery as cq

from gearen.models import KeyDesign


def build_parallel_key(design: KeyDesign) -> cq.Workplane:
    """Build an X-axis rectangular parallel key from width/height/length in mm."""
    if min(design.width_mm, design.height_mm, design.length_mm) <= 0:
        raise ValueError("key dimensions must be positive")
    plane = cq.Plane(origin=(0, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
    return (
        cq.Workplane(plane)
        .rect(design.width_mm, design.height_mm)
        .extrude(design.length_mm)
    )

