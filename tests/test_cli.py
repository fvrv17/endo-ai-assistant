import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from endo_ai_assistant import EndoAgentPlan, EndoAgentRun
from endo_ai_assistant.dev_extractors import SyntheticGastroscopyExtractor
from endo_ai_assistant.cli import main


class CliSmokeTest(unittest.TestCase):
    def test_demo_outputs_rendered_report(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--demo"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Исследование: ЭГДС", stdout.getvalue())
        self.assertIn("Антральный отдел", stdout.getvalue())

    def test_demo_with_stats_outputs_rendered_report_and_statistics(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--demo", "--stats"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Исследование: ЭГДС", stdout.getvalue())
        self.assertIn("Статистика:", stdout.getvalue())
        self.assertIn("Всего находок: 2", stdout.getvalue())

    def test_schema_outputs_json(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--schema"])

        schema = json.loads(stdout.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(schema["title"], "ExtractedFindings")
        self.assertIn("findings", schema["properties"])

    def test_strict_schema_outputs_provider_ready_json(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--strict-schema"])

        schema = json.loads(stdout.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(schema["required"], ["findings"])
        self.assertIn("location", schema["$defs"]["Observation"]["required"])

    def test_nomenclature_outputs_json(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--nomenclature"])

        payload = json.loads(stdout.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertIn("gastroscopy_zones", payload)
        self.assertIn("colonoscopy_zones", payload)
        self.assertIn("finding_types", payload)
        self.assertIn("antrum", {item["code"] for item in payload["gastroscopy_zones"]})
        self.assertIn("rectum", {item["code"] for item in payload["colonoscopy_zones"]})

    def test_prompt_outputs_extraction_prompts(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--demo", "--prompt"])

        self.assertEqual(exit_code, 0)
        self.assertIn("SYSTEM PROMPT", stdout.getvalue())
        self.assertIn("USER PROMPT", stdout.getvalue())
        self.assertIn("Doctor input:", stdout.getvalue())

    def test_eval_outputs_summary(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--eval", "eval_cases/synthetic_endoscopy.json"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Eval summary", stdout.getvalue())
        self.assertIn("Cases: 8/12 passed", stdout.getvalue())
        self.assertIn("Structural recall: 92.31%", stdout.getvalue())
        self.assertIn("Negation false-positives: 2", stdout.getvalue())

    def test_agent_outputs_structured_plan(self) -> None:
        stdout = io.StringIO()
        agent_run = EndoAgentRun(
            plan=EndoAgentPlan(
                intent="summarize_note",
                summary="The user wants a short summary.",
                needs_extraction=False,
                confidence=0.9,
                safety_note="No clinical report should be produced.",
            )
        )

        with patch("endo_ai_assistant.cli.run_endo_agent", return_value=agent_run):
            with redirect_stdout(stdout):
                exit_code = main(["--agent", "--text", "Summarize this note."])

        self.assertEqual(exit_code, 0)
        self.assertIn("Agent plan:", stdout.getvalue())
        self.assertIn("Intent: summarize_note", stdout.getvalue())
        self.assertIn("The user wants a short summary.", stdout.getvalue())

    def test_agent_reports_setup_failure_without_traceback(self) -> None:
        stderr = io.StringIO()

        with patch(
            "endo_ai_assistant.cli.run_endo_agent",
            side_effect=RuntimeError("Missing credentials"),
        ):
            with redirect_stderr(stderr):
                exit_code = main(["--agent", "--text", "Summarize this note."])

        self.assertEqual(exit_code, 1)
        self.assertIn("Agent run failed: Missing credentials", stderr.getvalue())

    def test_live_smoke_requires_openai_provider(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as caught:
                main(["--live-smoke"])

        self.assertEqual(caught.exception.code, 2)

    def test_live_smoke_outputs_render_and_eval_summary(self) -> None:
        stdout = io.StringIO()

        with patch(
            "endo_ai_assistant.cli.build_extractor",
            return_value=SyntheticGastroscopyExtractor(),
        ) as build_extractor:
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "--provider",
                        "openai",
                        "--live-smoke",
                        "eval_cases/synthetic_endoscopy.json",
                    ]
                )

        self.assertEqual(exit_code, 0)
        build_extractor.assert_called_once()
        self.assertIn("Live smoke case: egd_erosion_ulcer_001", stdout.getvalue())
        self.assertIn("Исследование: ЭГДС", stdout.getvalue())
        self.assertIn("Статистика:", stdout.getvalue())
        self.assertIn("Eval summary", stdout.getvalue())
        self.assertIn("Cases: 8/12 passed", stdout.getvalue())

    def test_live_smoke_reports_setup_failure_without_traceback(self) -> None:
        stderr = io.StringIO()

        with patch(
            "endo_ai_assistant.cli.build_extractor",
            side_effect=RuntimeError("Missing credentials"),
        ):
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "--provider",
                        "openai",
                        "--live-smoke",
                        "eval_cases/synthetic_endoscopy.json",
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertIn("Live smoke setup failed: Missing credentials", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
