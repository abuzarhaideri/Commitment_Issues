import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from benchmarks.run_free import run_series


class RepeatTests(unittest.TestCase):
    def exercise(self, statuses, estimates=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        evidence = root / 'runs'
        count = 0
        def run(args, options):
            nonlocal count
            status = statuses[count]
            path = evidence / str(count) / 'evidence/run/performance.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'status': status, 'verification': 'PASS' if status == 'RESOLVED' else 'NOT_RUN',
                                        'input_tokens': 100 + count, 'output_tokens': 20,
                                        'usage_estimated': estimates[count] if estimates else False}))
            count += 1
            return 0 if status == 'RESOLVED' else 1
        with patch('benchmarks.run_free.ROOT', root), patch('benchmarks.run_free.evidence_root', return_value=evidence), patch('benchmarks.run_free.run_selected', side_effect=run), contextlib.redirect_stdout(io.StringIO()):
            code = run_series(SimpleNamespace(repeat=3), ['--budget', '60000'])
        summary = json.loads(next((root / 'artifacts/comparisons').glob('*/summary.json')).read_text())
        return code, summary

    def test_failed_trials_retained_and_estimates_excluded_from_provider_median(self):
        code, summary = self.exercise(['RESOLVED', 'BUDGET_EXHAUSTED', 'RESOLVED'], [False, True, False])
        self.assertEqual(code, 1)
        self.assertEqual(summary['resolved'], 2)
        self.assertEqual(summary['completed'], 3)
        self.assertEqual(summary['provider_only_samples'], 2)
        self.assertEqual(summary['provider_only_token_median'], 121)
        self.assertEqual(summary['attempts'][1]['status'], 'BUDGET_EXHAUSTED')

    def test_quota_stops_remaining_trials(self):
        code, summary = self.exercise(['QUOTA_EXHAUSTED'])
        self.assertEqual(code, 1)
        self.assertEqual(summary['requested'], 3)
        self.assertEqual(summary['completed'], 1)

    def test_diagnostic_repeat_rejected_before_key_prompt(self):
        from benchmarks.run_free import main
        with patch('benchmarks.run_free.getpass.getpass') as prompt, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(['--probe', '--repeat', '3'])
        prompt.assert_not_called()
