from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import EndoscopyReport, ObservationType


@dataclass(frozen=True)
class ReviewFlag:
    severity: str
    message: str
    zone: str


SIZE_EXPECTED_TYPES = {
    ObservationType.POLYP,
    ObservationType.ULCER,
    ObservationType.MASS,
    ObservationType.TUMOR,
    ObservationType.SUBMUCOSAL_LESION,
}


def collect_review_flags(report: EndoscopyReport) -> List[ReviewFlag]:
    flags: List[ReviewFlag] = []

    if not report.findings:
        flags.append(
            ReviewFlag(
                severity="warning",
                message="Не извлечено ни одной находки. Проверьте исходное описание.",
                zone="report",
            )
        )
        return flags

    for zone_finding in report.findings:
        for observation in zone_finding.observations:
            if observation.location is None:
                flags.append(
                    ReviewFlag(
                        severity="warning",
                        message="Не указана точная локализация находки.",
                        zone=zone_finding.zone.value,
                    )
                )
            if observation.type in SIZE_EXPECTED_TYPES and observation.size_mm is None:
                flags.append(
                    ReviewFlag(
                        severity="warning",
                        message="Для этой находки желательно указать размер.",
                        zone=zone_finding.zone.value,
                    )
                )

    return flags
