import unittest
from pathlib import Path

from endo_ai_assistant import (
    EndoscopyReport,
    EndoscopyType,
    build_eval_summary,
    evaluate_report,
    evaluate_extractor,
    load_eval_cases,
    render_eval_summary,
)
from endo_ai_assistant.dev_extractors import SyntheticGastroscopyExtractor


class EvaluationTest(unittest.TestCase):
    def test_synthetic_eval_case_passes(self) -> None:
        cases = load_eval_cases(Path("eval_cases/synthetic_endoscopy.json"))
        summary = evaluate_extractor(SyntheticGastroscopyExtractor(), cases)

        self.assertEqual(summary.total_cases, 6)
        self.assertEqual(summary.passed_cases, 6)
        self.assertEqual(summary.observation_recall, 1.0)
        self.assertEqual(summary.observation_precision, 1.0)

    def test_eval_summary_renders_metrics(self) -> None:
        cases = load_eval_cases(Path("eval_cases/synthetic_endoscopy.json"))
        summary = evaluate_extractor(SyntheticGastroscopyExtractor(), cases)
        rendered = render_eval_summary(summary)

        self.assertIn("Eval summary", rendered)
        self.assertIn("Cases: 6/6 passed", rendered)
        self.assertIn("Observation recall: 100.00%", rendered)

    def test_eval_summary_renders_missing_observation_diff(self) -> None:
        case = load_eval_cases(Path("eval_cases/synthetic_endoscopy.json"))[0]
        empty_report = EndoscopyReport(
            exam_type=EndoscopyType.GASTROSCOPY,
            raw_input=case.raw_input,
            findings=[],
        )

        result = evaluate_report(case, empty_report)
        rendered = render_eval_summary(build_eval_summary([result]))

        self.assertFalse(result.passed)
        self.assertTrue(result.missing_observations)
        self.assertIn("Missing:", rendered)
        self.assertIn("zone=antrum", rendered)


if __name__ == "__main__":
    unittest.main()
