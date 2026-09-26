import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from benchmarks.run_inventory import LAB, prepare


class InventoryBenchmarkTests(unittest.TestCase):
    def test_reference_passes_visible_and_independent_acceptance(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests'],
                                cwd=LAB / 'repo', capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, '-B', str(LAB.parent / 'verify_inventory.py'),
                                 '--repo', str(LAB / 'repo')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('11/11', result.stdout)

    def test_broken_fresh_copy_has_distractors_without_reference(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            folder, target, _ = prepare(directory)
            self.assertEqual(len(list((target / 'legacy').glob('*.py'))), 12)
            self.assertFalse((target / 'bugs').exists())
            self.assertIn('FAILED (failures=3, errors=1)', (folder / 'baseline.log').read_text())

    @patch('benchmarks.run_inventory.run', return_value=0)
    def test_free_route_keeps_model_and_budget(self, run):
        from benchmarks.run_free import main
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'}, clear=True), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--synthetic-inventory', '--free-tier-confirmed']), 0)
        args = run.call_args.args[0]
        self.assertEqual(args[args.index('--budget') + 1], '60000')
