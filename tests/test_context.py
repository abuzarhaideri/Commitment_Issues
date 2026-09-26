import json
import unittest
from harness.context import ContextManager, filter_observation


class ObservationTests(unittest.TestCase):
    def test_protocol_recovery_keeps_contract_diagnosis_and_exact_source(self):
        from types import SimpleNamespace
        from harness.demo import ScriptedAdapter
        from harness.context import SYSTEM
        context = ContextManager()
        context.add({'name': 'read_file', 'arguments': {'path': 'calc.py'}},
                    {'ok': True, 'output': '1: def add(a, b):\n2:     return a - b\n'})
        for i in range(8):
            context.add({'name': 'run_command', 'arguments': {'command': 'echo'}},
                        {'ok': True, 'output': 'IRRELEVANT' * 400})
        state = SimpleNamespace(issue='Fix addition', repo='/tmp/repo', plan=['edit', 'verify'],
                                verification='NOT_RUN', failures=[], candidate_context_tokens=0,
                                sent_context_tokens=0, findings=[{'hypothesis': 'subtracts',
                                'evidence': 'calc.py:2', 'next_action': 'replace operator'}])
        context.recover_protocol()
        packed = context.pack(state, {'test_commands': ['verify'], 'markers': ['pyproject.toml'],
                                    'repo_map': ['UNRELATED_MAP'] * 100, 'hints': ['UNRELATED_HINT']},
                              [], ScriptedAdapter([]))
        text = json.dumps(packed)
        self.assertEqual(packed[0]['content'], SYSTEM)
        self.assertIn('return a - b', text)
        self.assertIn('subtracts', text)
        self.assertIn('verify', text)
        self.assertNotIn('IRRELEVANT', text)
        self.assertNotIn('UNRELATED_MAP', text)
        self.assertNotIn('UNRELATED_HINT', text)
        self.assertIn('pyproject.toml', text)
        self.assertIn('ONE small action', text)
        self.assertLessEqual(len(packed), 6)
        self.assertEqual(len(context.history), 9)
        context.clear_protocol_recovery()
        normal = context.pack(state, {}, [], ScriptedAdapter([]))
        self.assertIn('IRRELEVANT', json.dumps(normal))

    def test_interior_failure_survives_large_output(self):
        output = 'ordinary output\n' * 600 + 'AssertionError: SENTINEL expected 4 got 9\n' + 'ordinary output\n' * 600
        result = {'ok': False, 'output': output, 'returncode': 1}
        filtered = filter_observation(result)
        self.assertIn('SENTINEL expected 4 got 9', filtered)
        self.assertIn('TRUNCATED', filtered)
        self.assertLessEqual(len(filtered), 6000)
        repeated_errors = {'ok': False, 'output': 'AssertionError: long failure details\n' * 1000}
        self.assertLessEqual(len(filter_observation(repeated_errors)), 6000)

    def test_pass_summary_keeps_counts_warnings_and_raw_result(self):
        output = 'test_example ... ok\n' * 100 + 'Warning: deprecated API\nRan 100 tests in 1.5s\nOK\n'
        result = {'ok': True, 'returncode': 0, 'timed_out': False, 'truncated': False, 'output': output}
        filtered = json.loads(filter_observation(result, action='run_tests'))
        self.assertIn('Ran 100 tests', filtered['output'])
        self.assertIn('deprecated', filtered['output'])
        self.assertEqual(result['output'], output)
        self.assertTrue(filtered['output_summarized'])
        self.assertLess(len(json.dumps(filtered)), len(json.dumps(result)))

    def test_arbitrary_commands_and_failed_tests_are_not_pass_summarized(self):
        result = {'ok': True, 'output': 'data line\nRan 1 test\nOK\n'}
        self.assertEqual(json.loads(filter_observation(result, action='run_command')), result)
        result['ok'] = False
        self.assertEqual(json.loads(filter_observation(result, action='run_tests')), result)

    def test_context_uses_action_name(self):
        context = ContextManager()
        result = {'ok': True, 'output': 'test_example ... ok\n' * 100 + 'Ran 100 tests\nOK\n'}
        context.add({'name': 'run_tests'}, result)
        self.assertIn('output_summarized', context.history[-1]['content'])

    def test_truncated_pass_logs_preserve_truncation(self):
        result = {'ok': True, 'truncated': True, 'output': 'data\nRan 1 test\nOK\n'}
        self.assertEqual(json.loads(filter_observation(result, action='run_tests')), result)

    def test_failure_anchor_is_bounded_without_changing_evidence(self):
        from types import SimpleNamespace
        state = SimpleNamespace(issue='fix', repo='/tmp/repo', plan=[], verification='NOT_RUN',
                                failures=[{'message': 'diagnostic' * 300, 'category': 'TOOL_FAILURE', 'repeated': 1}],
                                candidate_context_tokens=0, sent_context_tokens=0)
        adapter = SimpleNamespace(count_or_estimate_tokens=lambda value: len(json.dumps(value)) // 4)
        packed = ContextManager().pack(state, {}, [], adapter)
        anchor = json.loads(packed[1]['content'])
        self.assertEqual(len(anchor['recent_failures'][0]['message']), 400)
        self.assertEqual(len(state.failures[0]['message']), 3000)
        self.assertIn('Full failure evidence', anchor['recent_failures'][0]['details'])

    def test_compaction_reduces_context_and_preserves_navigation_and_latest(self):
        from types import SimpleNamespace
        from harness.demo import ScriptedAdapter
        context = ContextManager(budget=30000)
        for i in range(10):
            context.add({'name': 'read_file', 'arguments': {'path': f'file{i}.py'}},
                        {'ok': True, 'output': (f'line{i} contents\n' * 300)})
        original = list(context.history)
        state = SimpleNamespace(issue='fix', repo='/tmp/repo', plan=[], verification='NOT_RUN',
                                failures=[], candidate_context_tokens=0, sent_context_tokens=0)
        packed = context.pack(state, {}, [], ScriptedAdapter([]))
        self.assertLess(state.sent_context_tokens, state.candidate_context_tokens * .65)
        anchor = json.loads(packed[1]['content'])
        self.assertIn('file0.py', json.dumps(anchor['navigation_memory']))
        self.assertEqual(packed[-1], original[-1])
        self.assertEqual(context.history, original)

    def test_failed_test_summary_retains_assertions_and_counts(self):
        output = 'test_good (suite.T) ... ok\n' * 100 + (
            'FAIL: test_bad (suite.T)\nAssertionError: expected 3 got 1\n'
            'Ran 101 tests\nFAILED (failures=1)\n')
        result = {'ok': False, 'output': output}
        filtered = json.loads(filter_observation(result, action='run_tests'))
        self.assertNotIn('test_good', filtered['output'])
        self.assertIn('expected 3 got 1', filtered['output'])
        self.assertIn('FAILED (failures=1)', filtered['output'])
        self.assertEqual(result['output'], output)
