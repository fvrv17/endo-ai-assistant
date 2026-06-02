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
    def test_synthetic_eval_reports_axis_metrics(self) -> None:
        cases = load_eval_cases(Path("eval_cases/synthetic_endoscopy.json"))
        summary = evaluate_extractor(SyntheticGastroscopyExtractor(), cases)

        self.assertEqual(summary.total_cases, 12)
        self.assertEqual(summary.passed_cases, 8)
        self.assertAlmostEqual(summary.structural_recall, 12 / 13)
        self.assertAlmostEqual(summary.structural_precision, 12 / 14)
        self.assertAlmostEqual(summary.size_within_tolerance_rate, 10 / 11)
        self.assertAlmostEqual(summary.normalized_text_match_rate, 8 / 12)
        self.assertEqual(summary.negation_false_positives, 2)

    def test_eval_summary_renders_metrics(self) -> None:
        cases = load_eval_cases(Path("eval_cases/synthetic_endoscopy.json"))
        summary = evaluate_extractor(SyntheticGastroscopyExtractor(), cases)
        rendered = render_eval_summary(summary)

        self.assertIn("Eval summary", rendered)
        self.assertIn("Cases: 8/12 passed", rendered)
        self.assertIn("Structural recall: 92.31%", rendered)
        self.assertIn("Structural precision: 85.71%", rendered)
        self.assertIn("Size within +/-2 mm: 90.91% (10/11)", rendered)
        self.assertIn("Normalized text match: 66.67% (8/12)", rendered)
        self.assertIn("Negation false-positives: 2", rendered)

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
        self.assertIn("Missing structural matches:", rendered)
        self.assertIn("zone=antrum", rendered)

    def test_text_mismatch_does_not_fail_case(self) -> None:
        case = next(
            item
            for item in load_eval_cases(Path("eval_cases/synthetic_endoscopy.json"))
            if item.case_id == "egd_paraphrased_erosion_001"
        )
        report = SyntheticGastroscopyExtractor().extract(
            raw_input=case.raw_input,
            exam_type=case.exam_type,
        )

        result = evaluate_report(case, report)

        self.assertTrue(result.passed)
        self.assertEqual(result.structural_matches, 1)
        self.assertEqual(result.normalized_text_matches, 0)
        self.assertTrue(result.text_mismatches)

    def test_negation_false_positive_is_counted_separately(self) -> None:
        case = next(
            item
            for item in load_eval_cases(Path("eval_cases/synthetic_endoscopy.json"))
            if item.case_id == "egd_negated_erosion_001"
        )
        report = SyntheticGastroscopyExtractor().extract(
            raw_input=case.raw_input,
            exam_type=case.exam_type,
        )

        result = evaluate_report(case, report)

        self.assertFalse(result.passed)
        self.assertEqual(result.expected_observations, 0)
        self.assertEqual(result.actual_observations, 1)
        self.assertEqual(result.negation_false_positives, 1)


if __name__ == "__main__":
    unittest.main()
