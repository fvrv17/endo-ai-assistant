from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_ai import Agent

from .analytics import calculate_report_stats, render_report_stats
from .models import EndoscopyReport, EndoscopyType
from .openai_client import DEFAULT_OPENAI_MODEL
from .pipeline import extract_report
from .quality import collect_review_flags
from .render import render_report


DEFAULT_AGENT_MODEL = f"openai:{DEFAULT_OPENAI_MODEL}"


class EndoIntent(str, Enum):
    STRUCTURE_REPORT = "structure_report"
    SUMMARIZE_NOTE = "summarize_note"
    OUT_OF_SCOPE = "out_of_scope"


class EndoAgentPlan(BaseModel):
    """Agent-level routing plan; clinical extraction is still done by code."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    intent: EndoIntent
    summary: str = Field(
        min_length=1,
        description="Short non-diagnostic summary of the user's request.",
    )
    needs_extraction: bool
    confidence: float = Field(ge=0, le=1)
    safety_note: str = Field(
        min_length=1,
        description="Short note about why human review or no extraction is needed.",
    )

    @model_validator(mode="after")
    def extraction_flag_must_match_intent(self) -> EndoAgentPlan:
        expected = self.intent == EndoIntent.STRUCTURE_REPORT
        if self.needs_extraction != expected:
            raise ValueError(
                "needs_extraction must be true only for structure_report intent"
            )
        return self


class EndoAgentRun(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    plan: EndoAgentPlan
    report: Optional[EndoscopyReport] = None
    report_text: Optional[str] = None
    stats_text: Optional[str] = None
    review_flags: list[str] = Field(default_factory=list)


ENDO_AGENT_INSTRUCTIONS = """
You are an intent router for an endoscopy report assistant.

Classify the user's message into exactly one intent:
- structure_report: the user provided an endoscopy note that should be converted
  into a structured report.
- summarize_note: the user asks for a short non-diagnostic summary only.
- out_of_scope: the message is not about endoscopy report preparation.

Do not invent clinical findings. Do not diagnose. Do not produce the final
endoscopy report. If a report should be structured, set needs_extraction=true;
the deterministic application pipeline will perform extraction and rendering.
""".strip()


def build_endo_agent(model: str = DEFAULT_AGENT_MODEL) -> Agent[None, EndoAgentPlan]:
    return Agent(
        model,
        output_type=EndoAgentPlan,
        instructions=ENDO_AGENT_INSTRUCTIONS,
        defer_model_check=True,
    )


def run_endo_agent(
    *,
    user_input: str,
    exam_type: EndoscopyType = EndoscopyType.GASTROSCOPY,
    agent_model: str = DEFAULT_AGENT_MODEL,
    extraction_provider: str = "synthetic",
    extraction_model: str = DEFAULT_OPENAI_MODEL,
    indication: Optional[str] = None,
    agent: Optional[Agent[None, EndoAgentPlan]] = None,
) -> EndoAgentRun:
    user_input = user_input.strip()
    if not user_input:
        raise ValueError("user_input cannot be empty")

    active_agent = agent or build_endo_agent(agent_model)
    plan = active_agent.run_sync(_build_agent_prompt(user_input, exam_type)).output

    if plan.intent != EndoIntent.STRUCTURE_REPORT:
        return EndoAgentRun(plan=plan)

    report = extract_report(
        raw_input=user_input,
        exam_type=exam_type,
        provider=extraction_provider,
        model=extraction_model,
        indication=indication,
    )
    flags = collect_review_flags(report)

    return EndoAgentRun(
        plan=plan,
        report=report,
        report_text=render_report(report),
        stats_text=render_report_stats(calculate_report_stats(report)),
        review_flags=[f"[{flag.severity}] {flag.message}" for flag in flags],
    )


def _build_agent_prompt(user_input: str, exam_type: EndoscopyType) -> str:
    return (
        f"Exam type: {exam_type.value}\n\n"
        "User message:\n"
        f"{user_input}\n\n"
        "Return an EndoAgentPlan only."
    )
