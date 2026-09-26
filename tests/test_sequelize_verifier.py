import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from benchmarks.verify_sequelize import verify


class SequelizeVerifierTests(unittest.TestCase):
    @patch('benchmarks.verify_sequelize.subprocess.run')
    def test_rebuild_failure_prevents_stale_test_success(self, run):
        run.return_value = Mock(returncode=1)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node = root / 'node'
            node.touch()
            self.assertEqual(verify(root, node), 1)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][-1], 'build')
