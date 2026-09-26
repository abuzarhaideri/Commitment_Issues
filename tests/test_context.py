import json
import unittest
from harness.context import ContextManager, filter_observation


class ObservationTests(unittest.TestCase):
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
