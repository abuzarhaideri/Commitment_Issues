import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from harness.main import main

REPORT = dict(status='RESOLVED', verification='PASS', model='fixture', steps=1,
              llm_calls=1, tool_calls=1, input_tokens=1, output_tokens=1,
              usage_estimated=True, files_modified=['calc.py'], diff_additions=1,
              diff_deletions=1, reason='verified', artifacts='fixture')


class EvaluationTests(unittest.TestCase):
    def test_reserve_and_retry_options_reach_runtime(self):
        _, _, call = self.call(['--evaluation', '--provider', 'openai-compatible',
            '--model', 'organiser-model', '--base-url', 'https://example.test/v1',
            '--repo', '.', '--issue', 'Fix', '--token-reserve', '500', '--max-rate-retries', '1'])
        self.assertEqual(call.kwargs['token_reserve'], 500)
        self.assertEqual(call.args[2].max_retries, 1)

    def test_invalid_reserve_rejected_before_launch(self):
        for reserve in ['-1', '100001']:
            with self.subTest(reserve=reserve), self.assertRaises(SystemExit), patch('sys.stderr', new_callable=io.StringIO):
                self.call(['--evaluation', '--launch-check', '--budget', '100000', '--token-reserve', reserve])

    def call(self, args, env=None, task=''):
        with patch.dict('os.environ', env or {'AI_API_KEY': 'TEST_PLACEHOLDER'}, clear=True), \
             patch('sys.stdin', io.StringIO(task)), patch('sys.stdout', new_callable=io.StringIO) as output, \
             patch('harness.main.Orchestrator') as runner:
            runner.return_value.run.return_value = REPORT
            code = main(args)
            return code, output.getvalue(), runner.call_args

    @patch('urllib.request.urlopen', side_effect=AssertionError('No request allowed'))
    def test_default_profile_launch_check_no_api(self, http):
        code, output, runner = self.call(['--evaluation', '--launch-check'])
        self.assertEqual(code, 0)
        self.assertIn('HARNESS READY', output)
        self.assertIn('provisional', output)
        self.assertIsNone(runner)
        http.assert_not_called()

    def test_task_json_supports_multiline_and_tests(self):
        code, _, call = self.call(['--evaluation'], task='{"repo":".","issue":"first\\nsecond","test_commands":["python -m unittest"]}\n')
        self.assertEqual(code, 0)
        self.assertEqual(call.args[1], 'first\nsecond')
        self.assertEqual(call.kwargs['test_commands'], ['python -m unittest'])
        self.assertEqual(call.args[2].api_key, 'TEST_PLACEHOLDER')

    def test_official_overrides_provisional_model_and_provider(self):
        _, _, call = self.call(['--evaluation', '--repo', '.', '--issue', 'Fix'], env={
            'AI_API_KEY': 'TEST_PLACEHOLDER', 'HARNESS_OFFICIAL_PROVIDER': 'openai-compatible',
            'HARNESS_OFFICIAL_MODEL': 'organiser-model', 'HARNESS_OFFICIAL_BASE_URL': 'https://example.test/v1'})
        self.assertEqual(call.args[2].model, 'organiser-model')
        self.assertEqual(call.args[2].base_url, 'https://example.test/v1')

    def test_evaluation_never_reuses_development_key(self):
        with self.assertRaises(SystemExit) as caught, patch('sys.stderr', new_callable=io.StringIO):
            self.call(['--evaluation', '--launch-check'], env={'GEMINI_API_KEY': 'DEVELOPMENT_ONLY'})
        self.assertEqual(caught.exception.code, 2)

    def test_invalid_task_input_rejected(self):
        for task in ['', '[]\n', '{"repo":".","issue":3}\n', '{"repo":".","issue":"Fix","unexpected":true}\n',
                     '{"repo":".","issue":"Fix","test_commands":"bad"}\n']:
            with self.subTest(task=task), self.assertRaises(SystemExit), patch('sys.stderr', new_callable=io.StringIO):
                self.call(['--evaluation'], task=task)

    def test_issue_file(self):
        with tempfile.TemporaryDirectory() as directory:
            issue = Path(directory) / 'issue.txt'
            issue.write_text('multiline\nissue', encoding='utf-8')
            _, _, call = self.call(['--evaluation', '--repo', '.', '--issue-file', str(issue)])
            self.assertEqual(call.args[1], 'multiline\nissue')

    def test_no_key_configuration_rejected(self):
        with self.assertRaises(SystemExit), patch('sys.stderr', new_callable=io.StringIO):
            self.call(['--evaluation', '--launch-check'], env={'UNRELATED': 'value'})

    def test_free_profile_cannot_be_evaluator_entry_point(self):
        with self.assertRaises(SystemExit), patch('sys.stderr', new_callable=io.StringIO):
            self.call(['--evaluation', '--config', 'config/gemini-free.json', '--launch-check'])
