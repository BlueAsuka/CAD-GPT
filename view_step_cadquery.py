"""
View a STEP file with CadQuery's built-in VTK viewer.

Usage:
    python view_step_cadquery.py path/to/model.step

Requires a CadQuery installation that includes cadquery.vis.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cadquery as cq
from cadquery.vis import show


def load_step(step_path: Path):
    if not step_path.is_file():
        raise FileNotFoundError(f"STEP file not found: {step_path}")

    model = cq.importers.importStep(str(step_path))

    # A STEP assembly may be flattened into a Workplane containing many solids.
    solid_count = len(model.solids().vals())
    print(f"Loaded: {step_path}")
    print(f"Solids found: {solid_count}")

    if solid_count == 0:
        raise RuntimeError(
            "The STEP importer returned no solids. "
            "Check the source STEP file and CadQuery/OpenCascade installation."
        )

    return model


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize a STEP file with CadQuery.")
    parser.add_argument("step_file", type=Path, help="Path to a .step or .stp file")
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=None,
        help="Optional PNG screenshot path",
    )
    args = parser.parse_args()

    model = load_step(args.step_file.resolve())

    if args.screenshot:
        show(
            model,
            width=1200,
            height=900,
            screenshot=str(args.screenshot.resolve()),
            interact=False,
        )
        print(f"Screenshot written to: {args.screenshot.resolve()}")
    else:
        # This call is blocking and opens CadQuery's VTK visualization window.
        show(model, width=1200, height=900)


if __name__ == "__main__":
    main()
