from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict

from .models import AnatomicalZone, EndoscopyReport, ObservationType
from .nomenclature import OBSERVATION_LABELS, ZONE_LABELS


@dataclass(frozen=True)
class ReportStats:
    zones_with_findings: int
    observations_total: int
    observations_by_zone: Dict[AnatomicalZone, int]
    observations_by_type: Dict[ObservationType, int]


def calculate_report_stats(report: EndoscopyReport) -> ReportStats:
    zone_counts: Counter[AnatomicalZone] = Counter()
    type_counts: Counter[ObservationType] = Counter()

    for finding in report.findings:
        if finding.observations:
            zone_counts[finding.zone] += len(finding.observations)
        for observation in finding.observations:
            type_counts[observation.type] += 1

    return ReportStats(
        zones_with_findings=len(zone_counts),
        observations_total=sum(zone_counts.values()),
        observations_by_zone=dict(zone_counts),
        observations_by_type=dict(type_counts),
    )


def render_report_stats(stats: ReportStats) -> str:
    lines = [
        "Статистика:",
        f"- Зон с находками: {stats.zones_with_findings}",
        f"- Всего находок: {stats.observations_total}",
    ]

    if stats.observations_by_zone:
        lines.append("- По зонам:")
        for zone, count in sorted(
            stats.observations_by_zone.items(), key=lambda item: ZONE_LABELS[item[0]]
        ):
            lines.append(f"  - {ZONE_LABELS[zone]}: {count}")

    if stats.observations_by_type:
        lines.append("- По типам:")
        for observation_type, count in sorted(
            stats.observations_by_type.items(),
            key=lambda item: OBSERVATION_LABELS[item[0]],
        ):
            lines.append(f"  - {OBSERVATION_LABELS[observation_type]}: {count}")

    return "\n".join(lines)
