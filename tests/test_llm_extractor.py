import unittest
from typing import Any, Mapping

from pydantic import ValidationError

from endo_ai_assistant import (
    AnatomicalZone,
    EndoscopyType,
    LLMExtractor,
    ObservationType,
    build_extraction_user_prompt,
)
from examples.synthetic_gastroscopy import RAW_INPUT


class RecordingStructuredClient:
    def __init__(self, payload: Mapping[str, Any]) -> None:
        self.payload = payload
        self.calls: list[Mapping[str, Any]] = []

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "json_schema": json_schema,
            }
        )
        return self.payload


class LLMExtractorTest(unittest.TestCase):
    def test_llm_extractor_builds_report_from_structured_payload(self) -> None:
        client = RecordingStructuredClient(
            {
                "findings": [
                    {
                        "zone": AnatomicalZone.ANTRUM,
                        "observations": [
                            {
                                "type": ObservationType.EROSION,
                                "description": "эрозия с фибринозным налетом",
                                "location": "по малой кривизне",
                                "size_mm": 3,
                                "quantity": None,
                                "evidence_text": (
                                    "В антральном отделе желудка по малой кривизне "
                                    "эрозия до 3 мм, фибринозный налет"
                                ),
                            }
                        ],
                    }
                ]
            }
        )

        report = LLMExtractor(client).extract(
            raw_input=RAW_INPUT,
            exam_type=EndoscopyType.GASTROSCOPY,
        )

        self.assertEqual(len(report.findings), 1)
        self.assertEqual(report.findings[0].zone, AnatomicalZone.ANTRUM)
        self.assertEqual(client.calls[0]["json_schema"]["title"], "ExtractedFindings")
        self.assertIn(RAW_INPUT, client.calls[0]["user_prompt"])

    def test_llm_extractor_rejects_hallucinated_evidence(self) -> None:
        client = RecordingStructuredClient(
            {
                "findings": [
                    {
                        "zone": AnatomicalZone.ANTRUM,
                        "observations": [
                            {
                                "type": ObservationType.TUMOR,
                                "description": "подозрение на опухолевое образование",
                                "location": "по большой кривизне",
                                "size_mm": 20,
                                "quantity": None,
                                "evidence_text": "опухолевое образование 20 мм",
                            }
                        ],
                    }
                ]
            }
        )

        with self.assertRaises(ValidationError):
            LLMExtractor(client).extract(
                raw_input=RAW_INPUT,
                exam_type=EndoscopyType.GASTROSCOPY,
            )

    def test_user_prompt_makes_source_boundary_explicit(self) -> None:
        prompt = build_extraction_user_prompt(
            raw_input=RAW_INPUT,
            exam_type=EndoscopyType.GASTROSCOPY,
        )

        self.assertIn("Doctor input:", prompt)
        self.assertIn("Return ExtractedFindings only", prompt)
        self.assertIn("Use null for missing values", prompt)
        self.assertIn("Allowed zones:", prompt)
        self.assertIn("antrum: Антральный отдел", prompt)
        self.assertIn("антрум", prompt)
        self.assertIn("Allowed finding types:", prompt)
        self.assertIn("submucosal_lesion: подслизистое образование", prompt)

    def test_user_prompt_scopes_zones_to_exam_type(self) -> None:
        prompt = build_extraction_user_prompt(
            raw_input="Колоноскопия. В прямой кишке полип 5 мм.",
            exam_type=EndoscopyType.COLONOSCOPY,
        )

        self.assertIn("rectum: Прямая кишка", prompt)
        self.assertIn("terminal_ileum: Терминальный отдел подвздошной кишки", prompt)
        self.assertNotIn("antrum: Антральный отдел", prompt)


if __name__ == "__main__":
    unittest.main()
