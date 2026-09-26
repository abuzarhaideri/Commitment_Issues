import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class InventoryCleanupTests(unittest.TestCase):
    def check(self, repo):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'benchmarks/verify_inventory_cleanup.py'),
                               '--repo', str(repo)], capture_output=True, text=True)

    def test_healthy_reference_satisfies_helper_and_style(self):
        result = self.check(ROOT / 'benchmarks/inventory_lab/repo')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('7/7', result.stdout)

    def test_unguarded_script_rejected_and_main_guard_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'target'
            shutil.copytree(ROOT / 'benchmarks/inventory_lab/repo', target)
            script = target / 'reproduce_issue.py'
            script.write_text("print('side effect')\n")
            result = self.check(target)
            self.assertEqual(result.returncode, 1)
            self.assertIn('unguarded', result.stdout)
            script.write_text("if __name__ == '__main__':\n    print('demonstration')\n")
            self.assertEqual(self.check(target).returncode, 0)

    @patch('benchmarks.run_inventory_cleanup.run', return_value=0)
    def test_free_launcher_route(self, run):
        from benchmarks.run_free import main
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'}, clear=True), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--inventory-cleanup', '--free-tier-confirmed']), 0)
        args = run.call_args.args[0]
        self.assertEqual(args[args.index('--budget') + 1], '60000')
