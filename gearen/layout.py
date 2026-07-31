"""Deterministic spatial layout and concept-level shaft hardware selection."""

from __future__ import annotations

import json
from pathlib import Path

from gearen.calculations import estimate_shaft_diameter
from gearen.models import (
    BearingSelection,
    ComponentPlacement,
    GearCandidate,
    KeyDesign,
    LayoutResult,
    OperatingParameters,
    ShaftDesign,
)


DATA_DIR = Path(__file__).parent / "data"


def select_bearing(
    component_id: str,
    shaft_diameter_mm: float,
    *,
    life_data_available: bool,
    catalog_path: Path | None = None,
) -> BearingSelection:
    """Choose the first catalog bearing whose bore accepts the shaft diameter."""
    path = catalog_path or DATA_DIR / "bearings.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    compatible = [
        item for item in catalog if float(item["bore_diameter_mm"]) >= shaft_diameter_mm
    ]
    if not compatible:
        raise ValueError(f"no catalog bearing accepts shaft diameter {shaft_diameter_mm}")
    item = min(compatible, key=lambda value: float(value["bore_diameter_mm"]))
    life_status = "provisional" if life_data_available else "blocked"
    reason = (
        "概念目录选型；仍需载荷分配和额定寿命校核"
        if life_data_available
        else "缺少工作小时和载荷谱，轴承寿命校核被阻塞"
    )
    return BearingSelection(
        component_id=component_id,
        designation=str(item["designation"]),
        bore_diameter_mm=float(item["bore_diameter_mm"]),
        outer_diameter_mm=float(item["outer_diameter_mm"]),
        width_mm=float(item["width_mm"]),
        life_check_status=life_status,
        reason=reason,
    )


def select_parallel_key(shaft_diameter_mm: float, face_width_mm: float) -> KeyDesign:
    """Select a simplified metric key cross-section from output shaft diameter."""
    if shaft_diameter_mm <= 0 or face_width_mm <= 0:
        raise ValueError("shaft diameter and face width must be positive")
    bands = [
        (22, 6, 6),
        (30, 8, 7),
        (38, 10, 8),
        (44, 12, 8),
        (50, 14, 9),
        (60, 16, 10),
    ]
    for maximum, width, height in bands:
        if shaft_diameter_mm <= maximum:
            return KeyDesign(
                width_mm=width,
                height_mm=height,
                length_mm=min(max(face_width_mm * 0.8, 20.0), 60.0),
            )
    raise ValueError("shaft diameter is outside the simplified key table")


class SingleStageLayoutSolver:
    """Place the supported single-stage gearbox using fixed geometric rules."""

    def solve(
        self,
        candidate: GearCandidate,
        operating: OperatingParameters,
        *,
        life_data_available: bool,
        shaft_safety_factor: float = 2.0,
        allowable_shear_stress_MPa: float = 40.0,
    ) -> LayoutResult:
        """Return deterministic X-axis shaft and Y-separated centre positions."""
        input_shaft = estimate_shaft_diameter(
            "input_shaft",
            operating.input_torque_Nm,
            shaft_safety_factor,
            allowable_shear_stress_MPa,
        )
        output_shaft = estimate_shaft_diameter(
            "output_shaft",
            operating.estimated_output_torque_Nm,
            shaft_safety_factor,
            allowable_shear_stress_MPa,
        )
        bearings = self._bearings(input_shaft.selected_diameter_mm,
                                  output_shaft.selected_diameter_mm,
                                  life_data_available)
        output_key = select_parallel_key(
            output_shaft.selected_diameter_mm, candidate.face_width_mm
        )
        placements = self._placements(
            candidate, input_shaft, output_shaft, bearings, output_key
        )
        return LayoutResult(
            centre_distance_mm=candidate.centre_distance_mm,
            placements=placements,
            input_shaft=input_shaft,
            output_shaft=output_shaft,
            bearings=bearings,
            output_key=output_key,
        )

    @staticmethod
    def _bearings(
        input_diameter: float, output_diameter: float, life_data_available: bool
    ) -> list[BearingSelection]:
        """Select two matching bearings for each shaft."""
        return [
            select_bearing(name, diameter, life_data_available=life_data_available)
            for name, diameter in [
                ("input_bearing_left", input_diameter),
                ("input_bearing_right", input_diameter),
                ("output_bearing_left", output_diameter),
                ("output_bearing_right", output_diameter),
            ]
        ]

    def _placements(
        self,
        candidate: GearCandidate,
        input_shaft: ShaftDesign,
        output_shaft: ShaftDesign,
        bearings: list[BearingSelection],
        output_key: KeyDesign,
    ) -> list[ComponentPlacement]:
        """Place gears at X=0 and bearings symmetrically on their two sides."""
        centre = candidate.centre_distance_mm
        face = candidate.face_width_mm
        shaft_length = max(face + 100.0, 150.0)
        placements = [
            self._place("input_shaft", (-shaft_length / 2, 0, 0),
                        (shaft_length, input_shaft.selected_diameter_mm,
                         input_shaft.selected_diameter_mm),
                        "fixed input axis"),
            self._place("output_shaft", (-shaft_length / 2, centre, 0),
                        (shaft_length, output_shaft.selected_diameter_mm,
                         output_shaft.selected_diameter_mm),
                        "parallel axis separated by centre distance"),
            self._place("pinion", (-face / 2, 0, 0),
                        (face, candidate.outside_diameter_pinion_mm,
                         candidate.outside_diameter_pinion_mm),
                        "pitch centres aligned", "input_shaft"),
            self._place("gear_wheel", (-face / 2, centre, 0),
                        (face, candidate.outside_diameter_wheel_mm,
                         candidate.outside_diameter_wheel_mm),
                        "same X span as pinion", "output_shaft"),
        ]
        bearing_map = {item.component_id: item for item in bearings}
        clearance = 15.0
        for shaft_name, y in [("input", 0.0), ("output", centre)]:
            for side, sign in [("left", -1.0), ("right", 1.0)]:
                bearing = bearing_map[f"{shaft_name}_bearing_{side}"]
                x = sign * (face / 2 + clearance + bearing.width_mm / 2)
                placements.append(
                    self._place(
                        bearing.component_id,
                        (x, y, 0),
                        (bearing.width_mm, bearing.outer_diameter_mm,
                         bearing.outer_diameter_mm),
                        f"{side} support outside gear face",
                        f"{shaft_name}_shaft",
                    )
                )
        placements.extend(
            self._key_and_housing(
                candidate,
                output_key,
                shaft_length,
                output_shaft.selected_diameter_mm,
            )
        )
        return placements

    @staticmethod
    def _key_and_housing(
        candidate: GearCandidate,
        output_key: KeyDesign,
        shaft_length: float,
        output_diameter: float,
    ) -> list[ComponentPlacement]:
        """Place the key and one shared enclosure envelope."""
        centre = candidate.centre_distance_mm
        radial = max(
            candidate.outside_diameter_pinion_mm,
            candidate.outside_diameter_wheel_mm,
        ) / 2
        housing_y = centre + 2 * radial + 40.0
        housing_z = 2 * radial + 40.0
        return [
            ComponentPlacement(
                component_id="output_key",
                origin=(
                    -output_key.length_mm / 2,
                    centre,
                    output_diameter / 2 - output_key.height_mm / 2,
                ),
                axis=(1, 0, 0),
                length_axis="X",
                mating_reference="gear_wheel",
                placement_reason="centred in output gear seat",
                estimated_bounding_box=(
                    output_key.length_mm, output_key.width_mm, output_key.height_mm
                ),
            ),
            ComponentPlacement(
                component_id="housing_lower",
                origin=(-shaft_length / 2 - 20, -radial - 20, -radial - 20),
                axis=(1, 0, 0),
                length_axis="X",
                placement_reason="encloses gears, bearings, and radial clearance",
                estimated_bounding_box=(shaft_length + 40, housing_y, housing_z),
            ),
            ComponentPlacement(
                component_id="housing_cover",
                origin=(-shaft_length / 2 - 20, -radial - 20, 0),
                axis=(1, 0, 0),
                length_axis="X",
                mating_reference="housing_lower",
                placement_reason="upper half at shaft split plane",
                estimated_bounding_box=(shaft_length + 40, housing_y, housing_z / 2),
            ),
        ]

    @staticmethod
    def _place(
        component_id: str,
        origin: tuple[float, float, float],
        box: tuple[float, float, float],
        reason: str,
        mating: str | None = None,
    ) -> ComponentPlacement:
        """Build one standard X-axis placement record."""
        return ComponentPlacement(
            component_id=component_id,
            origin=origin,
            axis=(1, 0, 0),
            length_axis="X",
            mating_reference=mating,
            placement_reason=reason,
            estimated_bounding_box=box,
        )
