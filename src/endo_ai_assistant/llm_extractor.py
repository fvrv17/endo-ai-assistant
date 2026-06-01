from __future__ import annotations

from typing import Any, List, Mapping, Optional, Protocol

from .extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    build_report_from_extraction,
    extraction_json_schema,
)
from .models import EndoscopyReport, EndoscopyType, ZONES_BY_EXAM_TYPE
from .nomenclature import (
    OBSERVATION_LABELS,
    OBSERVATION_SYNONYMS,
    ZONE_LABELS,
    ZONE_SYNONYMS,
)


class StructuredLLMClient(Protocol):
    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        ...


class LLMExtractor:
    def __init__(self, client: StructuredLLMClient) -> None:
        self.client = client

    def extract(
        self,
        raw_input: str,
        exam_type: EndoscopyType,
        indication: Optional[str] = None,
    ) -> EndoscopyReport:
        payload = self.client.complete_json(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=build_extraction_user_prompt(
                raw_input=raw_input,
                exam_type=exam_type,
                indication=indication,
            ),
            json_schema=extraction_json_schema(),
        )
        return build_report_from_extraction(
            raw_input=raw_input,
            exam_type=exam_type,
            indication=indication,
            extraction_payload=payload,
        )


def build_extraction_user_prompt(
    *,
    raw_input: str,
    exam_type: EndoscopyType,
    indication: Optional[str] = None,
) -> str:
    lines: List[str] = [
        "Extract findings from this endoscopy note.",
        "",
        f"Exam type: {exam_type.value}",
        f"Indication: {indication or 'not provided'}",
        "",
        "Return ExtractedFindings only. Do not return raw_input, exam_type, or indication.",
        "Use null for missing values and [] for empty lists.",
        "",
        "Nomenclature:",
        _nomenclature_section(exam_type),
        "",
        "Doctor input:",
        "```text",
        raw_input.strip(),
        "```",
    ]
    return "\n".join(lines)


def _nomenclature_section(exam_type: EndoscopyType) -> str:
    lines = ["Allowed zones:"]
    for zone in sorted(ZONES_BY_EXAM_TYPE[exam_type], key=lambda item: item.value):
        lines.append(
            f"- {zone.value}: {ZONE_LABELS[zone]} "
            f"(synonyms: {_format_synonyms(ZONE_SYNONYMS.get(zone, []))})"
        )

    lines.append("Allowed finding types:")
    for observation_type in sorted(OBSERVATION_LABELS, key=lambda item: item.value):
        lines.append(
            f"- {observation_type.value}: {OBSERVATION_LABELS[observation_type]} "
            f"(synonyms: {_format_synonyms(OBSERVATION_SYNONYMS.get(observation_type, []))})"
        )

    return "\n".join(lines)


def _format_synonyms(synonyms: List[str]) -> str:
    if not synonyms:
        return "none"
    return ", ".join(synonyms[:6])
