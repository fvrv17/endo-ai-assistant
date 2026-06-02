import unittest
from typing import Any, Mapping

from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from endo_ai_assistant import (
    EndoAgentPlan,
    EndoIntent,
    EndoscopyType,
    build_endo_agent,
    run_endo_agent,
)
from endo_ai_assistant.pipeline import DEMO_INPUT


def _function_model_for_output(output: Mapping[str, Any]) -> FunctionModel:
    def call_agent(messages, info: AgentInfo) -> ModelResponse:
        output_tool = info.output_tools[0]
        return ModelResponse(parts=[ToolCallPart(output_tool.name, dict(output))])

    return FunctionModel(call_agent)


class PydanticAIEndoAgentTest(unittest.TestCase):
    def test_agent_plan_can_trigger_existing_extraction_pipeline(self) -> None:
        agent = build_endo_agent()
        model = _function_model_for_output(
            {
                "intent": "structure_report",
                "summary": "The user provided a gastroscopy note to structure.",
                "needs_extraction": True,
                "confidence": 0.93,
                "safety_note": "Output must be reviewed and signed by a physician.",
            }
        )

        with agent.override(model=model):
            result = run_endo_agent(
                user_input=DEMO_INPUT,
                exam_type=EndoscopyType.GASTROSCOPY,
                extraction_provider="synthetic",
                agent=agent,
            )

        self.assertEqual(result.plan.intent, EndoIntent.STRUCTURE_REPORT)
        self.assertIsNotNone(result.report)
        self.assertIn("Исследование: ЭГДС", result.report_text or "")
        self.assertIn("Статистика:", result.stats_text or "")
        self.assertTrue(result.review_flags)

    def test_summarize_intent_does_not_extract_report(self) -> None:
        agent = build_endo_agent()
        model = _function_model_for_output(
            {
                "intent": "summarize_note",
                "summary": "The user wants a short non-diagnostic summary.",
                "needs_extraction": False,
                "confidence": 0.88,
                "safety_note": "No structured clinical report should be produced.",
            }
        )

        with agent.override(model=model):
            result = run_endo_agent(
                user_input="Summarize what this module does.",
                agent=agent,
            )

        self.assertEqual(result.plan.intent, EndoIntent.SUMMARIZE_NOTE)
        self.assertIsNone(result.report)
        self.assertIsNone(result.report_text)
        self.assertEqual(result.review_flags, [])

    def test_agent_plan_rejects_inconsistent_extraction_flag(self) -> None:
        with self.assertRaises(ValidationError):
            EndoAgentPlan(
                intent=EndoIntent.OUT_OF_SCOPE,
                summary="Out of scope request.",
                needs_extraction=True,
                confidence=0.5,
                safety_note="Do not extract.",
            )


if __name__ == "__main__":
    unittest.main()
