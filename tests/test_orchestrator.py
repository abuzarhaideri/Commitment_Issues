from pathlib import Path
import json
import sys
import tempfile
import unittest
from harness.demo import ScriptedAdapter, run_demo
from harness.models import Action, ProtocolError
from harness.orchestrator import Orchestrator
from harness.main import main

FINISH = Action('finish', {'summary': 'Fixed', 'semantic_review': 'Operands are added, including negatives and zero; tests unchanged.'})

class HarnessTests(unittest.TestCase):
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
        command = f'''{sys.executable} -c "from pathlib import Path; Path('tests/test_calc.py').write_text('')"'''
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
        report = Orchestrator(self.repo, 'Fix', Broken([]), self.artifacts, token_budget=1).run()
        self.assertEqual(report['status'], 'BUDGET_EXHAUSTED')
        self.assertGreater(report['input_tokens'], 0)
        self.assertTrue(report['usage_estimated'])

    def test_offline_demo(self):
        report = run_demo(self.artifacts)
        self.assertEqual(report['status'], 'RESOLVED')
        self.assertEqual(report['model'], 'offline-scripted-fixture')

if __name__ == '__main__':
    unittest.main()
