import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from benchmarks.run_recovery import EditConflictTools


class RecoveryBenchmarkTests(unittest.TestCase):
    def test_valid_edit_rejected_once_without_mutation_then_retry_works(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'app.py').write_text('return 1')
            tools = EditConflictTools(root)
            args = {'path': 'app.py', 'old': 'return 1', 'new': 'return 2'}
            first = tools.execute('edit_file', args)
            self.assertFalse(first['ok'])
            self.assertIn('CONTROLLED', first['output'])
            self.assertEqual((root / 'app.py').read_text(), 'return 1')
            self.assertTrue(tools.injected)
            self.assertTrue(tools.execute('edit_file', args)['ok'])
            self.assertEqual((root / 'app.py').read_text(), 'return 2')

    def test_invalid_or_protected_edit_does_not_consume_fault(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'test_app.py').write_text('protected')
            (root / 'app.py').write_text('source')
            tools = EditConflictTools(root)
            self.assertFalse(tools.execute('edit_file', {'path': 'test_app.py', 'old': 'protected', 'new': 'changed'})['ok'])
            self.assertFalse(tools.execute('edit_file', {'path': 'app.py', 'old': 'absent', 'new': 'changed'})['ok'])
            self.assertFalse(tools.injected)

    @patch('benchmarks.run_recovery.run', return_value=0)
    def test_free_route_preserves_limits(self, run):
        from benchmarks.run_free import main
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'}, clear=True), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--synthetic-recovery', '--free-tier-confirmed']), 0)
        args = run.call_args.args[0]
        self.assertEqual(args[args.index('--budget') + 1], '60000')
