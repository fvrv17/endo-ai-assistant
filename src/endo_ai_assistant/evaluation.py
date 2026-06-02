from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    AnatomicalZone,
    EndoscopyReport,
    EndoscopyType,
    Observation,
    ObservationType,
    ZoneFinding,
)


DEFAULT_SIZE_TOLERANCE_MM = 2.0
NEGATION_TAG = "negation"


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    case_id: str = Field(min_length=1)
    raw_input: str = Field(min_length=1)
    exam_type: EndoscopyType
    indication: Optional[str] = None
    tags: Tuple[str, ...] = ()
    expected_findings: List[ZoneFinding]


@dataclass(frozen=True)
class ObservationRecord:
    zone: AnatomicalZone
    type: ObservationType
    description: str
    location: Optional[str]
    size_mm: Optional[float]
    quantity: Optional[int]

    @classmethod
    def from_observation(
        cls,
        *,
        zone: AnatomicalZone,
        observation: Observation,
    ) -> ObservationRecord:
        return cls(
            zone=zone,
            type=observation.type,
            description=observation.description,
            location=observation.location,
            size_mm=observation.size_mm,
            quantity=observation.quantity,
        )


@dataclass(frozen=True)
class ObservationMatch:
    expected: ObservationRecord
    actual: ObservationRecord
    size_compared: bool
    size_within_tolerance: bool
    normalized_text_match: bool


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    expected_observations: int
    actual_observations: int
    structural_matches: int
    size_compared: int = 0
    size_within_tolerance: int = 0
    text_compared: int = 0
    normalized_text_matches: int = 0
    missing_observations: Tuple[str, ...] = ()
    extra_observations: Tuple[str, ...] = ()
    size_mismatches: Tuple[str, ...] = ()
    text_mismatches: Tuple[str, ...] = ()
    negation_false_positives: int = 0
    error: Optional[str] = None


@dataclass(frozen=True)
class EvalSummary:
    total_cases: int
    passed_cases: int
    total_expected_observations: int
    total_actual_observations: int
    total_structural_matches: int
    total_size_compared: int
    total_size_within_tolerance: int
    total_text_compared: int
    total_normalized_text_matches: int
    negation_false_positives: int
    results: Sequence[EvalResult]

    @property
    def structural_recall(self) -> float:
        if self.total_expected_observations == 0:
            return 1.0
        return self.total_structural_matches / self.total_expected_observations

    @property
    def structural_precision(self) -> float:
        if self.total_actual_observations == 0:
            return 1.0
        return self.total_structural_matches / self.total_actual_observations

    @property
    def size_within_tolerance_rate(self) -> float:
        if self.total_size_compared == 0:
            return 1.0
        return self.total_size_within_tolerance / self.total_size_compared

    @property
    def normalized_text_match_rate(self) -> float:
        if self.total_text_compared == 0:
            return 1.0
        return self.total_normalized_text_matches / self.total_text_compared


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
                    structural_matches=0,
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
        total_structural_matches=sum(result.structural_matches for result in results),
        total_size_compared=sum(result.size_compared for result in results),
        total_size_within_tolerance=sum(
            result.size_within_tolerance for result in results
        ),
        total_text_compared=sum(result.text_compared for result in results),
        total_normalized_text_matches=sum(
            result.normalized_text_matches for result in results
        ),
        negation_false_positives=sum(
            result.negation_false_positives for result in results
        ),
        results=results,
    )


def render_eval_summary(summary: EvalSummary) -> str:
    lines = [
        "Eval summary",
        f"Cases: {summary.passed_cases}/{summary.total_cases} passed",
        f"Structural recall: {summary.structural_recall:.2%}",
        f"Structural precision: {summary.structural_precision:.2%}",
        (
            "Size within +/-"
            f"{DEFAULT_SIZE_TOLERANCE_MM:g} mm: "
            f"{summary.size_within_tolerance_rate:.2%} "
            f"({summary.total_size_within_tolerance}/{summary.total_size_compared})"
        ),
        (
            "Normalized text match: "
            f"{summary.normalized_text_match_rate:.2%} "
            f"({summary.total_normalized_text_matches}/{summary.total_text_compared})"
        ),
        f"Negation false-positives: {summary.negation_false_positives}",
        "",
        "Cases:",
    ]

    for result in summary.results:
        status = "PASS" if result.passed else "FAIL"
        line = (
            f"- {status} {result.case_id}: structural "
            f"{result.structural_matches}/{result.expected_observations}, "
            f"actual {result.actual_observations}; size "
            f"{result.size_within_tolerance}/{result.size_compared}; text "
            f"{result.normalized_text_matches}/{result.text_compared}"
        )
        if result.negation_false_positives:
            line = f"{line}; negation FP {result.negation_false_positives}"
        if result.error is not None:
            line = f"{line}, error: {result.error}"
        lines.append(line)
        if result.missing_observations:
            lines.append("  Missing structural matches:")
            for item in result.missing_observations:
                lines.append(f"  - {item}")
        if result.extra_observations:
            lines.append("  Extra structural matches:")
            for item in result.extra_observations:
                lines.append(f"  - {item}")
        if result.size_mismatches:
            lines.append("  Size mismatches:")
            for item in result.size_mismatches:
                lines.append(f"  - {item}")
        if result.text_mismatches:
            lines.append("  Text mismatches:")
            for item in result.text_mismatches:
                lines.append(f"  - {item}")

    return "\n".join(lines)


def evaluate_report(
    case: EvalCase,
    report: EndoscopyReport,
    *,
    size_tolerance_mm: float = DEFAULT_SIZE_TOLERANCE_MM,
) -> EvalResult:
    expected = _observation_records(case.expected_findings)
    actual = _observation_records(report.findings)
    matches, missing, extra = _match_structural_observations(
        expected=expected,
        actual=actual,
        size_tolerance_mm=size_tolerance_mm,
    )

    size_compared = sum(1 for match in matches if match.size_compared)
    size_within_tolerance = sum(
        1
        for match in matches
        if match.size_compared and match.size_within_tolerance
    )
    text_compared = len(matches)
    normalized_text_matches = sum(1 for match in matches if match.normalized_text_match)
    size_mismatches = tuple(
        _format_size_mismatch(match, size_tolerance_mm)
        for match in matches
        if match.size_compared and not match.size_within_tolerance
    )
    text_mismatches = tuple(
        _format_text_mismatch(match)
        for match in matches
        if not match.normalized_text_match
    )
    negation_false_positives = len(extra) if NEGATION_TAG in case.tags else 0

    passed = (
        not missing
        and not extra
        and not size_mismatches
    )

    return EvalResult(
        case_id=case.case_id,
        passed=passed,
        expected_observations=len(expected),
        actual_observations=len(actual),
        structural_matches=len(matches),
        size_compared=size_compared,
        size_within_tolerance=size_within_tolerance,
        text_compared=text_compared,
        normalized_text_matches=normalized_text_matches,
        missing_observations=tuple(_format_observation(item) for item in missing),
        extra_observations=tuple(_format_observation(item) for item in extra),
        size_mismatches=size_mismatches,
        text_mismatches=text_mismatches,
        negation_false_positives=negation_false_positives,
    )


def _match_structural_observations(
    *,
    expected: Sequence[ObservationRecord],
    actual: Sequence[ObservationRecord],
    size_tolerance_mm: float,
) -> tuple[List[ObservationMatch], List[ObservationRecord], List[ObservationRecord]]:
    unmatched_actual = list(actual)
    matches: List[ObservationMatch] = []
    missing: List[ObservationRecord] = []

    for expected_item in expected:
        candidate = _best_structural_candidate(
            expected_item=expected_item,
            candidates=unmatched_actual,
            size_tolerance_mm=size_tolerance_mm,
        )
        if candidate is None:
            missing.append(expected_item)
            continue

        unmatched_actual.remove(candidate)
        matches.append(
            ObservationMatch(
                expected=expected_item,
                actual=candidate,
                size_compared=_has_size_signal(expected_item, candidate),
                size_within_tolerance=_size_within_tolerance(
                    expected_item,
                    candidate,
                    size_tolerance_mm,
                ),
                normalized_text_match=(
                    _normalize_text(expected_item.description)
                    == _normalize_text(candidate.description)
                ),
            )
        )

    return matches, missing, unmatched_actual


def _best_structural_candidate(
    *,
    expected_item: ObservationRecord,
    candidates: Sequence[ObservationRecord],
    size_tolerance_mm: float,
) -> Optional[ObservationRecord]:
    structural_candidates = [
        candidate
        for candidate in candidates
        if (
            candidate.zone == expected_item.zone
            and candidate.type == expected_item.type
        )
    ]
    if not structural_candidates:
        return None

    return max(
        structural_candidates,
        key=lambda candidate: _candidate_score(
            expected_item,
            candidate,
            size_tolerance_mm,
        ),
    )


def _candidate_score(
    expected: ObservationRecord,
    actual: ObservationRecord,
    size_tolerance_mm: float,
) -> tuple[int, int, int, int]:
    size_score = int(_size_within_tolerance(expected, actual, size_tolerance_mm))
    text_score = int(
        _normalize_text(expected.description) == _normalize_text(actual.description)
    )
    location_score = int(
        _normalize_nullable_text(expected.location)
        == _normalize_nullable_text(actual.location)
    )
    quantity_score = int(expected.quantity == actual.quantity)
    return size_score, text_score, location_score, quantity_score


def _size_within_tolerance(
    expected: ObservationRecord,
    actual: ObservationRecord,
    tolerance_mm: float,
) -> bool:
    if expected.size_mm is None and actual.size_mm is None:
        return True
    if expected.size_mm is None or actual.size_mm is None:
        return False
    return abs(expected.size_mm - actual.size_mm) <= tolerance_mm


def _has_size_signal(expected: ObservationRecord, actual: ObservationRecord) -> bool:
    return expected.size_mm is not None or actual.size_mm is not None


def _observation_count(findings: Sequence[ZoneFinding]) -> int:
    return sum(len(finding.observations) for finding in findings)


def _observation_records(findings: Sequence[ZoneFinding]) -> List[ObservationRecord]:
    records = []
    for finding in findings:
        for observation in finding.observations:
            records.append(
                ObservationRecord.from_observation(
                    zone=finding.zone,
                    observation=observation,
                )
            )
    return records


def _normalize_text(value: str) -> str:
    value = value.lower().replace("ё", "е")
    value = re.sub(r"[^0-9a-zа-я]+", " ", value)
    return " ".join(value.split())


def _normalize_nullable_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return _normalize_text(value)


def _format_observation(item: ObservationRecord) -> str:
    return (
        f"zone={item.zone.value}, type={item.type.value}, "
        f"description={item.description}, location={item.location}, "
        f"size_mm={item.size_mm}, quantity={item.quantity}"
    )


def _format_size_mismatch(
    match: ObservationMatch,
    tolerance_mm: float,
) -> str:
    return (
        f"zone={match.expected.zone.value}, type={match.expected.type.value}, "
        f"expected_size_mm={match.expected.size_mm}, "
        f"actual_size_mm={match.actual.size_mm}, "
        f"tolerance_mm={tolerance_mm:g}"
    )


def _format_text_mismatch(match: ObservationMatch) -> str:
    return (
        f"zone={match.expected.zone.value}, type={match.expected.type.value}, "
        f"expected_text={match.expected.description}, "
        f"actual_text={match.actual.description}"
    )
