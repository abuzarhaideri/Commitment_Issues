"""Offline infrastructure smoke test; does not measure model repair ability."""
from pathlib import Path
import sys
import tempfile
from .models import Action, ModelAdapter, ModelResponse
from .orchestrator import Orchestrator

class ScriptedAdapter(ModelAdapter):
    model = 'offline-scripted-fixture'
    def __init__(self, actions):
        self.actions = iter(actions)
    def generate(self, messages, tools=None):
        action = next(self.actions, Action('finish', {'summary': 'Fixed addition', 'semantic_review': 'Addition now adds operands; negative and zero values work, tests remain unchanged.'}))
        return ModelResponse([action], input_tokens=self.count_or_estimate_tokens(messages) + self.count_or_estimate_tokens(tools), output_tokens=40)

def run_demo(artifacts=Path('artifacts')):
    with tempfile.TemporaryDirectory(prefix='commitment-issues-demo-') as directory:
        repo = Path(directory)
        (repo / 'calc.py').write_text('def add(a, b):\n    return a - b\n')
        (repo / 'tests').mkdir()
        (repo / 'tests/test_calc.py').write_text('import unittest\nfrom calc import add\nclass AdditionTests(unittest.TestCase):\n    def test_positive(self): self.assertEqual(add(2, 3), 5)\n    def test_negative(self): self.assertEqual(add(-2, -3), -5)\n    def test_zero(self): self.assertEqual(add(0, 3), 3)\n')
        actions = [Action('update_plan', {'steps': ['Inspect the implementation', 'Replace subtraction with addition', 'Run regression tests and review diff']}),
                   Action('read_file', {'path': 'calc.py'}),
                   Action('run_tests', {'command': f'{sys.executable} -m unittest discover -s tests -v'}),
                   Action('edit_file', {'path': 'calc.py', 'old': 'return a - b', 'new': 'return a + b'}),
                   Action('run_tests', {'command': f'{sys.executable} -m unittest discover -s tests -v'})]
        return Orchestrator(repo, 'Fix add: it subtracts operands instead of adding', ScriptedAdapter(actions), artifacts,
                            test_commands=[f'{sys.executable} -m unittest discover -s tests -v'], max_steps=12).run()
