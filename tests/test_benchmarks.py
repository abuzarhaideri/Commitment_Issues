"""Benchmark selection must validate its baseline before calling a model."""
import contextlib
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import run_live


class BenchmarkTests(unittest.TestCase):
    def test_each_fixture_baseline_and_forwarded_issue(self):
        source = run_live.ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for fixture in run_live.FIXTURES:
                shutil.copytree(source / 'benchmarks' / fixture, root / 'benchmarks' / fixture)
            with patch.object(run_live, 'ROOT', root), patch.object(run_live, 'main', return_value=0) as main:
                for fixture in run_live.FIXTURES:
                    with self.subTest(fixture=fixture), contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(run_live.run(['--fixture', fixture, '--model', 'TEST_MODEL']), 0)
                        arguments = main.call_args.args[0]
                        self.assertNotIn('--fixture', arguments)
                        self.assertEqual(arguments[arguments.index('--model') + 1], 'TEST_MODEL')
                        target = Path(arguments[arguments.index('--repo') + 1])
                        self.assertEqual(arguments[arguments.index('--issue') + 1], (target / 'ISSUE.md').read_text())
                        self.assertTrue((target.parent / 'baseline.log').exists())

    def test_invalid_fixture_stops_before_model(self):
        with patch.object(run_live, 'main') as main, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                run_live.run(['--fixture', '../../arbitrary'])
            main.assert_not_called()
