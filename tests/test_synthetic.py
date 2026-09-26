import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from benchmarks.run_synthetic import ISSUES, ROOT, TOTAL_TESTS, prepare
from benchmarks.run_free import main as free_main


class SyntheticTests(unittest.TestCase):
    def test_each_baseline_is_isolated_and_has_full_suite(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            for issue in ISSUES:
                with self.subTest(issue=issue):
                    folder, target, _ = prepare(issue, directory)
                    self.assertTrue((folder / 'manifest.json').exists())
                    self.assertEqual(len(list((target / 'tests').glob('test_*.py'))), 4)
                    self.assertFalse((target / 'bugs').exists())
                    self.assertFalse((target / 'issues').exists())

    def test_healthy_template_passes_all_checks(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                cwd=ROOT / 'benchmarks/synthetic_lab/repo', capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f'Ran {TOTAL_TESTS} tests', result.stderr)

    @patch('benchmarks.run_synthetic.run', return_value=0)
    @patch('benchmarks.run_free.run_benchmark')
    @patch('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'})
    def test_free_launcher_selects_one_synthetic_issue(self, fixture, synthetic):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(free_main(['--synthetic-issue', 'pagination', '--free-tier-confirmed']), 0)
        args = synthetic.call_args.args[0]
        self.assertEqual(args[:2], ['--issue', 'pagination'])
        self.assertIn('--free-tier-confirmed', args)
        self.assertEqual(args[args.index('--gemini-api-route') + 1], 'native')
        fixture.assert_not_called()
