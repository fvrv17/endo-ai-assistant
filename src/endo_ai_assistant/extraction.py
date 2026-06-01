from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Protocol

from .models import EndoscopyReport, EndoscopyType, ExtractedFindings
from .schema_tools import make_strict_json_schema


EXTRACTION_SYSTEM_PROMPT = """
You extract structured endoscopy findings from a doctor's free-form note.

Rules:
- Extract only facts explicitly present in the doctor's input.
- Never add a diagnosis, measurement, medication, or anatomical location that is not in the input.
- Use null for any field that is not explicitly stated.
- For every observation, evidence_text must be an exact substring from the doctor's input.
- Return only data that conforms to the ExtractedFindings JSON schema.
""".strip()


class EndoscopyExtractor(Protocol):
    def extract(
        self,
        raw_input: str,
        exam_type: EndoscopyType,
        indication: Optional[str] = None,
    ) -> EndoscopyReport:
        ...


def extraction_json_schema() -> Dict[str, Any]:
    return ExtractedFindings.model_json_schema()


def strict_extraction_json_schema() -> Dict[str, Any]:
    return make_strict_json_schema(extraction_json_schema())


def build_report_from_extraction(
    *,
    raw_input: str,
    exam_type: EndoscopyType,
    extraction_payload: Mapping[str, Any],
    indication: Optional[str] = None,
) -> EndoscopyReport:
    extracted = ExtractedFindings.model_validate(extraction_payload)
    return EndoscopyReport(
        exam_type=exam_type,
        raw_input=raw_input,
        indication=indication,
        findings=extracted.findings,
    )
