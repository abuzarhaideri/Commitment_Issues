import io
import json
import unittest
from unittest.mock import patch
from harness.openai_responses import OpenAIResponsesAdapter
from harness.models import ModelError, ProtocolError
from harness.main import main


class ResponsesTests(unittest.TestCase):
    def adapter(self):
        return OpenAIResponsesAdapter('gpt-6-luna', 'https://api.openai.com/v1', 'PLACEHOLDER')

    def response(self, text, status='completed', usage=None):
        return io.BytesIO(json.dumps({'status': status, 'output': [
            {'type': 'reasoning', 'encrypted_content': 'opaque'},
            {'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}],
            'usage': usage or {'input_tokens': 100, 'output_tokens': 80}}).encode())

    @patch('urllib.request.urlopen')
    def test_request_and_action_normalization(self, http):
        http.return_value = self.response('{"actions":[{"action":"read_file","arguments":{"path":"calc.py"}}]}')
        result = self.adapter().generate([{'role': 'user', 'content': 'Inspect'}], tools=[])
        self.assertEqual(result.actions[0].name, 'read_file')
        self.assertEqual((result.input_tokens, result.output_tokens), (100, 80))
        self.assertFalse(result.usage_estimated)
        request = http.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.openai.com/v1/responses')
        payload = json.loads(request.data)
        self.assertEqual(payload['reasoning'], {'effort': 'low'})
        self.assertEqual(payload['max_output_tokens'], 8192)
        self.assertFalse(payload['store'])
        self.assertNotIn('max_tokens', payload)
        self.assertNotIn('tools', payload)
        self.assertIn('one strict JSON action object', payload['input'][0]['content'])

    @patch('urllib.request.urlopen')
    def test_incomplete_response_preserves_billed_usage(self, http):
        http.return_value = self.response('', status='incomplete')
        with self.assertRaises(ProtocolError) as caught:
            self.adapter().generate([])
        self.assertEqual(caught.exception.output_tokens, 80)
        self.assertFalse(caught.exception.usage_estimated)

    @patch('urllib.request.urlopen')
    def test_invalid_json_preserves_usage(self, http):
        http.return_value = self.response('unstructured answer')
        with self.assertRaises(ProtocolError) as caught:
            self.adapter().generate([])
        self.assertEqual(caught.exception.input_tokens, 100)

    @patch('urllib.request.urlopen')
    def test_invalid_usage_estimated(self, http):
        http.return_value = self.response('{"action":"read_file","arguments":{"path":"a"}}', usage={'input_tokens': -1})
        self.assertTrue(self.adapter().generate([]).usage_estimated)

    @patch('urllib.request.urlopen')
    def test_non_object_and_refusal(self, http):
        for result in [[], {'status': 'completed', 'output': [None]},
                       {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'refusal'}]}]}]:
            http.return_value = io.BytesIO(json.dumps(result).encode())
            with self.assertRaises(ProtocolError):
                self.adapter().generate([])

    @patch('harness.main.Orchestrator')
    @patch('os.environ', {'AI_API_KEY': 'PLACEHOLDER'})
    def test_prepared_config_is_usable(self, orchestrator):
        import contextlib
        from pathlib import Path
        report = dict(status='RESOLVED', verification='PASS', model='gpt-6-luna',
                      steps=1, llm_calls=1, tool_calls=1, input_tokens=100, output_tokens=10,
                      usage_estimated=False, files_modified=['calc.py'], diff_additions=1,
                      diff_deletions=1, reason='Verified', artifacts='placeholder')
        orchestrator.return_value.run.return_value = report
        config = Path(__file__).resolve().parents[1] / 'config/openai-luna.json'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--config', str(config), '--repo', '.', '--issue', 'Fix']), 0)
        adapter = orchestrator.call_args.args[2]
        self.assertIsInstance(adapter, OpenAIResponsesAdapter)
        self.assertEqual(adapter.model, 'gpt-6-luna')
        self.assertEqual(adapter.reasoning_effort, 'low')

    def test_invalid_reasoning_effort(self):
        with self.assertRaises(ValueError):
            OpenAIResponsesAdapter('gpt-6-luna', 'https://api.openai.com/v1', 'placeholder', reasoning_effort='invalid')
