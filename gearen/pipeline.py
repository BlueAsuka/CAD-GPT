"""Explicit, gearbox-specific pipeline; later phases extend its fixed data flow."""

from __future__ import annotations

from pathlib import Path

from gearen.calculations import derive_operating_parameters
from gearen.cad.assembly import export_all
from gearen.candidate_search import generate_candidates, select_candidate
from gearen.design_graph import DesignGraph, build_requirement_graph
from gearen.grammar_rules import apply_graph_grammar
from gearen.io_utils import (
    append_jsonl,
    ensure_run_directories,
    make_run_id,
    write_json,
)
from gearen.layout import SingleStageLayoutSolver
from gearen.models import GearCandidate, PipelineResult, PipelineStage
from gearen.requirement_parser import RuleBasedRequirementParser
from gearen.requirement_validator import validate_requirement
from gearen.reporting import write_reports
from gearen.validation import validate_design


class GearboxDesignPipeline:
    """Run the deterministic single-stage gearbox concept-design workflow."""

    def __init__(self, output_root: Path | str = "outputs") -> None:
        """Configure where independently identified run directories are created."""
        self.output_root = Path(output_root)
        self.parser = RuleBasedRequirementParser()

    def run(self, requirement_text: str) -> PipelineResult:
        """Run the currently implemented stages and persist inspectable artifacts."""
        run_id = make_run_id()
        output_dir = self.output_root / run_id
        ensure_run_directories(output_dir)
        (output_dir / "input" / "requirement_text.txt").write_text(
            requirement_text, encoding="utf-8"
        )

        self._trace(output_dir, PipelineStage.PARSE_REQUIREMENT)
        requirement = self.parser.parse(requirement_text)
        write_json(output_dir / "requirements" / "requirement.json", requirement)

        self._trace(output_dir, PipelineStage.VALIDATE_REQUIREMENT)
        review = validate_requirement(requirement)
        write_json(
            output_dir / 'requirements' / 'requirement.json', requirement
        )
        write_json(
            output_dir / "requirements" / "requirement_review.json", review
        )
        if not review.is_valid:
            self._trace(output_dir, PipelineStage.NEED_USER_INPUT)
            return PipelineResult(
                run_id=run_id,
                output_dir=output_dir,
                stage=PipelineStage.NEED_USER_INPUT,
                requirement=requirement,
                requirement_review=review,
            )

        self._trace(output_dir, PipelineStage.BUILD_GRAPH)
        requirement_graph = build_requirement_graph(requirement)
        requirement_graph.export_json(
            output_dir / 'graphs' / 'requirement_graph.json'
        )

        self._trace(output_dir, PipelineStage.GENERATE_TOPOLOGY)
        product_graph, rule_results = apply_graph_grammar(
            requirement_graph, requirement
        )
        product_graph.export_json(output_dir / 'graphs' / 'product_graph.json')
        product_graph.export_graphml(
            output_dir / 'graphs' / 'product_graph.graphml'
        )
        write_json(
            output_dir / 'trace' / 'grammar_trace.json',
            [
                {
                    'rule_id': item.rule_id,
                    'applied': item.applied,
                    'added_nodes': list(item.added_nodes),
                    'message': item.message,
                }
                for item in rule_results
            ],
        )

        self._trace(output_dir, PipelineStage.CALCULATE_PARAMETERS)
        operating = derive_operating_parameters(
            requirement,
            efficiency=float(review.assumptions["efficiency"]),
            pressure_angle_deg=float(review.assumptions["pressure_angle_deg"]),
        )
        write_json(
            output_dir / "synthesis" / "operating_parameters.json", operating
        )
        self._trace(output_dir, PipelineStage.SEARCH_CANDIDATES)
        candidates = generate_candidates(operating)
        selected = select_candidate(candidates)
        write_json(
            output_dir / 'synthesis' / 'candidates.json',
            [item.model_dump(mode='json') for item in candidates],
        )
        write_json(
            output_dir / 'synthesis' / 'selected_candidate.json', selected
        )
        self._add_candidate_parameters(product_graph, selected)
        product_graph.export_json(output_dir / 'graphs' / 'product_graph.json')
        product_graph.export_graphml(
            output_dir / 'graphs' / 'product_graph.graphml'
        )

        self._trace(output_dir, PipelineStage.SOLVE_LAYOUT)
        life_data_available = (
            requirement.operating_hours.value is not None
            and '载荷谱' not in review.unresolved_requirements
        )
        layout = SingleStageLayoutSolver().solve(
            selected,
            operating,
            life_data_available=life_data_available,
            shaft_safety_factor=float(review.assumptions['shaft_safety_factor']),
            allowable_shear_stress_MPa=float(
                review.assumptions['allowable_shaft_shear_stress_MPa']
            ),
        )
        write_json(output_dir / 'layout' / 'layout.json', layout)

        self._trace(output_dir, PipelineStage.GENERATE_CAD)
        _, cad_parts, cad_files = export_all(
            selected, layout, output_dir / 'cad'
        )

        self._trace(output_dir, PipelineStage.VALIDATE_DESIGN)
        validation = validate_design(
            requirement,
            review,
            product_graph,
            selected,
            layout,
            cad_parts,
        )
        write_reports(
            output_dir,
            requirement,
            review,
            operating,
            selected,
            layout,
            validation,
            cad_files,
        )

        self._trace(output_dir, PipelineStage.COMPLETE)
        return PipelineResult(
            run_id=run_id,
            output_dir=output_dir,
            stage=PipelineStage.COMPLETE,
            requirement=requirement,
            requirement_review=review,
            operating_parameters=operating,
            candidate_count=len(candidates),
            selected_candidate=selected,
            layout=layout,
            cad_files=cad_files,
            validation_report=validation,
        )

    @staticmethod
    def _add_candidate_parameters(
        product_graph: DesignGraph, candidate: GearCandidate
    ) -> None:
        '''Attach serializable calculated values to product-graph nodes.'''
        common = {
            'module_mm': candidate.module_mm,
            'face_width_mm': candidate.face_width_mm,
            'pressure_angle_deg': candidate.pressure_angle_deg,
        }
        product_graph.update_node(
            'pinion',
            geometry_parameters={
                **common,
                'teeth': candidate.z1,
                'pitch_diameter_mm': candidate.pitch_diameter_pinion_mm,
                'outside_diameter_mm': candidate.outside_diameter_pinion_mm,
            },
        )
        product_graph.update_node(
            'gear_wheel',
            geometry_parameters={
                **common,
                'teeth': candidate.z2,
                'pitch_diameter_mm': candidate.pitch_diameter_wheel_mm,
                'outside_diameter_mm': candidate.outside_diameter_wheel_mm,
            },
        )
        product_graph.update_node(
            'gear_mesh',
            attributes={
                'centre_distance_mm': candidate.centre_distance_mm,
                'tangential_force_N': candidate.tangential_force_N,
                'radial_force_N': candidate.radial_force_N,
            },
        )

    @staticmethod
    def _trace(output_dir: Path, stage: PipelineStage) -> None:
        """Record an explicit stage transition in the run trace."""
        append_jsonl(
            output_dir / "trace" / "pipeline_trace.jsonl",
            {"stage": stage.value},
        )
