"""Small filesystem helpers for reproducible run artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def read_text_file(path: Path) -> str:
    """Read a requirement file as UTF-8 with an actionable decoding error."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path} must be UTF-8 encoded") from exc


def make_run_id() -> str:
    """Create a sortable UTC run identifier with microsecond uniqueness."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def ensure_run_directories(output_dir: Path) -> None:
    """Create all fixed artifact directories for one pipeline run."""
    for relative in [
        "input",
        "requirements",
        "graphs",
        "synthesis",
        "layout",
        "cad",
        "reports",
        "trace",
    ]:
        (output_dir / relative).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: BaseModel | dict[str, Any] | list[Any]) -> None:
    """Write Pydantic or plain serializable data as readable UTF-8 JSON."""
    if isinstance(data, BaseModel):
        payload = data.model_dump(mode="json")
    else:
        payload = data
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_jsonl(path: Path, item: dict[str, Any]) -> None:
    """Append one compact UTF-8 JSON object to a trace file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False) + "\n")

