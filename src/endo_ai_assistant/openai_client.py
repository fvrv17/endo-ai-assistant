from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from .schema_tools import make_strict_json_schema


DEFAULT_OPENAI_MODEL = "gpt-5.5"


class OpenAIStructuredClient:
    def __init__(
        self,
        *,
        model: str = DEFAULT_OPENAI_MODEL,
        client: Optional[Any] = None,
    ) -> None:
        self.model = model
        self.client = client or _build_default_client()

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "extracted_findings",
                    "description": "Structured endoscopy findings extracted from the doctor's input.",
                    "schema": make_strict_json_schema(json_schema),
                    "strict": True,
                }
            },
        )
        return _decode_response_json(response)


def _build_default_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "OpenAIStructuredClient requires the 'openai' package. "
            "Install project requirements first."
        ) from exc
    return OpenAI()


def _decode_response_json(response: Any) -> Mapping[str, Any]:
    parsed = getattr(response, "output_parsed", None)
    if isinstance(parsed, Mapping):
        return parsed
    if parsed is not None and hasattr(parsed, "model_dump"):
        return parsed.model_dump()

    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str):
        return json.loads(output_text)

    raise RuntimeError("OpenAI response did not contain structured JSON output")
