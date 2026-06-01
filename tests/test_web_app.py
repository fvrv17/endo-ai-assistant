import unittest

from endo_ai_assistant.pipeline import DEMO_INPUT, build_extract_response
from endo_ai_assistant.web_app import INDEX_HTML


class WebAppTest(unittest.TestCase):
    def test_build_extract_response_returns_report_stats_and_json(self) -> None:
        payload = build_extract_response(
            {
                "raw_input": DEMO_INPUT,
                "exam_type": "gastroscopy",
                "provider": "synthetic",
                "indication": "",
            }
        )

        self.assertIn("Исследование: ЭГДС", payload["report_text"])
        self.assertIn("Статистика:", payload["stats_text"])
        self.assertEqual(payload["structured"]["exam_type"], "gastroscopy")
        self.assertEqual(payload["stats"]["observations_total"], 2)
        self.assertEqual(payload["provider"], "synthetic")

    def test_build_extract_response_rejects_empty_input(self) -> None:
        with self.assertRaises(ValueError):
            build_extract_response({"raw_input": "   "})

    def test_index_html_contains_required_controls(self) -> None:
        self.assertIn('id="rawInput"', INDEX_HTML)
        self.assertIn('id="extractBtn"', INDEX_HTML)
        self.assertIn('data-tab="report"', INDEX_HTML)
        self.assertIn('/api/extract', INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
