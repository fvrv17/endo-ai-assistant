from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field

from .models import EndoscopyReport, EndoscopyType, ZoneFinding


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    case_id: str = Field(min_length=1)
    raw_input: str = Field(min_length=1)
    exam_type: EndoscopyType
    indication: Optional[str] = None
    expected_findings: List[ZoneFinding]


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    expected_observations: int
    actual_observations: int
    matched_observations: int
    missing_observations: Tuple[str, ...] = ()
    extra_observations: Tuple[str, ...] = ()
    error: Optional[str] = None


@dataclass(frozen=True)
class EvalSummary:
    total_cases: int
    passed_cases: int
    total_expected_observations: int
    total_actual_observations: int
    total_matched_observations: int
    results: Sequence[EvalResult]

    @property
    def observation_recall(self) -> float:
        if self.total_expected_observations == 0:
            return 1.0
        return self.total_matched_observations / self.total_expected_observations

    @property
    def observation_precision(self) -> float:
        if self.total_actual_observations == 0:
            return 1.0
        return self.total_matched_observations / self.total_actual_observations


def load_eval_cases(path: Path) -> List[EvalCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [EvalCase.model_validate(item) for item in data]


def evaluate_extractor(extractor, cases: Iterable[EvalCase]) -> EvalSummary:
    results: List[EvalResult] = []

    for case in cases:
        try:
            report = extractor.extract(
                raw_input=case.raw_input,
                exam_type=case.exam_type,
                indication=case.indication,
            )
            results.append(evaluate_report(case, report))
        except Exception as exc:  # noqa: BLE001 - eval must report extractor failures.
            expected_count = _observation_count(case.expected_findings)
            results.append(
                EvalResult(
                    case_id=case.case_id,
                    passed=False,
                    expected_observations=expected_count,
                    actual_observations=0,
                    matched_observations=0,
                    error=str(exc),
                )
            )

    return build_eval_summary(results)


def build_eval_summary(results: Sequence[EvalResult]) -> EvalSummary:
    return EvalSummary(
        total_cases=len(results),
        passed_cases=sum(1 for result in results if result.passed),
        total_expected_observations=sum(
            result.expected_observations for result in results
        ),
        total_actual_observations=sum(result.actual_observations for result in results),
        total_matched_observations=sum(
            result.matched_observations for result in results
        ),
        results=results,
    )


def render_eval_summary(summary: EvalSummary) -> str:
    lines = [
        "Eval summary",
        f"Cases: {summary.passed_cases}/{summary.total_cases} passed",
        f"Observation recall: {summary.observation_recall:.2%}",
        f"Observation precision: {summary.observation_precision:.2%}",
        "",
        "Cases:",
    ]

    for result in summary.results:
        status = "PASS" if result.passed else "FAIL"
        line = (
            f"- {status} {result.case_id}: matched "
            f"{result.matched_observations}/{result.expected_observations}, "
            f"actual {result.actual_observations}"
        )
        if result.error is not None:
            line = f"{line}, error: {result.error}"
        lines.append(line)
        if result.missing_observations:
            lines.append("  Missing:")
            for item in result.missing_observations:
                lines.append(f"  - {item}")
        if result.extra_observations:
            lines.append("  Extra:")
            for item in result.extra_observations:
                lines.append(f"  - {item}")

    return "\n".join(lines)


def evaluate_report(case: EvalCase, report: EndoscopyReport) -> EvalResult:
    expected = _observation_keys(case.expected_findings)
    actual = _observation_keys(report.findings)
    expected_counts = Counter(expected)
    actual_counts = Counter(actual)
    matched = sum(
        min(expected_counts[key], actual_counts[key])
        for key in expected_counts.keys() | actual_counts.keys()
    )
    passed = expected == actual
    missing = tuple(
        _format_observation_key(key)
        for key in _counter_difference(expected_counts, actual_counts)
    )
    extra = tuple(
        _format_observation_key(key)
        for key in _counter_difference(actual_counts, expected_counts)
    )

    return EvalResult(
        case_id=case.case_id,
        passed=passed,
        expected_observations=len(expected),
        actual_observations=len(actual),
        matched_observations=matched,
        missing_observations=missing,
        extra_observations=extra,
    )


def _observation_count(findings: Sequence[ZoneFinding]) -> int:
    return sum(len(finding.observations) for finding in findings)


def _observation_keys(findings: Sequence[ZoneFinding]) -> List[tuple]:
    keys = []
    for finding in findings:
        for observation in finding.observations:
            keys.append(
                (
                    finding.zone.value,
                    observation.type.value,
                    observation.description,
                    observation.location,
                    observation.size_mm,
                    observation.quantity,
                )
            )
    return keys


def _counter_difference(left: Counter, right: Counter) -> List[tuple]:
    diff = []
    for key in sorted(left):
        count = left[key] - right.get(key, 0)
        if count > 0:
            diff.extend([key] * count)
    return diff


def _format_observation_key(key: tuple) -> str:
    zone, observation_type, description, location, size_mm, quantity = key
    return (
        f"zone={zone}, type={observation_type}, description={description}, "
        f"location={location}, size_mm={size_mm}, quantity={quantity}"
    )
