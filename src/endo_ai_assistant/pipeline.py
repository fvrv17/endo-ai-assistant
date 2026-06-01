from __future__ import annotations

from typing import Any, Dict, Optional

from .analytics import calculate_report_stats, render_report_stats
from .dev_extractors import SyntheticGastroscopyExtractor
from .llm_extractor import LLMExtractor
from .models import EndoscopyReport, EndoscopyType
from .openai_client import DEFAULT_OPENAI_MODEL, OpenAIStructuredClient
from .quality import collect_review_flags
from .render import render_report


DEMO_INPUT = (
    "ЭГДС. В антральном отделе желудка по малой кривизне эрозия до 3 мм, "
    "фибринозный налет. В луковице ДПК язвенный дефект 6 мм без признаков "
    "активного кровотечения."
)


def build_extractor(provider: str, model: str = DEFAULT_OPENAI_MODEL):
    if provider == "synthetic":
        return SyntheticGastroscopyExtractor()
    if provider == "openai":
        return LLMExtractor(OpenAIStructuredClient(model=model))
    raise ValueError(f"Unsupported provider: {provider}")


def extract_report(
    *,
    raw_input: str,
    exam_type: EndoscopyType,
    provider: str = "synthetic",
    model: str = DEFAULT_OPENAI_MODEL,
    indication: Optional[str] = None,
) -> EndoscopyReport:
    return build_extractor(provider, model).extract(
        raw_input=raw_input,
        exam_type=exam_type,
        indication=indication,
    )


def build_extract_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_input = str(payload.get("raw_input", "")).strip()
    if not raw_input:
        raise ValueError("Введите свободное описание исследования.")

    exam_type = EndoscopyType(payload.get("exam_type", EndoscopyType.GASTROSCOPY.value))
    provider = str(payload.get("provider", "synthetic"))
    model = str(payload.get("model") or DEFAULT_OPENAI_MODEL)
    indication = _optional_string(payload.get("indication"))

    report = extract_report(
        raw_input=raw_input,
        exam_type=exam_type,
        provider=provider,
        model=model,
        indication=indication,
    )
    return build_response_from_report(report, provider=provider, model=model)


def build_response_from_report(
    report: EndoscopyReport,
    *,
    provider: str,
    model: str,
) -> Dict[str, Any]:
    stats = calculate_report_stats(report)
    flags = collect_review_flags(report)

    return {
        "report_text": render_report(report),
        "stats_text": render_report_stats(stats),
        "structured": report.model_dump(mode="json"),
        "review_flags": [flag.__dict__ for flag in flags],
        "stats": {
            "zones_with_findings": stats.zones_with_findings,
            "observations_total": stats.observations_total,
            "observations_by_zone": {
                zone.value: count for zone, count in stats.observations_by_zone.items()
            },
            "observations_by_type": {
                item.value: count for item, count in stats.observations_by_type.items()
            },
        },
        "provider": provider,
        "model": model if provider == "openai" else None,
    }


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None
