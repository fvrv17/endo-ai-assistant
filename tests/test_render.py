import unittest

from pydantic import ValidationError

from endo_ai_assistant import (
    AnatomicalZone,
    EndoscopyReport,
    EndoscopyType,
    ObservationType,
    build_report_from_extraction,
    extraction_json_schema,
    render_report,
)
from endo_ai_assistant.quality import collect_review_flags
from examples.synthetic_gastroscopy import build_synthetic_report
from examples.synthetic_gastroscopy import RAW_INPUT


class RenderSmokeTest(unittest.TestCase):
    def test_synthetic_report_renders_observations(self) -> None:
        report = build_synthetic_report()
        rendered = report.model_dump()

        self.assertEqual(rendered["exam_type"].value, "gastroscopy")
        self.assertEqual(len(report.findings), 2)

    def test_missing_location_is_flagged_for_review(self) -> None:
        report = build_synthetic_report()
        flags = collect_review_flags(report)

        self.assertTrue(any("локализация" in flag.message for flag in flags))

    def test_synthetic_input_runs_end_to_end(self) -> None:
        report = build_synthetic_report()
        rendered = render_report(report)

        self.assertIn("Антральный отдел", rendered)
        self.assertIn("Луковица ДПК", rendered)
        self.assertIn("Размер: 3 мм", rendered)

    def test_extraction_schema_exposes_findings_contract(self) -> None:
        schema = extraction_json_schema()

        self.assertEqual(schema["title"], "ExtractedFindings")
        self.assertIn("findings", schema["properties"])
        self.assertIn("findings", schema["required"])
        self.assertIn("antrum", schema["$defs"]["AnatomicalZone"]["enum"])
        self.assertIn("duodenum_d2", schema["$defs"]["AnatomicalZone"]["enum"])
        self.assertIn("cecal_pole", schema["$defs"]["AnatomicalZone"]["enum"])
        self.assertIn("submucosal_lesion", schema["$defs"]["ObservationType"]["enum"])

    def test_untraceable_evidence_is_rejected(self) -> None:
        payload = {
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

        with self.assertRaises(ValidationError):
            build_report_from_extraction(
                raw_input=RAW_INPUT,
                exam_type=EndoscopyType.GASTROSCOPY,
                extraction_payload=payload,
            )

    def test_blank_required_text_is_rejected_after_strip(self) -> None:
        payload = {
            "findings": [
                {
                    "zone": AnatomicalZone.ANTRUM,
                    "observations": [
                        {
                            "type": ObservationType.EROSION,
                            "description": "   ",
                            "location": "   ",
                            "size_mm": None,
                            "quantity": None,
                            "evidence_text": "   ",
                        }
                    ],
                }
            ]
        }

        with self.assertRaises(ValidationError):
            build_report_from_extraction(
                raw_input=RAW_INPUT,
                exam_type=EndoscopyType.GASTROSCOPY,
                extraction_payload=payload,
            )

    def test_blank_optional_text_becomes_none(self) -> None:
        report = EndoscopyReport(
            exam_type=EndoscopyType.GASTROSCOPY,
            raw_input=RAW_INPUT,
            indication="   ",
            findings=[],
        )

        self.assertIsNone(report.indication)

    def test_zone_outside_exam_type_is_rejected(self) -> None:
        raw_input = "Колоноскопия. В прямой кишке полип 5 мм."
        payload = {
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
        }

        with self.assertRaises(ValidationError):
            build_report_from_extraction(
                raw_input=raw_input,
                exam_type=EndoscopyType.GASTROSCOPY,
                extraction_payload=payload,
            )


if __name__ == "__main__":
    unittest.main()
