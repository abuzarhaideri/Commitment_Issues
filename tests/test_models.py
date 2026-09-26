import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from harness.models import ModelError, OpenAICompatibleAdapter, ProtocolError


class ModelTests(unittest.TestCase):
    def adapter(self, native=False):
        return OpenAICompatibleAdapter("explicit-model", "https://example.test/v1", "SECRET", native)

    def response(self, message, usage=None):
        result = {"choices": [{"message": message}]}
        if usage is not None:
            result["usage"] = usage
        return io.BytesIO(json.dumps(result).encode())

    @patch("urllib.request.urlopen")
    def test_json_fence_and_usage(self, http):
        http.return_value = self.response({"content": '```json\n{"actions":[{"action":"finish","arguments":{"summary":"Done","semantic_review":"Checked"},"goal":"close"}]}\n```'}, {"prompt_tokens": 10, "completion_tokens": 20})
        response = self.adapter().generate([{"role": "user", "content": "work"}])
        self.assertEqual(response.actions[0].name, "finish")
        self.assertEqual(response.actions[0].goal, "close")
        self.assertEqual((response.input_tokens, response.output_tokens, response.usage_estimated), (10, 20, False))
        payload = json.loads(http.call_args.args[0].data)
        self.assertEqual(payload["max_tokens"], 2048)
        self.assertIn("strict JSON", payload["messages"][0]["content"])

    @patch("urllib.request.urlopen")
    def test_native_tools(self, http):
        http.return_value = self.response({"content": None, "tool_calls": [{"function": {"name": "read", "arguments": '{"path":"a"}'}}]})
        adapter = self.adapter(True)
        response = adapter.generate([], [{"name": "read", "parameters": {"type": "object"}}])
        self.assertTrue(adapter.supports_native_tools())
        self.assertEqual(response.actions[0].arguments, {"path": "a"})
        self.assertTrue(response.usage_estimated)
        self.assertGreater(response.input_tokens, 0)
        self.assertEqual(json.loads(http.call_args.args[0].data)["tools"][0]["type"], "function")

    @patch("urllib.request.urlopen")
    def test_malformed_actions(self, http):
        for value in [[], "text", {"actions": [1]}, {"action": "read", "arguments": []}, {"action": "finish", "arguments": {"summary": "done"}}, {"actions": []}, {"action": "read", "arguments": {}, "goal": 1}]:
            with self.subTest(value=value):
                http.return_value = self.response({"content": json.dumps(value)})
                with self.assertRaises(ProtocolError):
                    self.adapter().generate([])

    @patch("urllib.request.urlopen")
    def test_invalid_usage_is_estimated(self, http):
        http.return_value = self.response({"content": '{"action":"read","arguments":{}}'}, {"prompt_tokens": -1, "completion_tokens": True})
        self.assertTrue(self.adapter().generate([]).usage_estimated)

    @patch("urllib.request.urlopen")
    def test_errors_do_not_expose_secrets(self, http):
        for error in [URLError("SECRET"), HTTPError("SECRET", 403, "SECRET", {}, None)]:
            http.side_effect = error
            with self.assertRaises(ModelError) as caught:
                self.adapter().generate([])
            self.assertNotIn("SECRET", str(caught.exception))

    def test_explicit_model(self):
        with self.assertRaises(ValueError):
            OpenAICompatibleAdapter("", "https://example.test", "key")

    def test_url_validation(self):
        for url in ["http://example.test", "ftp://localhost", "https://SECRET@example.test", "https://example.test?SECRET", "https://example.test#SECRET", "https://example.test:SECRET", "https://example.test?", "https://example.test#"]:
            with self.subTest(url=url), self.assertRaises(ValueError) as caught:
                OpenAICompatibleAdapter("model", url, "key")
            self.assertNotIn("SECRET", str(caught.exception))
        for url in ["https://example.test/v1", "http://localhost:8000/v1", "http://127.0.0.1:8000", "http://[::1]:8000"]:
            OpenAICompatibleAdapter("model", url, "key")

    @patch("urllib.request.urlopen")
    def test_response_size_limit(self, http):
        http.return_value = io.BytesIO(b"x" * (2 * 1024 * 1024 + 1))
        with self.assertRaises(ModelError):
            self.adapter().generate([])

    @patch("urllib.request.urlopen")
    def test_non_string_native_arguments(self, http):
        for arguments in [None, 1, {}, []]:
            http.return_value = self.response({"tool_calls": [{"function": {"name": "read", "arguments": arguments}}]})
            with self.subTest(arguments=arguments), self.assertRaises(ProtocolError):
                self.adapter(True).generate([])

    @patch("urllib.request.urlopen")
    def test_custom_token_bound(self, http):
        http.return_value = self.response({"content": '{"action":"read","arguments":{}}'})
        OpenAICompatibleAdapter("model", "https://example.test", "key", max_output_tokens=100).generate([])
        self.assertEqual(json.loads(http.call_args.args[0].data)["max_tokens"], 100)
        for value in [0, -1, True, "SECRET"]:
            with self.assertRaises(ValueError) as caught:
                OpenAICompatibleAdapter("model", "https://example.test", "key", max_output_tokens=value)
            self.assertNotIn("SECRET", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
