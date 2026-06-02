import unittest

from pydantic import ValidationError

from endo_ai_assistant import (
    AnatomicalZone,
    EndoscopyType,
    Observation,
    ObservationType,
    ZoneFinding,
    build_report_from_extraction,
)


class ModelSafetyValidationTest(unittest.TestCase):
    def test_untraceable_evidence_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            build_report_from_extraction(
                raw_input="ЭГДС. В антральном отделе желудка эрозия до 3 мм.",
                exam_type=EndoscopyType.GASTROSCOPY,
                extraction_payload={
                    "findings": [
                        {
                            "zone": AnatomicalZone.ANTRUM,
                            "observations": [
                                {
                                    "type": ObservationType.TUMOR,
                                    "description": "опухолевое образование",
                                    "location": None,
                                    "size_mm": 20,
                                    "quantity": None,
                                    "evidence_text": "опухолевое образование 20 мм",
                                }
                            ],
                        }
                    ]
                },
            )

    def test_zone_outside_exam_type_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            build_report_from_extraction(
                raw_input="Колоноскопия. В прямой кишке полип 5 мм.",
                exam_type=EndoscopyType.GASTROSCOPY,
                extraction_payload={
                    "findings": [
                        {
                            "zone": AnatomicalZone.RECTUM,
                            "observations": [
                                {
                                    "type": ObservationType.POLYP,
                                    "description": "полип",
                                    "location": None,
                                    "size_mm": 5,
                                    "quantity": None,
                                    "evidence_text": "В прямой кишке полип 5 мм",
                                }
                            ],
                        }
                    ]
                },
            )

    def test_size_upper_boundary_is_allowed(self) -> None:
        observation = Observation(
            type=ObservationType.POLYP,
            description="полип",
            location=None,
            size_mm=300,
            quantity=None,
            evidence_text="В прямой кишке полип 300 мм",
        )
        finding = ZoneFinding(
            zone=AnatomicalZone.RECTUM,
            observations=[observation],
        )

        self.assertEqual(finding.observations[0].size_mm, 300)

    def test_size_above_upper_boundary_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            Observation(
                type=ObservationType.POLYP,
                description="полип",
                location=None,
                size_mm=301,
                quantity=None,
                evidence_text="В прямой кишке полип 301 мм",
            )


if __name__ == "__main__":
    unittest.main()
