"""Convert requirement source files into a validated Pydantic model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Protocol, Sequence

from file_reader import ExampleFile, ExampleReader
from prompts.requirement_formalization import (
    REQUIREMENT_FORMALIZATION_SYSTEM_PROMPT,
    build_requirement_formalization_prompt,
)
from schema.gearbox_requirement_schema import DesignRequirement

Message = dict[str, Any]


class LLMBackend(Protocol):
    def __call__(
        self,
        messages: Sequence[Message],
        *,
        json_output: bool = False,
        json_schema: dict[str, Any] | None = None,
        schema_name: str = "response",
        temperature: float = 0.0,
    ) -> str: ...


class RequirementFormalizer:
    """Extract and validate formal requirements using a callable backend."""

    def __init__(self, backend: LLMBackend, max_language_retries: int = 1) -> None:
        if max_language_retries < 0:
            raise ValueError("max_language_retries must be non-negative")
        self.backend = backend
        self.max_language_retries = max_language_retries

    def formalize(self, files: Sequence[ExampleFile]) -> DesignRequirement:
        if not files:
            raise ValueError("At least one source file is required")

        requirement_schema = DesignRequirement.model_json_schema()
        schema_json = json.dumps(requirement_schema, ensure_ascii=False)
        content = [{
            "type": "text",
            "text": build_requirement_formalization_prompt(schema_json),
        }]
        for source in files:
            content.extend(source.as_message_content())
        content.append({
            "type": "text",
            "text": (
                "End of source files. Perform the coverage and alignment audit, "
                "then return only the schema-valid JSON object."
            ),
        })

        messages: list[Message] = [
            {
                "role": "system",
                "content": REQUIREMENT_FORMALIZATION_SYSTEM_PROMPT,
            },
            {"role": "user", "content": content},
        ]
        raw = self.backend(
            messages,
            json_output=True,
            json_schema=requirement_schema,
            schema_name="design_requirement",
            temperature=0.0,
        )
        payload = json.loads(raw)
        payload["source_files"] = [str(source.path) for source in files]
        result = DesignRequirement.model_validate(payload)
        return result


def main() -> None:
    from llm_client import LLMClient, LLMConfig

    parser = argparse.ArgumentParser(description="Formalize design requirements")
    parser.add_argument("input", nargs="?", default="examples")
    parser.add_argument(
        "--provider", choices=("openai", "lmstudio"), default="lmstudio"
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    sources = ExampleReader().read(args.input)
    backend = LLMClient(LLMConfig.from_env(args.provider))
    result = RequirementFormalizer(backend).formalize(sources)
    output = result.model_dump_json(indent=2)

    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
