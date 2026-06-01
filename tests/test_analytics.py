import unittest

from endo_ai_assistant import calculate_report_stats, render_report_stats
from examples.synthetic_gastroscopy import build_synthetic_report


class AnalyticsTest(unittest.TestCase):
    def test_report_stats_counts_zones_and_observation_types(self) -> None:
        stats = calculate_report_stats(build_synthetic_report())

        self.assertEqual(stats.zones_with_findings, 2)
        self.assertEqual(stats.observations_total, 2)
        self.assertEqual(sum(stats.observations_by_zone.values()), 2)
        self.assertEqual(sum(stats.observations_by_type.values()), 2)

    def test_report_stats_renders_russian_summary(self) -> None:
        rendered = render_report_stats(calculate_report_stats(build_synthetic_report()))

        self.assertIn("Статистика:", rendered)
        self.assertIn("Зон с находками: 2", rendered)
        self.assertIn("Антральный отдел: 1", rendered)
        self.assertIn("эрозия: 1", rendered)


if __name__ == "__main__":
    unittest.main()
