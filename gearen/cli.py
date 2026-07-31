"""Command-line interface for the deterministic gearbox design pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gearen.cad.assembly import build_gearbox_assembly, export_all
from gearen.design_graph import DesignGraph
from gearen.io_utils import read_text_file, write_json
from gearen.models import (
    GearCandidate,
    GearboxRequirement,
    LayoutResult,
    RequirementReview,
)
from gearen.pipeline import GearboxDesignPipeline
from gearen.validation import validate_design


DEFAULT_REQUIREMENT_FILE = Path("requirements/requirements_text.txt")


def _design(args: argparse.Namespace) -> int:
    """Run a design from inline text or a UTF-8 requirement file."""
    text = args.text if args.text is not None else read_text_file(args.file)
    result = GearboxDesignPipeline(output_root=args.output_root).run(text)
    requirement = result.requirement
    print(f"阶段: {result.stage.value}")
    print(f"需求: {requirement.objective}")
    print(f"关键假设: {', '.join(requirement.assumptions)}")
    print(f"缺失项: {', '.join(result.requirement_review.unresolved_requirements)}")
    if result.operating_parameters:
        values = result.operating_parameters
        print(f"输出转速: {values.output_speed_rpm:.3f} rpm")
        print(f"输入扭矩: {values.input_torque_Nm:.3f} N·m")
    print(f"输出目录: {result.output_dir}")
    if result.selected_candidate:
        selected = result.selected_candidate
        print(f'候选数量: {result.candidate_count}')
        print(
            f'选中参数: z1={selected.z1}, z2={selected.z2}, '
            f'm={selected.module_mm:g} mm, b={selected.face_width_mm:g} mm'
        )
        print(f'中心距: {selected.centre_distance_mm:.3f} mm')
    if result.cad_files:
        print('CAD文件:')
        for path in result.cad_files:
            print(f'  - {path.name}')
    if result.validation_report:
        report = result.validation_report
        print(
            f'验证摘要: overall={report.overall_status}, '
            f'counts={report.summary}'
        )
    if result.requirement_review.blocking_issues:
        print("阻塞项: " + "; ".join(result.requirement_review.blocking_issues))
        return 2
    return 0


def _load_json(path: Path) -> dict | list:
    '''Load one UTF-8 JSON artifact from an existing run.'''
    if not path.exists():
        raise FileNotFoundError(f'run artifact does not exist: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def _inspect(args: argparse.Namespace) -> int:
    '''Print a concise summary without changing a completed run.'''
    run_dir = args.run_dir
    requirement = _load_json(
        run_dir / 'requirements' / 'requirement.json'
    )
    candidate = _load_json(
        run_dir / 'synthesis' / 'selected_candidate.json'
    )
    validation = _load_json(
        run_dir / 'reports' / 'validation_report.json'
    )
    objective = requirement['objective']
    z1 = candidate['z1']
    z2 = candidate['z2']
    module = candidate['module_mm']
    centre = candidate['centre_distance_mm']
    overall = validation['overall_status']
    summary = validation['summary']
    print(f'需求: {objective}')
    print(
        f'齿轮: z1={z1}, z2={z2}, '
        f'm={module} mm, 中心距={centre} mm'
    )
    print(f'验证: {overall} {summary}')
    print(f'运行目录: {run_dir}')
    return 0


def _validate_existing(args: argparse.Namespace) -> int:
    '''Rebuild CAD in memory and rerun transparent validation checks.'''
    run_dir = args.run_dir
    requirement = GearboxRequirement.model_validate(
        _load_json(run_dir / 'requirements' / 'requirement.json')
    )
    review = RequirementReview.model_validate(
        _load_json(run_dir / 'requirements' / 'requirement_review.json')
    )
    graph = DesignGraph.from_dict(
        _load_json(run_dir / 'graphs' / 'product_graph.json')
    )
    candidate = GearCandidate.model_validate(
        _load_json(run_dir / 'synthesis' / 'selected_candidate.json')
    )
    layout = LayoutResult.model_validate(
        _load_json(run_dir / 'layout' / 'layout.json')
    )
    _, parts = build_gearbox_assembly(candidate, layout)
    report = validate_design(requirement, review, graph, candidate, layout, parts)
    write_json(run_dir / 'reports' / 'validation_report.json', report)
    print(f'验证: {report.overall_status} {report.summary}')
    return 1 if report.overall_status == 'failed' else 0


def _regenerate_cad(args: argparse.Namespace) -> int:
    '''Regenerate CAD solely from selected candidate and saved layout.'''
    run_dir = args.run_dir
    candidate = GearCandidate.model_validate(
        _load_json(run_dir / 'synthesis' / 'selected_candidate.json')
    )
    layout = LayoutResult.model_validate(
        _load_json(run_dir / 'layout' / 'layout.json')
    )
    _, _, files = export_all(candidate, layout, run_dir / 'cad')
    cad_dir = run_dir / 'cad'
    print(f'已重新生成 {len(files)} 个CAD文件: {cad_dir}')
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the intentionally small argparse command tree."""
    parser = argparse.ArgumentParser(prog="gearen")
    commands = parser.add_subparsers(dest="command", required=True)
    design = commands.add_parser("design", help="run a gearbox concept design")
    source = design.add_mutually_exclusive_group()
    source.add_argument("--file", type=Path, default=DEFAULT_REQUIREMENT_FILE)
    source.add_argument("--text")
    design.add_argument("--output-root", type=Path, default=Path("outputs"))
    design.set_defaults(handler=_design)
    inspect_command = commands.add_parser(
        'inspect', help='inspect a completed run'
    )
    inspect_command.add_argument('run_dir', type=Path)
    inspect_command.set_defaults(handler=_inspect)
    validate_command = commands.add_parser(
        'validate', help='rerun validation for a completed run'
    )
    validate_command.add_argument('run_dir', type=Path)
    validate_command.set_defaults(handler=_validate_existing)
    regenerate = commands.add_parser(
        'regenerate-cad', help='regenerate CAD from saved artifacts'
    )
    regenerate.add_argument('run_dir', type=Path)
    regenerate.set_defaults(handler=_regenerate_cad)
    return parser


def main() -> int:
    """Parse command-line arguments and dispatch one command."""
    args = build_parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
