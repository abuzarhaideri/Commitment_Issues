from pathlib import Path
import json
import sys
import shlex
import tempfile
import unittest
from harness.demo import ScriptedAdapter, run_demo
from harness.models import Action, ProtocolError
from harness.orchestrator import Orchestrator, protected, diff_snapshots
from harness.main import main

FINISH = Action('finish', {'summary': 'Fixed', 'semantic_review': 'Operands are added, including negatives and zero; tests unchanged.'})

class HarnessTests(unittest.TestCase):
    def reserve_events(self, report):
        return [event for line in (Path(report['artifacts']) / 'events.jsonl').read_text().splitlines()
                if (event := json.loads(line))['event'] == 'token_reserve_decision']

    def test_reserve_holds_normal_and_releases_for_finish_review(self):
        class Exact(ScriptedAdapter):
            max_output_tokens = 10000
            def count_or_estimate_tokens(self, value):
                return 1
            def estimate_request_tokens(self, messages, tools):
                return 100
        adapter = Exact([self.edit(), FINISH, FINISH])
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts, token_budget=5000,
                              token_reserve=1000, test_commands=[self.command]).run()
        events = self.reserve_events(report)
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(events[0]['held_reserve'], 1000)
        self.assertEqual(events[0]['output_limit'], 5000 - 1000 - 381)
        self.assertEqual(events[-1]['phase'], 'verification_review')
        self.assertEqual(events[-1]['held_reserve'], 0)
        for event in events:
            self.assertLessEqual(event['output_limit'] + event['estimated_input'] + event['held_reserve'], event['remaining'])
        self.assertEqual(adapter.max_output_tokens, 10000)
        self.assertLessEqual(report['input_tokens'] + report['output_tokens'], 5000)

    def test_protocol_recovery_spends_corrective_half_and_keeps_review_half(self):
        class BrokenOnce(ScriptedAdapter):
            max_output_tokens = 10000
            first = True
            def count_or_estimate_tokens(self, value):
                return 1
            def estimate_request_tokens(self, messages, tools):
                return 100
            def generate(self, messages, tools=None):
                if self.first:
                    self.first = False
                    error = ProtocolError('Invalid JSON')
                    error.input_tokens, error.output_tokens = 100, 3000
                    raise error
                return super().generate(messages, tools)
        report = Orchestrator(self.repo, 'Fix', BrokenOnce([self.edit(), FINISH, FINISH]),
                              self.artifacts, token_budget=5000, token_reserve=1000,
                              test_commands=[self.command]).run()
        events = self.reserve_events(report)
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(events[1]['phase'], 'protocol_recovery')
        self.assertEqual(events[1]['held_reserve'], 500)
        self.assertEqual(events[1]['output_limit'], 1900 - 500 - 381)
        self.assertEqual(events[-1]['held_reserve'], 0)
        self.assertLessEqual(report['input_tokens'] + report['output_tokens'], 5000)

    def test_small_budget_reserve_is_scaled_and_does_not_send_unaffordable_call(self):
        report = self.run_actions([], token_budget=1)
        self.assertEqual(report['token_reserve'], 0)
        self.assertEqual(report['llm_calls'], 0)
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')
        for reserve in (-1, 5001, True, 1.5):
            with self.assertRaises(ValueError):
                Orchestrator(self.repo, 'Fix', ScriptedAdapter([]), self.artifacts,
                             token_budget=5000, token_reserve=reserve)

    def test_explicit_reserve_that_cannot_fit_minimum_fails_without_call(self):
        class Exact(ScriptedAdapter):
            def count_or_estimate_tokens(self, value):
                return 0
            def estimate_request_tokens(self, messages, tools):
                return 100
            def generate(self, messages, tools=None):
                raise AssertionError('Reserved allowance cannot fit minimum response')
        report = Orchestrator(self.repo, 'Fix', Exact([]), self.artifacts,
                              token_budget=1000, token_reserve=900).run()
        self.assertEqual(report['llm_calls'], 0)
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')
        self.assertIn('phase reserve held', report['reason'])

    def test_unknown_adapter_remains_supported_with_unenforced_limit_telemetry(self):
        report = self.run_actions([Action('read_file', {'path': 'calc.py'})], max_steps=1)
        self.assertFalse(self.reserve_events(report)[0]['output_limit_enforced'])
        self.assertEqual(report['files_inspected'], ['calc.py'])

    def test_reserve_access_preserves_narrow_read_diagnosis(self):
        class Exact(ScriptedAdapter):
            max_output_tokens = 10000
            def count_or_estimate_tokens(self, value):
                return 1
            def estimate_request_tokens(self, messages, tools):
                return 100
        report = Orchestrator(self.repo, 'Fix', Exact([Action('read_file', {'path': 'calc.py'})]),
                              self.artifacts, token_budget=1500, token_reserve=1000, max_steps=1).run()
        event = self.reserve_events(report)[0]
        self.assertEqual(event['phase'], 'corrective')
        self.assertEqual(event['held_reserve'], 500)
        self.assertEqual(report['files_inspected'], ['calc.py'])

    def test_meaningful_edit_unlocks_request_to_finish_with_only_review_funds(self):
        class Exact(ScriptedAdapter):
            max_output_tokens = 10000
            calls = 0
            def count_or_estimate_tokens(self, value):
                return 1
            def estimate_request_tokens(self, messages, tools):
                return 100
            def generate(self, messages, tools=None):
                self.calls += 1
                response = super().generate(messages, tools)
                if self.calls == 1:
                    response.input_tokens, response.output_tokens = 381, self.max_output_tokens
                return response
        report = Orchestrator(self.repo, 'Fix', Exact([self.edit(), FINISH, FINISH]), self.artifacts,
                              token_budget=5000, token_reserve=1200, test_commands=[self.command]).run()
        events = self.reserve_events(report)
        self.assertEqual(events[1]['remaining'], 1200)
        self.assertEqual(events[1]['phase'], 'verification_review')
        self.assertEqual(events[1]['held_reserve'], 0)
        self.assertEqual(report['verification'], 'PASS')

    def test_noop_edit_does_not_unlock_review_reserve(self):
        class Exact(ScriptedAdapter):
            max_output_tokens = 10000
            def count_or_estimate_tokens(self, value):
                return 1
            def estimate_request_tokens(self, messages, tools):
                return 100
        report = Orchestrator(self.repo, 'Fix', Exact([self.edit('return a - b'),
                              Action('read_file', {'path': 'calc.py'})]), self.artifacts,
                              token_budget=5000, token_reserve=1000, max_steps=2).run()
        self.assertGreaterEqual(self.reserve_events(report)[1]['held_reserve'], 500)
        self.assertEqual(report['files_modified'], [])

    def test_truncated_protocol_recovers_small_edit_and_independent_pass(self):
        class Truncated(ScriptedAdapter):
            max_output_tokens = 8000
            calls = 0
            prompts = []
            def generate(self, messages, tools=None):
                self.calls += 1
                self.prompts.append(messages)
                if self.calls == 3:
                    error = ProtocolError('Invalid action JSON')
                    error.input_tokens, error.output_tokens = 120, 8000
                    error.usage_estimated = False
                    error.finish_reason = 'MAX_TOKENS'
                    raise error
                if self.calls == 4:
                    self.recovery_limit = self.max_output_tokens
                return super().generate(messages, tools)
        adapter = Truncated([Action('read_file', {'path': 'calc.py'}),
                             Action('record_findings', {'hypothesis': 'Subtracts operands',
                                    'evidence': 'calc.py:2', 'next_action': 'Replace minus with plus'}),
                             self.edit(), FINISH, FINISH])
        report = Orchestrator(self.repo, 'Fix addition', adapter, self.artifacts,
                              test_commands=[self.command]).run()
        self.assertEqual(report['verification'], 'PASS')
        self.assertEqual(report['successful_recoveries'], 1)
        self.assertEqual(report['files_modified'], ['calc.py'])
        self.assertEqual(adapter.recovery_limit, 8000)
        recovery = json.dumps(adapter.prompts[3])
        self.assertIn('return a - b', recovery)
        self.assertIn('Subtracts operands', recovery)
        self.assertIn('ONE small action', recovery)
        self.assertNotIn('ONE small action', json.dumps(adapter.prompts[4]))
        events = [json.loads(line) for line in (Path(report['artifacts']) / 'events.jsonl').read_text().splitlines()]
        failed = next(event for event in events if event['event'] == 'llm_call_failed')
        self.assertEqual((failed['input_tokens'], failed['output_tokens']), (120, 8000))
        self.assertFalse(failed['usage_estimated'])
        self.assertEqual(failed['details'], {'finish_reason': 'MAX_TOKENS'})
        self.assertTrue(any(event['event'] == 'test_run' and event['result']['ok'] for event in events))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        self.artifacts = Path(self.tmp.name) / 'artifacts'
        (self.repo / 'calc.py').write_text('def add(a, b):\n    return a - b\n')
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests/test_calc.py').write_text('import unittest\nfrom calc import add\nclass T(unittest.TestCase):\n    def test_add(self): self.assertEqual(add(2,3),5)\n')
        self.command = f'{sys.executable} -m unittest discover -s tests -v'

    def run_actions(self, actions, **kwargs):
        return Orchestrator(self.repo, 'Fix addition', ScriptedAdapter(actions), self.artifacts,
                            test_commands=[self.command], **kwargs).run()

    def edit(self, new='return a + b'):
        return Action('edit_file', {'path': 'calc.py', 'old': 'return a - b', 'new': new})

    def test_end_to_end_repair_and_evidence(self):
        report = self.run_actions([self.edit(), FINISH, FINISH])
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['files_modified'], ['calc.py'])
        self.assertEqual(report['verification'], 'PASS')
        self.assertTrue(report['usage_estimated'])
        output = Path(report['artifacts'])
        self.assertTrue((output / 'final.diff').read_text())
        events = [json.loads(l)['event'] for l in (output / 'events.jsonl').read_text().splitlines()]
        self.assertIn('test_run', events)
        self.assertEqual(events[-1], 'session_end')

    def test_done_does_not_bypass_failed_tests(self):
        report = self.run_actions([self.edit('return 1'), FINISH, FINISH], max_steps=4)
        self.assertNotEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['verification'], 'FAIL')
        self.assertTrue(report['failures'])

    def test_test_tampering_through_shell_is_detected(self):
        self.assertTrue(protected('middleware/cache/cache_test.go'))
        command = shlex.join([sys.executable, "-c", "from pathlib import Path; Path('tests/test_calc.py').write_text('weakened')"])
        report = self.run_actions([self.edit(), Action('run_command', {'command': command}), FINISH, FINISH], max_steps=4)
        self.assertNotEqual(report['status'], 'RESOLVED')
        self.assertIn('Protected', report['failures'][-1]['message'])

    def test_no_tests_unverified(self):
        (self.repo / 'tests/test_calc.py').unlink()
        report = Orchestrator(self.repo, 'Fix', ScriptedAdapter([self.edit(), FINISH, FINISH]), self.artifacts,
                              test_commands=[], max_steps=4).run()
        self.assertEqual(report['status'], 'UNVERIFIED')

    def test_zero_tests_cannot_pass(self):
        (self.repo / 'tests/test_calc.py').write_text('')
        report = self.run_actions([self.edit(), FINISH, FINISH], max_steps=4)
        self.assertNotEqual(report['status'], 'RESOLVED')

    def test_protocol_failure_recovers(self):
        class BrokenOnce(ScriptedAdapter):
            broken = False
            def generate(self, messages, tools=None):
                if not self.broken:
                    self.broken = True
                    raise ProtocolError('Invalid JSON')
                return super().generate(messages, tools)
        adapter = BrokenOnce([self.edit(), FINISH, FINISH])
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts, test_commands=[self.command]).run()
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['recoveries'], 1)

    def test_tiny_context_fails_cleanly(self):
        report = self.run_actions([], context_budget=1)
        self.assertEqual(report['status'], 'FAILED')
        self.assertIn('Context budget', report['reason'])

    def test_model_receives_explicit_verification_commands(self):
        class RecordingAdapter(ScriptedAdapter):
            def generate(self, messages, tools=None):
                self.first_messages = messages
                return super().generate(messages, tools)
        adapter = RecordingAdapter([Action('read_file', {'path': 'calc.py'})])
        command = 'python3 custom_verifier.py'
        Orchestrator(self.repo, 'Fix', adapter, self.artifacts,
                     test_commands=[command], max_steps=1).run()
        anchor = json.loads(adapter.first_messages[1]['content'])
        self.assertEqual(anchor['profile']['test_commands'], [command])
        self.assertEqual(anchor['profile']['test_command_source'], 'provided verification commands')

    def test_step_limit(self):
        report = self.run_actions([Action('read_file', {'path': 'calc.py'})], max_steps=1)
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')

    def test_custom_artifacts_inside_repo(self):
        report = Orchestrator(self.repo, 'Fix', ScriptedAdapter([self.edit(), FINISH, FINISH]),
                              self.repo / 'logs', test_commands=[self.command]).run()
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['files_modified'], ['calc.py'])

    def test_large_diff_delivered_in_complete_chunks(self):
        class Recorder(ScriptedAdapter):
            observations = []
            def generate(self, messages, tools=None):
                self.observations.append(messages[-1]['content'])
                return super().generate(messages, tools)
        body = '\n'.join('# unique-line-' + str(i) for i in range(400))
        adapter = Recorder([self.edit('return a + b\n' + body)] + [FINISH] * 10)
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts, test_commands=[self.command], max_steps=15).run()
        self.assertEqual(report['status'], 'RESOLVED')
        joined = ''.join(adapter.observations)
        for index in (0, 200, 399):
            self.assertIn('unique-line-' + str(index), joined)

    def test_failed_model_calls_charge_estimated_budget(self):
        class Broken(ScriptedAdapter):
            def generate(self, messages, tools=None):
                raise ProtocolError('Invalid JSON')
        report = Orchestrator(self.repo, 'Fix', Broken([]), self.artifacts, token_budget=4000).run()
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')
        self.assertGreater(report['input_tokens'], 0)
        self.assertTrue(report['usage_estimated'])

    def test_offline_demo(self):
        report = run_demo(self.artifacts)
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['model'], 'offline-scripted-fixture')

    def test_budget_guard_does_not_send_unaffordable_request(self):
        class NeverCalled(ScriptedAdapter):
            def generate(self, messages, tools=None):
                self.fail_if_called = True
                raise AssertionError('Unaffordable request sent')
        adapter = NeverCalled([])
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts, token_budget=1).run()
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')
        self.assertEqual(report['llm_calls'], 0)
        self.assertEqual(report['input_tokens'], 0)

    def test_budget_guard_accounts_for_adapter_request_overhead(self):
        class SchemaHeavy(ScriptedAdapter):
            def estimate_request_tokens(self, messages, tools):
                return 10000
            def generate(self, messages, tools=None):
                raise AssertionError('Request schema exceeds remaining allowance')
        report = Orchestrator(self.repo, 'Fix', SchemaHeavy([]), self.artifacts,
                              token_budget=5000).run()
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')
        self.assertEqual(report['llm_calls'], 0)

    def test_output_allowance_is_bounded_and_restored(self):
        class Recorder(ScriptedAdapter):
            max_output_tokens = 10000
            def generate(self, messages, tools=None):
                self.observed_limit = self.max_output_tokens
                return super().generate(messages, tools)
        adapter = Recorder([self.edit()])
        Orchestrator(self.repo, 'Fix', adapter, self.artifacts, token_budget=5000, max_steps=1).run()
        self.assertLess(adapter.observed_limit, 5000)
        self.assertEqual(adapter.max_output_tokens, 10000)

    def test_broken_baseline_not_counted_as_patch_recovery(self):
        report = self.run_actions([Action('run_tests', {'command': self.command}), self.edit(), FINISH, FINISH])
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(len(report['baseline_failures']), 1)
        self.assertEqual(report['recoveries'], 0)
        self.assertEqual(report['successful_recoveries'], 0)

    def test_failed_patch_corrected_and_independently_verified(self):
        report = self.run_actions([self.edit('return 1'),
                                  Action('run_tests', {'command': self.command}),
                                  Action('edit_file', {'path': 'calc.py', 'old': 'return 1', 'new': 'return a + b'}),
                                  FINISH, FINISH])
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['successful_recoveries'], 1)
        self.assertEqual(report['recoveries'], 1)
        self.assertEqual(report['baseline_failures'], [])

    def test_successful_read_does_not_claim_recovery(self):
        class BrokenOnce(ScriptedAdapter):
            first = True
            def generate(self, messages, tools=None):
                if self.first:
                    self.first = False
                    raise ProtocolError('Invalid action JSON')
                self.recovery_prompt = messages
                return super().generate(messages, tools)
        adapter = BrokenOnce([Action('read_file', {'path': 'calc.py'})])
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts, max_steps=2).run()
        self.assertEqual(report['successful_recoveries'], 0)
        self.assertIn('Escape quotes/newlines', json.dumps(adapter.recovery_prompt))

    def test_findings_retained_for_next_request(self):
        class Recorder(ScriptedAdapter):
            def generate(self, messages, tools=None):
                self.messages = messages
                return super().generate(messages, tools)
        note = {'hypothesis': 'Operands are subtracted', 'evidence': 'calc.py:2', 'next_action': 'Replace operator'}
        adapter = Recorder([Action('record_findings', note), Action('read_file', {'path': 'calc.py'})])
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts, max_steps=2).run()
        self.assertEqual(report['findings'], [note])
        self.assertEqual(json.loads(adapter.messages[1]['content'])['model_findings'], [note])

    def test_findings_are_bounded_and_validate_fields(self):
        actions = [Action('record_findings', {'hypothesis': str(i), 'evidence': 'calc.py:2', 'next_action': 'inspect'}) for i in range(6)]
        report = self.run_actions(actions, max_steps=6)
        self.assertEqual(len(report['findings']), 4)
        self.assertEqual(report['findings'][0]['hypothesis'], '2')

    def test_invalid_findings_are_not_saved(self):
        report = self.run_actions([Action('record_findings', {'hypothesis': 'x' * 501, 'evidence': 'file', 'next_action': 'inspect'})], max_steps=1)
        self.assertEqual(report['findings'], [])
        self.assertEqual(report['recoveries'], 1)

    def test_build_changes_need_review_without_repeating_verified_commands(self):
        class BuildRecorder(ScriptedAdapter):
            pass
        command = shlex.join([sys.executable, "-c", "from pathlib import Path; Path('built.js').write_text('built')"])
        adapter = BuildRecorder([self.edit()] + [FINISH] * 8)
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts,
                              test_commands=[self.command, command], max_steps=10).run()
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(len(report['tests']), 2)
        self.assertEqual(report['recoveries'], 0)
        self.assertIn('built.js', report['files_modified'])

    def test_build_protected_changes_still_fail(self):
        command = shlex.join([sys.executable, "-c", "from pathlib import Path; Path('tests/test_calc.py').write_text('weakened')"])
        report = Orchestrator(self.repo, 'Fix', ScriptedAdapter([self.edit()] + [FINISH] * 5),
                              self.artifacts, test_commands=[command], max_steps=7).run()
        self.assertNotEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['verification'], 'FAIL')

    def test_post_build_pending_review_is_reported_honestly(self):
        command = shlex.join([sys.executable, "-c", "from pathlib import Path; Path('built.js').write_text('built')"])
        report = Orchestrator(self.repo, 'Fix', ScriptedAdapter([self.edit(), FINISH, FINISH]),
                              self.artifacts, test_commands=[self.command, command], max_steps=3).run()
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')
        self.assertEqual(report['verification'], 'PASS_PENDING_REVIEW')

    def test_verification_cache_invalidated_by_new_source_edit(self):
        command = shlex.join([sys.executable, "-c", "from pathlib import Path; Path('built.js').write_text('built')"])
        extra = Action('edit_file', {'path': 'calc.py', 'old': 'return a + b', 'new': 'return a + b # reviewed'})
        adapter = ScriptedAdapter([self.edit(), FINISH, FINISH, extra, FINISH, FINISH])
        report = Orchestrator(self.repo, 'Fix', adapter, self.artifacts,
                              test_commands=[self.command, command], max_steps=8).run()
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(len(report['tests']), 4)

    def test_no_final_newline_has_marker_and_separate_file_headers(self):
        _, diff = diff_snapshots({'a.py': b'one\n', 'b.py': b'old\n'},
                                 {'a.py': b'two', 'b.py': b'new\n'})
        self.assertIn('+two\n\\ No newline at end of file\n--- a/b.py\n', diff)
        self.assertNotIn('two---', diff)

if __name__ == '__main__':
    unittest.main()
