from __future__ import annotations

from typing import Dict, List

from .models import AnatomicalZone, EndoscopyReport, EndoscopyType
from .nomenclature import OBSERVATION_LABELS, ZONE_LABELS
from .quality import collect_review_flags


EXAM_LABELS: Dict[EndoscopyType, str] = {
    EndoscopyType.GASTROSCOPY: "ЭГДС",
    EndoscopyType.COLONOSCOPY: "Колоноскопия",
}


def render_report(report: EndoscopyReport) -> str:
    lines: List[str] = [
        f"Исследование: {EXAM_LABELS[report.exam_type]}",
        f"Повод: {report.indication or 'не указано'}",
        "",
        "Описание:",
    ]

    if not report.findings:
        lines.append("Находки не указаны.")
    else:
        for zone_finding in report.findings:
            zone_label = ZONE_LABELS[zone_finding.zone]
            if not zone_finding.observations:
                lines.append(f"- {zone_label}: находки не указаны.")
                continue

            rendered_observations = [
                _render_observation(observation)
                for observation in zone_finding.observations
            ]
            lines.append(f"- {zone_label}: {' '.join(rendered_observations)}")

    flags = collect_review_flags(report)
    if flags:
        lines.extend(["", "Поля для вычитки:"])
        for flag in flags:
            zone = _zone_label_from_flag(flag.zone)
            lines.append(f"- [{flag.severity}] {zone}: {flag.message}")

    return "\n".join(lines)


def _render_observation(observation) -> str:
    label = OBSERVATION_LABELS[observation.type]
    description = _sentence(observation.description)
    if _description_already_names_type(label, observation.description):
        parts = [description.capitalize()]
    else:
        parts = [f"{label.capitalize()}: {description}"]

    if observation.location is not None:
        parts.append(f"Локализация: {observation.location}.")
    else:
        parts.append("Локализация: не указана.")

    if observation.size_mm is not None:
        parts.append(f"Размер: {observation.size_mm:g} мм.")

    if observation.quantity is not None:
        parts.append(f"Количество: {observation.quantity}.")

    return " ".join(parts)


def _zone_label_from_flag(zone: str) -> str:
    if zone == "report":
        return "Отчет"
    try:
        return ZONE_LABELS[AnatomicalZone(zone)]
    except ValueError:
        return zone


def _sentence(text: str) -> str:
    text = text.strip()
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."


def _description_already_names_type(label: str, description: str) -> bool:
    normalized = description.lower()
    if normalized.startswith(label):
        return True
    if label == "язва" and normalized.startswith("язвен"):
        return True
    return False
