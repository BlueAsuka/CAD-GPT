"""Independent local file reader with no LLM or provider dependencies."""

from __future__ import annotations

import argparse
import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

FileKind = Literal["text", "image"]
TEXT_EXTENSIONS = {".csv", ".json", ".md", ".py", ".scad", ".toml", ".txt", ".yaml", ".yml"}
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}


@dataclass(frozen=True)
class ExampleFile:
    """Provider-independent content read from a local source file."""

    path: Path
    kind: FileKind
    media_type: str
    content: str | bytes

    def as_message_content(self) -> list[dict[str, Any]]:
        """Convert local content to OpenAI-compatible multimodal message parts."""
        label = {"type": "text", "text": f"Source file: {self.path}"}
        if self.kind == "text":
            return [
                label,
                {"type": "text", "text": str(self.content)},
            ]
        encoded = base64.b64encode(bytes(self.content)).decode("ascii")
        return [
            label,
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{self.media_type};base64,{encoded}",
                },
            },
        ]


class ExampleReader:
    """Read supported text files and images from a file or directory."""

    def read_file(self, path: str | Path) -> ExampleFile:
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"Not a file: {file_path}")
        suffix = file_path.suffix.lower()
        media_type = mimetypes.guess_type(file_path.name)[0]
        if suffix in TEXT_EXTENSIONS:
            return ExampleFile(
                file_path,
                "text",
                media_type or "text/plain",
                file_path.read_text(encoding="utf-8-sig"),
            )
        if suffix in IMAGE_EXTENSIONS:
            return ExampleFile(
                file_path,
                "image",
                media_type or "application/octet-stream",
                file_path.read_bytes(),
            )
        raise ValueError(f"Unsupported file type {suffix!r}: {file_path}")

    def supported_files(self, directory: str | Path) -> list[Path]:
        root = Path(directory)
        if not root.is_dir():
            raise NotADirectoryError(f"Directory not found: {root}")
        supported = TEXT_EXTENSIONS | IMAGE_EXTENSIONS
        return sorted(
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in supported
        )

    def read(self, path: str | Path = "examples") -> list[ExampleFile]:
        source = Path(path)
        if source.is_file():
            return [self.read_file(source)]
        return [self.read_file(file_path) for file_path in self.supported_files(source)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Read local example files")
    parser.add_argument("input", nargs="?", default="examples")
    args = parser.parse_args()

    for source in ExampleReader().read(args.input):
        if source.kind == "text":
            print(f"--- {source.path} ---\n{source.content}\n")
        else:
            print(
                f"--- {source.path} ---\n"
                f"<{source.media_type}, {len(source.content)} bytes>\n"
            )


if __name__ == "__main__":
    main()
