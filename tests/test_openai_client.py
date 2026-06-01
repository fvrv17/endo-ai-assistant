import json
import unittest
from typing import Any, Mapping, Optional

from endo_ai_assistant import extraction_json_schema
from endo_ai_assistant.openai_client import OpenAIStructuredClient


class FakeResponse:
    output_text = json.dumps({"findings": []})


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs: Optional[Mapping[str, Any]] = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return FakeResponse()


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


class OpenAIStructuredClientTest(unittest.TestCase):
    def test_complete_json_sends_strict_json_schema_request(self) -> None:
        fake_client = FakeOpenAIClient()
        client = OpenAIStructuredClient(model="test-model", client=fake_client)

        payload = client.complete_json(
            system_prompt="system",
            user_prompt="user",
            json_schema=extraction_json_schema(),
        )

        self.assertEqual(payload, {"findings": []})
        request = fake_client.responses.kwargs
        self.assertIsNotNone(request)
        assert request is not None

        self.assertEqual(request["model"], "test-model")
        self.assertEqual(request["input"][0]["role"], "system")
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertTrue(request["text"]["format"]["strict"])

        schema = request["text"]["format"]["schema"]
        self.assertEqual(schema["required"], ["findings"])
        observation_schema = schema["$defs"]["Observation"]
        self.assertIn("location", observation_schema["required"])
        self.assertIn("size_mm", observation_schema["required"])
        self.assertFalse(_contains_key(schema, "default"))


def _contains_key(node, key: str) -> bool:
    if isinstance(node, dict):
        return key in node or any(_contains_key(value, key) for value in node.values())
    if isinstance(node, list):
        return any(_contains_key(value, key) for value in node)
    return False


if __name__ == "__main__":
    unittest.main()
