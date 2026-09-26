import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks.run_fiber import ISSUE, run
from benchmarks.verify_fiber import summarize, verify


class FiberBenchmarkTests(unittest.TestCase):
    def test_go_counts_distinguish_parent_and_subtests(self):
        events = [{'Action': 'pass', 'Test': 'Test_A/one'},
                  {'Action': 'fail', 'Test': 'Test_A/two'},
                  {'Action': 'fail', 'Test': 'Test_A'},
                  {'Action': 'fail'}, {'Action': 'skip', 'Test': 'Test_B'}]
        counts = summarize([json.dumps(e) for e in events] + ['not JSON'])
        self.assertEqual(counts['fail'], 2)
        self.assertEqual(counts['top_level_fail'], 1)
        self.assertEqual(counts['packages_fail'], 1)
        self.assertEqual(counts['skip'], 1)

    @patch('benchmarks.run_fiber.harness_main', return_value=0)
    @patch('benchmarks.run_fiber.prepare', return_value=(Path('/tmp/run'), Path('/tmp/run/target')))
    def test_runner_passes_discovery_prompt_and_fixed_verification(self, prepare, main):
        self.assertEqual(run(['--model', 'explicit-model']), 0)
        args = main.call_args.args[0]
        self.assertTrue(args[args.index('--issue') + 1].startswith(ISSUE))
        self.assertIn('--scope regression', args[args.index('--issue') + 1])
        self.assertNotIn('MaxRanges', ISSUE)
        self.assertNotIn('req.go', ISSUE)
        self.assertEqual(args.count('--test-command'), 2)
        self.assertIn('--model', args)

    @patch('benchmarks.verify_fiber.subprocess.run')
    @patch('benchmarks.verify_fiber.go_environment', return_value=(Path('/tmp/go'), {}))
    def test_protected_tampering_stops_before_test_execution(self, environment, process):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / 'target'
            repo.mkdir()
            (repo / 'go.mod').write_text('module test')
            (root / 'task-manifest.json').write_text(json.dumps({'protected_hashes': {'go.mod': 'wrong-hash'}}))
            with self.assertRaisesRegex(ValueError, 'Protected prepared file changed'):
                verify(repo)
        process.assert_not_called()

    @patch('benchmarks.verify_fiber.subprocess.run')
    @patch('benchmarks.verify_fiber.go_environment', return_value=(Path('/tmp/go'), {}))
    def test_test_failure_does_not_run_vet(self, environment, process):
        def failing(command, **kwargs):
            kwargs['stdout'].write(json.dumps({'Action': 'fail', 'Test': 'Test_A'}) + '\n')
            return Mock(returncode=1)
        process.side_effect = failing
        with tempfile.TemporaryDirectory() as directory, patch('sys.stdout', new_callable=io.StringIO):
            root = Path(directory)
            repo = root / 'target'
            repo.mkdir()
            (repo / 'go.mod').write_text('module test')
            (root / 'task-manifest.json').write_text(json.dumps({'protected_hashes': {}}))
            with patch('benchmarks.verify_fiber.BASE', root):
                self.assertEqual(verify(repo), 1)
        self.assertEqual(process.call_count, 1)

    @patch('benchmarks.run_fiber.run', return_value=0)
    def test_free_launcher_routes_fiber_without_provider_change(self, run_fiber):
        from benchmarks.run_free import main
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'TEST_PLACEHOLDER'}, clear=True), patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(main(['--fiber', '--free-tier-confirmed']), 0)
        args = run_fiber.call_args.args[0]
        self.assertIn('gemini-compatible', args)
        self.assertIn('config/gemini-free.json', ' '.join(args))

    @patch('benchmarks.run_free.getpass.getpass')
    def test_mixed_benchmarks_rejected_before_key_prompt(self, getpass):
        from benchmarks.run_free import main
        with patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
            main(['--fiber', '--sequelize'])
        getpass.assert_not_called()

    @patch('benchmarks.run_fiber.harness_main', return_value=0)
    @patch('benchmarks.run_fiber.prepare', return_value=(Path('/tmp/run'), Path('/tmp/run/target')))
    def test_focused_prompt_preserves_verification_and_labels_mode(self, prepare, main):
        from benchmarks.run_fiber import FOCUSED_ISSUE
        self.assertEqual(run(['--focused', '--model', 'explicit-model']), 0)
        prepare.assert_called_once_with(FOCUSED_ISSUE, 'focused')
        args = main.call_args.args[0]
        issue = args[args.index('--issue') + 1]
        self.assertIn('MaxRanges=1', issue)
        self.assertIn('bytes=0-0,', issue)
        self.assertIn('--scope regression', issue)
        self.assertNotIn('req.go', issue)
        self.assertEqual(args.count('--test-command'), 2)
        self.assertIn('--scope all', args[args.index('--test-command') + 1])
        self.assertIn('--scope range-race', args[args.index('--test-command', args.index('--test-command') + 1) + 1])

    @patch('benchmarks.run_fiber.run', return_value=0)
    def test_focused_free_launcher_keeps_model_and_budget(self, run_fiber):
        from benchmarks.run_free import main
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'TEST_PLACEHOLDER'}, clear=True), patch('sys.stdout', new_callable=io.StringIO):
            self.assertEqual(main(['--fiber-focused', '--free-tier-confirmed']), 0)
        args = run_fiber.call_args.args[0]
        self.assertIn('--focused', args)
        self.assertEqual(args[args.index('--budget') + 1], '60000')
        self.assertEqual(args[args.index('--model') + 1], 'gemini-3.1-flash-lite')

    @patch('benchmarks.run_free.getpass.getpass')
    def test_focused_conflicts_rejected_before_key_prompt(self, getpass):
        from benchmarks.run_free import main
        for conflicting in ('--fiber', '--sequelize', '--probe'):
            with self.subTest(conflicting=conflicting), patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
                main(['--fiber-focused', conflicting])
        getpass.assert_not_called()
