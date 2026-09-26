"""Offline wire contracts; fixtures do not certify a deployed provider/model."""
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from harness.models import OpenAICompatibleAdapter, ModelHTTPError, ModelError, ProtocolError
from harness.openai_responses import OpenAIResponsesAdapter


def response(value):
    return io.BytesIO(json.dumps(value).encode())


def chat(content=None, calls=None, reason="stop"):
    return {"choices": [{"finish_reason": reason, "message": {
        "content": content, "reasoning_content": "private deliberation",
        "tool_calls": calls}}], "usage": {"prompt_tokens": 31, "completion_tokens": 19}}


class ProviderContracts(unittest.TestCase):
    def adapter(self, native=False, **kwargs):
        return OpenAICompatibleAdapter("explicit-prescribed-id", "https://provider.test/compatible/v1",
                                       "PRIVATEKEY", native_tools=native, **kwargs)

    @patch("urllib.request.urlopen")
    def test_reasoning_is_separate_and_wire_identity_preserved(self, http):
        for native in (False, True):
            with self.subTest(native=native):
                calls = [{"type": "function", "function": {"name": "read_file", "arguments": '{"path":"x"}'}}]
                http.return_value = response(chat('{"action":"read_file","arguments":{"path":"x"}}',
                                                  calls if native else None,
                                                  "tool_calls" if native else "stop"))
                result = self.adapter(native).generate([], [{"name": "read_file", "parameters": {"type": "object"}}])
                self.assertEqual(result.actions[0].arguments, {"path": "x"})
                self.assertNotIn("private", result.content)
                request = http.call_args.args[0]
                self.assertEqual(request.full_url, "https://provider.test/compatible/v1/chat/completions")
                self.assertEqual(request.get_header("Authorization"), "Bearer PRIVATEKEY")
                self.assertEqual(json.loads(request.data)["model"], "explicit-prescribed-id")
                self.assertEqual((result.input_tokens, result.output_tokens, result.usage_estimated), (31, 19, False))

    @patch("urllib.request.urlopen")
    def test_reasoning_never_substitutes_for_action(self, http):
        http.return_value = response(chat(None))
        with self.assertRaises(ProtocolError):
            self.adapter().generate([])

    @patch("urllib.request.urlopen")
    def test_partial_native_batch_is_never_returned(self, http):
        for reason, arguments in [("length", "{}"), ("tool_calls", "bad")]:
            http.return_value = response(chat(calls=[
                {"function": {"name": "read", "arguments": "{}"}},
                {"function": {"name": "edit", "arguments": arguments}}], reason=reason))
            with self.assertRaises(ProtocolError) as caught:
                self.adapter(True).generate([])
            self.assertEqual(caught.exception.output_tokens, 19)

    @patch("harness.models.time.sleep")
    @patch("urllib.request.urlopen")
    def test_retry_after_then_success_reuses_identity(self, http, sleep):
        http.side_effect = [HTTPError("PRIVATE", 503, "PRIVATE", {"Retry-After": "3"}, None),
                            response(chat('{"action":"read","arguments":{}}'))]
        adapter = self.adapter()
        adapter.generate([])
        sleep.assert_called_once_with(3)
        self.assertEqual(adapter.http_requests, 2)
        self.assertIs(http.call_args_list[0].args[0], http.call_args_list[1].args[0])

    @patch("harness.models.time.sleep")
    @patch("urllib.request.urlopen")
    def test_fatal_and_unhinted_quota_never_retry(self, http, sleep):
        for status in (400, 401, 403, 404, 429):
            http.reset_mock()
            http.side_effect = HTTPError("PRIVATEKEY", status, "PRIVATEKEY", {}, None)
            with self.assertRaises(ModelHTTPError) as caught:
                self.adapter().generate([])
            self.assertEqual(http.call_count, 1)
            self.assertNotIn("PRIVATE", str(caught.exception))
        sleep.assert_not_called()

    @patch("harness.models.time.sleep")
    @patch("urllib.request.urlopen")
    def test_exhaustion_is_bounded(self, http, sleep):
        http.side_effect = HTTPError("PRIVATE", 502, "PRIVATE", {}, None)
        with self.assertRaises(ModelHTTPError):
            self.adapter(max_retries=2).generate([])
        self.assertEqual(http.call_count, 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])

    @patch("harness.models.time.monotonic", return_value=100)
    @patch("harness.models.time.sleep")
    @patch("urllib.request.urlopen")
    def test_deadline_prevents_retry_wait_and_bounds_socket(self, http, sleep, monotonic):
        http.side_effect = HTTPError("PRIVATE", 503, "PRIVATE", {"Retry-After": "20"}, None)
        adapter = self.adapter()
        adapter.deadline = 110
        with self.assertRaises(ModelHTTPError):
            adapter.generate([])
        self.assertEqual(http.call_args.kwargs["timeout"], 10)
        sleep.assert_not_called()
        adapter.deadline = 99
        with self.assertRaises(ModelError):
            adapter.generate([])
        self.assertEqual(http.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_estimates_include_exact_instruction_and_wire_overhead(self, http):
        messages = [{"role": "user", "content": "inspect हिन्दी 中文"}]
        tools = [{"name": "read", "parameters": {"type": "object"}}]
        adapters = [self.adapter(), self.adapter(True),
                    OpenAIResponsesAdapter("explicit", "https://provider.test/v1", "PRIVATEKEY")]
        for adapter in adapters:
            with self.subTest(adapter=type(adapter).__name__, native=adapter.native_tools):
                fixture = ({"status": "completed", "output": [{"type": "message", "content": [
                    {"type": "output_text", "text": '{"action":"read","arguments":{}}'}]}]}
                    if isinstance(adapter, OpenAIResponsesAdapter) else chat('{"action":"read","arguments":{}}'))
                http.return_value = response(fixture)
                estimate = adapter.estimate_request_tokens(messages, tools)
                adapter.generate(messages, tools)
                self.assertEqual(estimate, adapter.count_or_estimate_tokens(http.call_args.args[0].data.decode()))
                self.assertGreater(estimate, adapter.count_or_estimate_tokens(messages))
                self.assertEqual(len(messages), 1)

    @patch("harness.models.time.time", return_value=0)
    @patch("harness.models.time.sleep")
    @patch("urllib.request.urlopen")
    def test_http_date_retry_hint_and_callback(self, http, sleep, wall):
        http.side_effect = [HTTPError("PRIVATE", 429, "PRIVATE",
                                     {"Retry-After": "Thu, 01 Jan 1970 00:00:05 GMT"}, None),
                            response(chat('{"action":"read","arguments":{}}'))]
        adapter = self.adapter()
        events = []
        adapter.event_callback = lambda kind, **data: events.append((kind, data))
        adapter.generate([])
        sleep.assert_called_once_with(5)
        self.assertEqual(adapter.transport_retries, 1)
        self.assertEqual(events[0][0], "transport_retry")
        self.assertNotIn("PRIVATE", str(events))

    @patch("urllib.request.urlopen")
    def test_responses_incomplete_message_never_yields_action(self, http):
        http.return_value = response({"status": "completed", "usage": {
            "input_tokens": 9, "output_tokens": 8}, "output": [{"type": "message",
            "status": "incomplete", "content": [{"type": "output_text",
            "text": '{"action":"edit","arguments":{}}'}]}]})
        adapter = OpenAIResponsesAdapter("explicit", "https://provider.test/v1", "PRIVATEKEY")
        with self.assertRaises(ProtocolError) as caught:
            adapter.generate([])
        self.assertEqual(caught.exception.output_tokens, 8)

    def test_retry_knob_validation(self):
        for value in (-1, 6, True, 1.5):
            with self.assertRaises(ValueError):
                self.adapter(max_retries=value)


if __name__ == "__main__":
    unittest.main()
