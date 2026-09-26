"""Offline scripted recovery controls; these are not live model evaluations."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.demo import ScriptedAdapter
from harness.models import Action, ProtocolError
from harness.orchestrator import Orchestrator

FINISH = Action('finish', {'summary': 'Repair complete',
                          'semantic_review': 'Addition restored for positive, zero and negative operands; tests unchanged.'})


class MalformedOnce(ScriptedAdapter):
    def __init__(self, actions):
        super().__init__(actions)
        self.first = True

    def generate(self, messages, tools=None):
        if self.first:
            self.first = False
            error = ProtocolError('Invalid action JSON')
            error.input_tokens, error.output_tokens, error.usage_estimated = 100, 10, False
            raise error
        return super().generate(messages, tools)


def run(repeats=3):
    output = ROOT / 'artifacts/reliability' / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    records = []
    for repetition in range(repeats):
        for scenario in ('baseline', 'failed-patch', 'malformed-action'):
            with tempfile.TemporaryDirectory(prefix='harness-recovery-') as directory:
                repo = Path(directory)
                (repo / 'calc.py').write_text('def add(a, b):\n    return a - b\n')
                (repo / 'tests').mkdir()
                tests = repo / 'tests/test_calc.py'
                original = ('import unittest\nfrom calc import add\nclass T(unittest.TestCase):\n'
                            '    def test_positive(self): self.assertEqual(add(2, 3), 5)\n'
                            '    def test_negative(self): self.assertEqual(add(-2, -3), -5)\n'
                            '    def test_zero(self): self.assertEqual(add(0, 0), 0)\n')
                tests.write_text(original)
                command = f'{sys.executable} -B -m unittest discover -s tests -v'
                edit = Action('edit_file', {'path': 'calc.py', 'old': 'return a - b', 'new': 'return a + b'})
                test = Action('run_tests', {'command': command})
                if scenario == 'baseline':
                    adapter = ScriptedAdapter([test, edit, FINISH])
                elif scenario == 'failed-patch':
                    adapter = ScriptedAdapter([
                        Action('edit_file', {'path': 'calc.py', 'old': 'return a - b', 'new': 'return 1'}),
                        test, Action('edit_file', {'path': 'calc.py', 'old': 'return 1', 'new': 'return a + b'}), FINISH])
                else:
                    adapter = MalformedOnce([edit, FINISH])
                report = Orchestrator(repo, 'Fix addition', adapter,
                                      output / f'{scenario}-{repetition}', test_commands=[command]).run()
                expected_recovery = 0 if scenario == 'baseline' else 1
                passed = (report['status'] == 'RESOLVED' and report['verification'] == 'PASS' and
                          tests.read_text() == original and report['successful_recoveries'] == expected_recovery)
                records.append({'scenario': scenario, 'repetition': repetition + 1, 'passed': passed,
                                'status': report['status'], 'verified_recovery': report['successful_recoveries'],
                                'baseline_failures': len(report['baseline_failures']),
                                'evidence': report['artifacts']})
    summary = {'scope': 'Offline predetermined actions; validates mechanics, not model intelligence or live recovery',
               'repeats': repeats, 'passed': sum(r['passed'] for r in records), 'total': len(records), 'runs': records}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f"Offline recovery controls: {summary['passed']}/{summary['total']} passed. Evidence: {output / 'summary.json'}")
    return 0 if all(r['passed'] for r in records) else 1


if __name__ == '__main__':
    raise SystemExit(run())
