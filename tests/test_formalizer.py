"""Tests for formalizer prompt assembly and schema integration."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Sequence

from file_reader import ExampleFile
from formalizer import Message, RequirementFormalizer
from prompts.requirement_formalization import (
    REQUIREMENT_FORMALIZATION_SYSTEM_PROMPT,
    build_requirement_formalization_prompt,
)


class RecordingBackend:
    def __init__(self) -> None:
        self.messages: Sequence[Message] | None = None
        self.options: dict[str, Any] = {}

    def __call__(
        self,
        messages: Sequence[Message],
        *,
        json_output: bool = False,
        json_schema: dict[str, Any] | None = None,
        schema_name: str = "response",
        temperature: float = 0.0,
    ) -> str:
        self.messages = messages
        self.options = {
            "json_output": json_output,
            "json_schema": json_schema,
            "schema_name": schema_name,
            "temperature": temperature,
        }
        return json.dumps(
            {
                "title": "Single-stage gearbox",
                "objective": "Design a gearbox for the stated application.",
                "quantitative_requirements": [
                    {
                        "name": "Input power",
                        "semantic_key": "input_power",
                        "value": 10,
                        "unit": "kW",
                        "original_text": "Input power: 10 kW",
                    }
                ],
            }
        )


class RequirementFormalizerTests(unittest.TestCase):
    def test_prompt_contract_contains_segmentation_and_alignment_rules(self) -> None:
        prompt = build_requirement_formalization_prompt('{"type": "object"}')

        self.assertIn("Segment before extracting", prompt)
        self.assertIn("same segment or table row/column", prompt)
        self.assertIn("coverage and alignment audit", prompt)
        self.assertIn("original_text", prompt)
        self.assertIn('{"type": "object"}', prompt)

    def test_formalize_uses_external_prompt_and_records_actual_sources(self) -> None:
        backend = RecordingBackend()
        source = ExampleFile(
            path=Path("examples/requirement.txt"),
            kind="text",
            media_type="text/plain",
            content="Input power: 10 kW",
        )

        result = RequirementFormalizer(backend).formalize([source])

        self.assertIsNotNone(backend.messages)
        assert backend.messages is not None
        self.assertEqual(
            backend.messages[0]["content"],
            REQUIREMENT_FORMALIZATION_SYSTEM_PROMPT,
        )
        user_content = backend.messages[1]["content"]
        self.assertIn("Source file:", user_content[1]["text"])
        self.assertIn("requirement.txt", user_content[1]["text"])
        self.assertIn("End of source files", user_content[-1]["text"])
        self.assertEqual(backend.options["schema_name"], "design_requirement")
        self.assertEqual(result.source_files[0].path, "examples/requirement.txt")

    def test_empty_schema_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_requirement_formalization_prompt("  ")


if __name__ == "__main__":
    unittest.main()
