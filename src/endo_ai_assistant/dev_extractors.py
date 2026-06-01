from __future__ import annotations

import re
from typing import Dict, List, Optional

from .extraction import build_report_from_extraction
from .models import (
    AnatomicalZone,
    EndoscopyReport,
    EndoscopyType,
    ObservationType,
)


class SyntheticGastroscopyExtractor:
    """Tiny offline extractor for synthetic demos and eval baselines.

    This is deliberately narrow. It lets the project run end-to-end before an
    LLM provider is connected, but it is not clinical extraction logic.
    """

    def extract(
        self,
        raw_input: str,
        exam_type: EndoscopyType = EndoscopyType.GASTROSCOPY,
        indication: Optional[str] = None,
    ) -> EndoscopyReport:
        payload = {"findings": _extract_findings(raw_input, exam_type)}

        return build_report_from_extraction(
            raw_input=raw_input,
            exam_type=exam_type,
            indication=indication,
            extraction_payload=payload,
        )


def _extract_findings(raw_input: str, exam_type: EndoscopyType) -> List[dict]:
    findings_by_zone: Dict[AnatomicalZone, dict] = {}

    for sentence in _clinical_sentences(raw_input):
        zone = _zone_from_sentence(sentence, exam_type)
        if zone is None:
            continue

        observations = _observations_from_sentence(sentence)
        if not observations:
            continue

        if zone not in findings_by_zone:
            findings_by_zone[zone] = {"zone": zone, "observations": []}
        findings_by_zone[zone]["observations"].extend(observations)

    return list(findings_by_zone.values())


def _clinical_sentences(text: str) -> List[str]:
    return [sentence.strip() for sentence in re.split(r"\.\s*", text) if sentence.strip()]


def _zone_from_sentence(
    sentence: str, exam_type: EndoscopyType
) -> Optional[AnatomicalZone]:
    lowered = sentence.lower()

    if exam_type == EndoscopyType.GASTROSCOPY:
        if "антральн" in lowered or "антрум" in lowered or "антруме" in lowered:
            return AnatomicalZone.ANTRUM
        if "луковиц" in lowered:
            return AnatomicalZone.DUODENAL_BULB

    if exam_type == EndoscopyType.COLONOSCOPY:
        if "прям" in lowered and "киш" in lowered:
            return AnatomicalZone.RECTUM
        if "сигмовид" in lowered:
            return AnatomicalZone.SIGMOID_COLON

    return None


def _observations_from_sentence(sentence: str) -> List[dict]:
    observations = []
    lowered = sentence.lower()
    location = _location_from_text(sentence, "по малой кривизне")

    if "эроз" in lowered:
        observations.append(
            {
                "type": ObservationType.EROSION,
                "description": _erosion_description(sentence),
                "location": location,
                "size_mm": _size_for_stem(sentence, "эроз"),
                "quantity": _quantity_for_stem(sentence, "эроз"),
                "evidence_text": sentence,
            }
        )

    if "язвен" in lowered:
        observations.append(
            {
                "type": ObservationType.ULCER,
                "description": _ulcer_description(sentence),
                "location": location,
                "size_mm": _size_for_stem(sentence, "язвен"),
                "quantity": _quantity_for_stem(sentence, "язвен"),
                "evidence_text": sentence,
            }
        )

    if "полип" in lowered:
        observations.append(
            {
                "type": ObservationType.POLYP,
                "description": "полип",
                "location": location,
                "size_mm": _size_for_stem(sentence, "полип"),
                "quantity": _quantity_for_stem(sentence, "полип"),
                "evidence_text": sentence,
            }
        )

    return observations


def _size_for_stem(text: str, stem: str) -> Optional[float]:
    match = re.search(
        rf"{stem}[^\d]*(?:до\s*)?(\d+(?:[,.]\d+)?)\s*мм",
        text.lower(),
    )
    if match is None:
        return None
    return float(match.group(1).replace(",", "."))


def _quantity_for_stem(text: str, stem: str) -> Optional[int]:
    lowered = text.lower()
    if f"две {stem}" in lowered or f"два {stem}" in lowered:
        return 2
    match = re.search(rf"(\d+)\s+\w*{stem}", lowered)
    if match is None:
        return None
    return int(match.group(1))


def _location_from_text(text: str, phrase: str) -> Optional[str]:
    if phrase in text.lower():
        return phrase
    return None


def _erosion_description(text: str) -> str:
    if "фибрин" in text.lower():
        return "эрозия с фибринозным налетом"
    return "эрозия"


def _ulcer_description(text: str) -> str:
    if "без признаков активного кровотечения" in text.lower():
        return "язвенный дефект без признаков активного кровотечения"
    return "язвенный дефект"
