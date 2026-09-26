import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch, Mock
from urllib.error import HTTPError
from harness.gemini import GeminiAdapter, GEMINI_ENDPOINT, FREE_DEVELOPMENT_MODEL, list_generation_models
from harness.models import ModelHTTPError, ServiceUnavailableError
from harness.rate_limits import RateLimitError
from harness.main import main
from benchmarks.run_free import main as free_main


class GeminiTests(unittest.TestCase):
    @patch('benchmarks.run_sequelize.run', return_value=0)
    @patch('benchmarks.run_free.run_benchmark')
    @patch('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'})
    def test_sequelize_launcher_keeps_selected_free_model(self, fixture, sequelize):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(free_main(['--sequelize', '--free-tier-confirmed']), 0)
        options = sequelize.call_args.args[0]
        self.assertEqual(options[options.index('--model') + 1], FREE_DEVELOPMENT_MODEL)
        self.assertIn('--free-tier-confirmed', options)
        self.assertEqual(options[options.index('--gemini-api-route') + 1], 'native')
        fixture.assert_not_called()

    @patch('benchmarks.run_sequelize.run', side_effect=ValueError('Baseline changed'))
    @patch('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER', 'AI_API_KEY': 'OTHER'})
    def test_sequelize_setup_error_restores_credentials(self, sequelize):
        import os
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(free_main(['--sequelize', '--free-tier-confirmed']), 1)
        self.assertEqual(os.environ['AI_API_KEY'], 'OTHER')
        self.assertEqual(os.environ['GEMINI_API_KEY'], 'PLACEHOLDER')
    @patch('urllib.request.urlopen')
    def test_native_request_and_thought_usage(self, http):
        http.return_value = io.BytesIO(json.dumps({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'thought': True, 'text': 'Internal text'},
            {'text': '{"action":"read_file","arguments":{"path":"catalog.py"}}'}]}}],
            'usageMetadata': {'promptTokenCount': 100, 'candidatesTokenCount': 20, 'thoughtsTokenCount': 30}}).encode())
        adapter = self.adapter()
        adapter.api_route = 'native'
        result = adapter.generate([{'role': 'system', 'content': 'Contract'}, {'role': 'user', 'content': 'Fix'}])
        request = http.call_args.args[0]
        self.assertEqual(request.full_url, 'https://generativelanguage.googleapis.com/v1beta/models/' + FREE_DEVELOPMENT_MODEL + ':generateContent')
        self.assertIsNone(request.get_header('Authorization'))
        self.assertEqual(request.get_header('X-goog-api-key'), 'PLACEHOLDER')
        payload = json.loads(request.data)
        self.assertEqual(payload['generationConfig']['thinkingConfig'], {'thinkingLevel': 'low'})
        self.assertEqual(payload['generationConfig']['responseMimeType'], 'application/json')
        self.assertIn('Contract', payload['systemInstruction']['parts'][0]['text'])
        self.assertEqual(result.actions[0].name, 'read_file')
        self.assertEqual((result.input_tokens, result.output_tokens), (100, 50))
        self.assertNotIn('Internal text', result.content)

    def test_native_25_uses_thinking_budget(self):
        adapter = GeminiAdapter('gemini-2.5-flash', GEMINI_ENDPOINT, 'PLACEHOLDER', api_route='native')
        request = adapter._request({'messages': [{'role': 'user', 'content': 'Fix'}]})
        self.assertEqual(json.loads(request.data)['generationConfig']['thinkingConfig'], {'thinkingBudget': 1024})

    @patch('urllib.request.urlopen')
    @patch('benchmarks.run_free.run_benchmark')
    @patch('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'})
    def test_probe_one_native_request_without_tools_or_benchmark(self, benchmark, http):
        http.return_value = io.BytesIO(json.dumps({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': '{"action":"probe_ok","arguments":{}}'}]}}]}).encode())
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(free_main(['--probe', '--free-tier-confirmed']), 0)
        self.assertIn('probe passed', output.getvalue())
        self.assertNotIn('PLACEHOLDER', output.getvalue())
        self.assertEqual(http.call_count, 1)
        self.assertNotIn('tools', json.loads(http.call_args.args[0].data))
        self.assertEqual(json.loads(http.call_args.args[0].data)['generationConfig']['maxOutputTokens'], 2048)
        benchmark.assert_not_called()

    @patch('urllib.request.urlopen')
    def test_model_listing_paginates_and_filters_without_generation(self, http):
        http.side_effect = [io.BytesIO(json.dumps({'models': [
            {'name': 'models/gemini-example', 'supportedGenerationMethods': ['generateContent']},
            {'name': 'models/embedding-example', 'supportedGenerationMethods': ['embedContent']},
            {'name': 'models/unsafe\nname', 'supportedGenerationMethods': ['generateContent']}],
            'nextPageToken': 'next page'}).encode()), io.BytesIO(b'{"models": []}')]
        self.assertEqual(list_generation_models('PLACEHOLDER'), ['gemini-example'])
        for call in http.call_args_list:
            request = call.args[0]
            self.assertEqual(request.get_method(), 'GET')
            self.assertIsNone(request.data)
            self.assertNotIn('PLACEHOLDER', request.full_url)
        self.assertIn('pageToken=next+page', http.call_args_list[1].args[0].full_url)

    @patch('urllib.request.urlopen')
    def test_model_listing_error_hides_key_and_body(self, http):
        http.side_effect = HTTPError(GEMINI_ENDPOINT, 403, 'SECRET', {}, io.BytesIO(b'SECRET'))
        with self.assertRaises(ModelHTTPError) as caught:
            list_generation_models('PLACEHOLDER')
        self.assertNotIn('SECRET', str(caught.exception))

    @patch('benchmarks.run_free.list_generation_models', return_value=['gemini-example'])
    @patch('benchmarks.run_free.run_benchmark')
    @patch('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'})
    def test_listing_launcher_never_runs_benchmark(self, benchmark, listing):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(free_main(['--list-models', '--free-tier-confirmed']), 0)
        listing.assert_called_once_with('PLACEHOLDER')
        benchmark.assert_not_called()
        self.assertIn('gemini-example', output.getvalue())
        self.assertNotIn('PLACEHOLDER', output.getvalue())

    def test_free_config_matches_selected_model(self):
        config = json.loads((Path(__file__).resolve().parents[1] / 'config/gemini-free.json').read_text())
        self.assertEqual(config['model'], FREE_DEVELOPMENT_MODEL)
        self.assertTrue(config['require_free_tier'])

    def adapter(self):
        adapter = GeminiAdapter(FREE_DEVELOPMENT_MODEL, GEMINI_ENDPOINT, 'PLACEHOLDER')
        adapter.pacer = Mock()
        adapter.pacer.backoff.return_value = 2
        return adapter

    def response(self):
        return io.BytesIO(json.dumps({'choices': [{'message': {'content':
            '{"action":"read_file","arguments":{"path":"catalog.py"}}'}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 20}}).encode())

    @patch('urllib.request.urlopen')
    def test_official_request_shape(self, http):
        http.return_value = self.response()
        adapter = self.adapter()
        result = adapter.generate([{'role': 'system', 'content': 'Contract'}, {'role': 'user', 'content': 'Fix'}])
        self.assertEqual(result.actions[0].name, 'read_file')
        request = http.call_args.args[0]
        self.assertEqual(request.full_url, GEMINI_ENDPOINT + '/chat/completions')
        payload = json.loads(request.data)
        self.assertEqual(payload['reasoning_effort'], 'low')
        self.assertEqual(sum(m['role'] == 'system' for m in payload['messages']), 1)
        self.assertEqual(payload['max_tokens'], 8192)
        self.assertNotIn('tools', payload)
        self.assertEqual(adapter.http_requests, 1)

    @patch('urllib.request.urlopen')
    def test_429_retries_same_endpoint(self, http):
        http.side_effect = [HTTPError(GEMINI_ENDPOINT, 429, 'quota', {'Retry-After': '2'}, io.BytesIO(b'{}')), self.response()]
        adapter = self.adapter()
        with contextlib.redirect_stdout(io.StringIO()):
            adapter.generate([])
        self.assertEqual(adapter.http_requests, 2)
        self.assertEqual(adapter.rate_limit_retries, 1)
        self.assertEqual(adapter.pacer.backoff.call_args.args[1], 2)
        self.assertTrue(all(call.args[0].full_url.startswith(GEMINI_ENDPOINT) for call in http.call_args_list))

    @patch('urllib.request.urlopen')
    def test_daily_quota_stops_without_retry(self, http):
        data = {'error': {'details': [{'@type': 'type.googleapis.com/google.rpc.QuotaFailure',
                                     'violations': [{'quotaId': 'GenerateRequestsPerDayPerProject'}]}]}}
        http.side_effect = HTTPError(GEMINI_ENDPOINT, 429, 'quota', {}, io.BytesIO(json.dumps(data).encode()))
        adapter = self.adapter()
        with self.assertRaises(RateLimitError) as caught:
            adapter.generate([])
        self.assertTrue(caught.exception.terminal_quota)
        self.assertEqual(caught.exception.input_tokens, 0)
        self.assertEqual(http.call_count, 1)
        adapter.pacer.backoff.assert_not_called()

    @patch('urllib.request.urlopen')
    def test_invalid_key_stops_and_hides_body(self, http):
        http.side_effect = HTTPError(GEMINI_ENDPOINT, 403, 'SECRET', {}, io.BytesIO(b'SECRET'))
        with self.assertRaises(ModelHTTPError) as caught:
            self.adapter().generate([])
        self.assertNotIn('SECRET', str(caught.exception))
        self.assertEqual(caught.exception.status_code, 403)

    @patch('urllib.request.urlopen')
    def test_service_errors_retry_identical_request_then_succeed(self, http):
        http.side_effect = [HTTPError(GEMINI_ENDPOINT, code, 'SECRET', {}, io.BytesIO(b'SECRET'))
                            for code in (503, 502)] + [self.response()]
        adapter = self.adapter()
        with contextlib.redirect_stdout(io.StringIO()):
            result = adapter.generate([])
        self.assertEqual(result.actions[0].name, 'read_file')
        self.assertEqual(adapter.service_retries, 2)
        self.assertEqual(adapter.rate_limit_retries, 0)
        self.assertEqual(adapter.http_requests, 3)
        self.assertEqual([c.args[1] for c in adapter.pacer.backoff.call_args_list], [12, 24])
        self.assertTrue(all(c.args[0] is http.call_args_list[0].args[0] for c in http.call_args_list))

    @patch('urllib.request.urlopen')
    def test_persistent_503_stops_loop_as_service_unavailable(self, http):
        import tempfile
        from harness.orchestrator import Orchestrator
        http.side_effect = [HTTPError(GEMINI_ENDPOINT, 503, 'SECRET', {}, io.BytesIO(b'SECRET'))
                            for _ in range(4)]
        adapter = self.adapter()
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            root = Path(folder)
            (root / 'repo').mkdir()
            report = Orchestrator(root / 'repo', 'Fix', adapter, root / 'evidence').run()
        self.assertEqual(report['status'], 'SERVICE_UNAVAILABLE')
        self.assertEqual(report['recoveries'], 0)
        self.assertEqual(report['llm_calls'], 1)
        self.assertEqual(report['http_requests'], 4)
        self.assertEqual(report['service_retries'], 3)
        self.assertEqual(report['input_tokens'], 0)
        self.assertNotIn('SECRET', report['reason'])

    @patch('urllib.request.urlopen')
    def test_service_retry_respects_provider_wait_and_deadline(self, http):
        http.side_effect = HTTPError(GEMINI_ENDPOINT, 503, 'busy', {'Retry-After': '120'}, io.BytesIO(b'{}'))
        adapter = self.adapter()
        adapter.pacer.backoff.side_effect = RateLimitError('Wait exceeds budget', terminal_quota=True)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ServiceUnavailableError):
            adapter.generate([])
        self.assertEqual(adapter.pacer.backoff.call_args.args[1], 120)
        self.assertEqual(http.call_count, 1)

    @patch('urllib.request.urlopen')
    @patch('os.environ', {'AI_API_KEY': 'PLACEHOLDER'})
    def test_free_config_requires_confirmation_and_blocks_paid_override(self, http):
        config = str(Path(__file__).resolve().parents[1] / 'config/gemini-free.json')
        for options in [[], ['--provider', 'openai-responses', '--free-tier-confirmed'],
                        ['--model', 'another-model', '--free-tier-confirmed']]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                main(['--config', config, '--repo', '.', '--issue', 'Fix', *options])
            self.assertEqual(caught.exception.code, 2)
        http.assert_not_called()

    @patch('benchmarks.run_free.run_benchmark')
    @patch('os.environ', {'GEMINI_API_KEY': 'FREE_KEY', 'AI_API_KEY': 'UNRELATED_KEY'})
    def test_free_launcher_uses_gemini_key_only_and_restores_env(self, benchmark):
        import os
        seen = []
        def check(argv):
            seen.append(os.environ['AI_API_KEY'])
            self.assertIn('gemini-compatible', argv)
            self.assertEqual(argv[argv.index('--model') + 1], FREE_DEVELOPMENT_MODEL)
            self.assertIn('--free-tier-confirmed', argv)
            return 0
        benchmark.side_effect = check
        self.assertEqual(free_main(['--free-tier-confirmed']), 0)
        self.assertEqual(seen, ['FREE_KEY'])
        self.assertEqual(os.environ['AI_API_KEY'], 'UNRELATED_KEY')

    @patch('urllib.request.urlopen')
    def test_full_gemini_loop_with_transient_quota(self, http):
        import shutil
        import sys
        import tempfile
        from harness.orchestrator import Orchestrator
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fixture = Path(__file__).resolve().parents[1] / 'benchmarks/label_normalization'
            shutil.copytree(fixture, root / 'repo')
            edit = {'action': 'edit_file', 'arguments': {'path': 'catalog.py',
                'old': 'return sorted(set(label for label in normalized if label))',
                'new': 'return list(dict.fromkeys(label for label in normalized if label))'}}
            finish = {'action': 'finish', 'arguments': {'summary': 'Preserve order',
                'semantic_review': 'Preserves first occurrence order after trim/casefold. Unicode, generator, blank, empty, mutation tests retained.'}}
            def response(actions):
                return io.BytesIO(json.dumps({'choices': [{'message': {'content': json.dumps({'actions': actions})}}],
                                             'usage': {'prompt_tokens': 100, 'completion_tokens': 40}}).encode())
            http.side_effect = [HTTPError(GEMINI_ENDPOINT, 429, 'quota', {'Retry-After': '2'}, io.BytesIO(b'{}')),
                                response([edit, finish]), response([finish])]
            adapter = self.adapter()
            with contextlib.redirect_stdout(io.StringIO()):
                report = Orchestrator(root / 'repo', 'Fix label order', adapter, root / 'evidence',
                           test_commands=[f'{sys.executable} -m unittest discover -s tests -v']).run()
            self.assertEqual(report['status'], 'RESOLVED')
            self.assertEqual(report['rate_limit_retries'], 1)
            self.assertEqual(report['http_requests'], 3)
            self.assertEqual(report['files_modified'], ['catalog.py'])
            self.assertEqual(report['test_counts'][-1]['collected'], 6)
            self.assertIn('rate_limit', (Path(report['artifacts']) / 'events.jsonl').read_text())

    def test_quota_error_terminates_loop_without_recovery_spin(self):
        import tempfile
        from harness.orchestrator import Orchestrator
        class QuotaAdapter(GeminiAdapter):
            def generate(self, messages, tools=None):
                raise RateLimitError('Daily quota exhausted', terminal_quota=True)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'repo').mkdir()
            adapter = QuotaAdapter(FREE_DEVELOPMENT_MODEL, GEMINI_ENDPOINT, 'PLACEHOLDER')
            report = Orchestrator(root / 'repo', 'Fix', adapter, root / 'evidence').run()
            self.assertEqual(report['status'], 'QUOTA_EXHAUSTED')
            self.assertEqual(report['llm_calls'], 1)
            self.assertEqual(report['recoveries'], 0)
            self.assertEqual(report['input_tokens'], 0)
            self.assertEqual(report['output_tokens'], 0)

    @patch('harness.main.Orchestrator')
    @patch('os.environ', {'GEMINI_API_KEY': 'FREE_KEY', 'AI_API_KEY': 'OTHER_KEY'})
    def test_direct_free_config_never_uses_unrelated_key(self, orchestrator):
        report = dict(status='RESOLVED', verification='PASS', model=FREE_DEVELOPMENT_MODEL,
                      steps=1, llm_calls=1, tool_calls=1, input_tokens=100, output_tokens=10,
                      usage_estimated=False, files_modified=['catalog.py'], diff_additions=1,
                      diff_deletions=1, reason='Verified', artifacts='placeholder')
        orchestrator.return_value.run.return_value = report
        config = Path(__file__).resolve().parents[1] / 'config/gemini-free.json'
        with contextlib.redirect_stdout(io.StringIO()):
            main(['--config', str(config), '--free-tier-confirmed', '--repo', '.', '--issue', 'Fix'])
        self.assertEqual(orchestrator.call_args.args[2].api_key, 'FREE_KEY')

    @patch('urllib.request.urlopen')
    def test_malformed_key_never_reaches_transport_or_leaks(self, http):
        for key in ('SECRET\n', 'SECRET\r', 'SECRET\x00', 'SECRET '):
            with self.assertRaises(ValueError) as caught:
                GeminiAdapter(FREE_DEVELOPMENT_MODEL, GEMINI_ENDPOINT, key)
            self.assertNotIn('SECRET', str(caught.exception))
        http.assert_not_called()

    @patch('sys.stdin.isatty', return_value=False)
    @patch('benchmarks.run_free.run_benchmark')
    def test_noninteractive_free_launcher_never_assumes_confirmation(self, benchmark, tty):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            free_main([])
        benchmark.assert_not_called()
