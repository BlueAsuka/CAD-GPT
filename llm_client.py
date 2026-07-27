"""Callable OpenAI-compatible backend for OpenAI and LM Studio."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal, Sequence

from openai import OpenAI

Provider = Literal["openai", "lmstudio"]
Message = dict[str, Any]


@dataclass(frozen=True)
class LLMConfig:
    provider: Provider
    model: str
    api_key: str
    base_url: str | None = None

    @classmethod
    def from_env(cls, provider: Provider) -> "LLMConfig":
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY must be set for OpenAI")
            return cls(
                provider,
                os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                api_key,
                os.getenv("OPENAI_BASE_URL"),
            )
        if provider == "lmstudio":
            return cls(
                provider,
                os.getenv("LMSTUDIO_MODEL", "local-model"),
                os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
                os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            )
        raise ValueError(f"Unsupported provider: {provider}")


class LLMClient:
    """Small callable wrapper around ``OpenAI.chat.completions``."""

    def __init__(self, config: LLMConfig, client: OpenAI | None = None) -> None:
        self.config = config
        self._client = client or OpenAI(
            api_key=config.api_key, base_url=config.base_url
        )

    def __call__(
        self,
        messages: Sequence[Message],
        *,
        json_output: bool = False,
        json_schema: dict[str, Any] | None = None,
        schema_name: str = "response",
        temperature: float = 0.0,
    ) -> str:
        options: dict[str, Any] = {
            "model": self.config.model,
            "messages": list(messages),
            "temperature": temperature,
        }
        if json_schema is not None:
            options["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": json_schema,
                },
            }
        elif json_output:
            options["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**options)
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("The LLM returned an empty response")
        return content
