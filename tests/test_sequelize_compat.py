import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from benchmarks.verify_sequelize_compat import verify_compat


class SequelizeCompatibilityTests(unittest.TestCase):
    @patch('benchmarks.verify_sequelize_compat.verify')
    def test_tampering_stops_before_build(self, verify):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'target'
            target.mkdir()
            (target / 'package.json').write_text('{}')
            (root / 'task-manifest.json').write_text(json.dumps({'protected_hashes': {'package.json': 'bad'}}))
            with self.assertRaisesRegex(ValueError, 'Protected file changed'):
                verify_compat(target, Path('/node'))
        verify.assert_not_called()

    @patch('benchmarks.verify_sequelize_compat.subprocess.run')
    @patch('benchmarks.verify_sequelize_compat.verify', return_value=1)
    def test_existing_failure_cannot_be_hidden_by_compatibility(self, verify, process):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'target'
            target.mkdir()
            (root / 'task-manifest.json').write_text(json.dumps({'protected_hashes': {}}))
            self.assertEqual(verify_compat(target, Path('/node')), 1)
        process.assert_not_called()

    @patch('benchmarks.run_sequelize_compat.run', return_value=0)
    def test_free_route_and_conflicts(self, run):
        from benchmarks.run_free import main
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'PLACEHOLDER'}, clear=True), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--sequelize-compat', '--free-tier-confirmed']), 0)
        args = run.call_args.args[0]
        self.assertEqual(args[args.index('--budget') + 1], '60000')
        with patch('benchmarks.run_free.getpass.getpass') as prompt, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(['--sequelize-compat', '--synthetic-inventory'])
        prompt.assert_not_called()
