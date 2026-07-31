"""End-to-end artifact and legacy-isolation tests with no external API."""

from pathlib import Path

from gearen.io_utils import read_text_file
from gearen.models import PipelineStage
from gearen.pipeline import GearboxDesignPipeline


ROOT = Path(__file__).resolve().parents[1]


def test_default_input_completes_and_exports_all_artifacts(tmp_path) -> None:
    """Run the documented default input through graphs, CAD, and reports."""
    text = read_text_file(ROOT / "requirements" / "requirements_text.txt")
    result = GearboxDesignPipeline(tmp_path / "outputs").run(text)
    assert result.stage == PipelineStage.COMPLETE
    assert result.requirement.output_speed.value == 480
    assert result.validation_report is not None
    assert result.validation_report.summary.get("failed", 0) == 0
    expected = [
        "requirements/requirement.json",
        "requirements/requirement_review.json",
        "graphs/requirement_graph.json",
        "graphs/product_graph.json",
        "graphs/product_graph.graphml",
        "synthesis/candidates.json",
        "synthesis/selected_candidate.json",
        "layout/layout.json",
        "cad/pinion.step",
        "cad/gearbox_assembly.step",
        "cad/gearbox_assembly.stl",
        "reports/calculation_report.md",
        "reports/validation_report.json",
        "reports/design_summary.md",
        "trace/pipeline_trace.jsonl",
    ]
    assert all((result.output_dir / relative).exists() for relative in expected)


def test_new_modules_do_not_depend_on_paper_code() -> None:
    """Keep the new implementation completely isolated from paper internals."""
    for path in (ROOT / "gearen").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "paper_code" not in source, path

