"""Simplified deep-groove bearing envelope for concept assemblies."""

from __future__ import annotations

import cadquery as cq

from gearen.models import BearingSelection


def _yz_plane(x_position: float) -> cq.Plane:
    """Return an X-normal work plane at an axial coordinate."""
    return cq.Plane(
        origin=(x_position, 0, 0),
        xDir=(0, 1, 0),
        normal=(1, 0, 0),
    )


def build_simplified_bearing(selection: BearingSelection) -> cq.Workplane:
    """Build an annular bearing with shallow face grooves separating its zones."""
    outer_radius = selection.outer_diameter_mm / 2.0
    bore_radius = selection.bore_diameter_mm / 2.0
    if bore_radius <= 0 or outer_radius <= bore_radius or selection.width_mm <= 0:
        raise ValueError("bearing dimensions must satisfy OD > bore > 0")

    ring = (
        cq.Workplane(_yz_plane(-selection.width_mm / 2.0))
        .circle(outer_radius)
        .circle(bore_radius)
        .extrude(selection.width_mm)
    )
    # Two shallow annular cuts visually separate inner/outer rings from the
    # rolling-element zone without pretending to model real contacts.
    rolling_inner = bore_radius + (outer_radius - bore_radius) * 0.32
    rolling_outer = bore_radius + (outer_radius - bore_radius) * 0.68
    groove_depth = min(0.6, selection.width_mm * 0.05)
    face_grooves = (
        cq.Workplane(_yz_plane(-selection.width_mm / 2.0))
        .circle(rolling_outer)
        .circle(rolling_inner)
        .extrude(groove_depth)
    )
    return ring.cut(face_grooves)

