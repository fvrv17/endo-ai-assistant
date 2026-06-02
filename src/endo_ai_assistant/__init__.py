"""Prototype primitives for structured endoscopy reports."""

from .agent import (
    DEFAULT_AGENT_MODEL,
    ENDO_AGENT_INSTRUCTIONS,
    EndoAgentPlan,
    EndoAgentRun,
    EndoIntent,
    build_endo_agent,
    run_endo_agent,
)
from .analytics import ReportStats, calculate_report_stats, render_report_stats
from .models import (
    AnatomicalZone,
    COLONOSCOPY_ZONES,
    EndoscopyReport,
    EndoscopyType,
    ExtractedFindings,
    FindingType,
    GASTROSCOPY_ZONES,
    Observation,
    ObservationType,
    ZoneFinding,
    ZONES_BY_EXAM_TYPE,
)
from .nomenclature import (
    OBSERVATION_LABELS,
    OBSERVATION_SYNONYMS,
    ZONE_LABELS,
    ZONE_SYNONYMS,
    export_nomenclature,
)
from .extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    EndoscopyExtractor,
    build_report_from_extraction,
    extraction_json_schema,
    strict_extraction_json_schema,
)
from .llm_extractor import (
    LLMExtractor,
    StructuredLLMClient,
    build_extraction_user_prompt,
)
from .openai_client import DEFAULT_OPENAI_MODEL, OpenAIStructuredClient
from .evaluation import (
    EvalCase,
    EvalResult,
    EvalSummary,
    build_eval_summary,
    evaluate_extractor,
    evaluate_report,
    load_eval_cases,
    render_eval_summary,
)
from .quality import ReviewFlag, collect_review_flags
from .render import render_report

__all__ = [
    "AnatomicalZone",
    "COLONOSCOPY_ZONES",
    "DEFAULT_AGENT_MODEL",
    "EvalCase",
    "EvalResult",
    "EvalSummary",
    "ENDO_AGENT_INSTRUCTIONS",
    "EXTRACTION_SYSTEM_PROMPT",
    "DEFAULT_OPENAI_MODEL",
    "EndoAgentPlan",
    "EndoAgentRun",
    "EndoIntent",
    "EndoscopyReport",
    "EndoscopyExtractor",
    "EndoscopyType",
    "ExtractedFindings",
    "FindingType",
    "GASTROSCOPY_ZONES",
    "LLMExtractor",
    "OBSERVATION_LABELS",
    "OBSERVATION_SYNONYMS",
    "Observation",
    "ObservationType",
    "OpenAIStructuredClient",
    "ReportStats",
    "ReviewFlag",
    "StructuredLLMClient",
    "ZoneFinding",
    "ZONE_LABELS",
    "ZONE_SYNONYMS",
    "ZONES_BY_EXAM_TYPE",
    "build_endo_agent",
    "build_eval_summary",
    "build_report_from_extraction",
    "build_extraction_user_prompt",
    "calculate_report_stats",
    "collect_review_flags",
    "evaluate_extractor",
    "evaluate_report",
    "export_nomenclature",
    "extraction_json_schema",
    "strict_extraction_json_schema",
    "load_eval_cases",
    "render_eval_summary",
    "render_report",
    "render_report_stats",
    "run_endo_agent",
]
