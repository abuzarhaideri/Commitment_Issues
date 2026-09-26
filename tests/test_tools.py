import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness.tools import ToolRegistry, profile_repository


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / 'repo'
        self.repo.mkdir()
        self.tools = ToolRegistry(self.repo, timeout=.15, max_output=2000)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, name, **args):
        return self.tools.execute(name, args)

    def test_paths_and_symlinks(self):
        outside = Path(self.temp.name) / 'secret'
        outside.write_text('secret')
        (self.repo / 'link').symlink_to(outside)
        for path in ('../secret', str(outside), 'link', '.git/config'):
            self.assertFalse(self.call('read_file', path=path)['ok'])

    def test_edit_requires_unique_match_and_protects_tests(self):
        target = self.repo / 'app.py'
        target.write_text('one one')
        self.assertFalse(self.call('edit_file', path='app.py', old='one', new='two')['ok'])
        self.assertEqual(target.read_text(), 'one one')
        self.assertTrue(self.call('edit_file', path='app.py', old='one one', new='two')['ok'])
        self.assertFalse(self.call('edit_file', path='app.py', old='', new='bad')['ok'])
        self.assertTrue(self.call('edit_file', path='new.py', old='', new='created')['ok'])
        self.assertFalse(self.call('edit_file', path='tests/test_a.py', old='', new='bad')['ok'])
        self.assertFalse(self.call('edit_file', path='ctx_test.go', old='', new='bad')['ok'])
        self.assertEqual(self.tools.files_modified, {'app.py', 'new.py'})

    def test_cache_invalidates_on_content_change(self):
        p = self.repo / 'app.py'
        p.write_text('alpha')
        self.call('read_file', path='app.py')
        self.call('read_file', path='app.py')
        self.assertEqual((self.tools.cache_hits, self.tools.cache_misses), (1, 1))
        p.write_text('bravo')
        self.assertIn('bravo', self.call('read_file', path='app.py')['output'])
        self.assertEqual(self.tools.cache_misses, 2)
        self.assertEqual(self.tools.files_seen, {'app.py'})

    def test_timeout_and_output_bound(self):
        result = self.call('run_command', command="python3 -c 'import time; print(123, flush=True); time.sleep(10)'")
        self.assertFalse(result['ok'])
        self.assertTrue(result['timed_out'])
        self.assertIn('123', result['output'])
        result = self.call('run_command', command="python3 -c 'print(\"x\" * 5000)'")
        self.assertLessEqual(len(result['output']), 2000)
        self.assertTrue(result['truncated'])

    def test_search_fallback_literal_and_containment(self):
        (self.repo / 'app.py').write_text('a.b\naxb\n')
        outside = Path(self.temp.name) / 'outside'
        outside.write_text('a.b')
        (self.repo / 'link').symlink_to(outside)
        with patch('harness.tools.shutil.which', return_value=None):
            result = self.call('search_code', query='a.b')
        self.assertTrue(result['ok'])
        self.assertEqual(result['output'], 'app.py:1:a.b')

    def test_invalid_arguments_and_shell_guard(self):
        for name, arguments in [('bad', {}), ('read_file', {}), ('read_file', {'path': 1}), ('repo_overview', {'extra': True})]:
            self.assertFalse(self.tools.execute(name, arguments)['ok'])
        for command in ('rm -rf .', 'git reset --hard', 'sudo true', 'printenv', 'curl https://example.com'):
            self.assertFalse(self.call('run_command', command=command)['ok'])

    def test_profile_does_not_invent_empty_test_suite(self):
        self.assertEqual(profile_repository(self.repo)['test_commands'], [])
        (self.repo / 'tests').mkdir()
        (self.repo / 'tests/test_a.py').write_text('import unittest\n')
        self.assertTrue(any(command.endswith(' -m unittest discover -s tests -v') for command in profile_repository(self.repo)['test_commands']))

    def test_git_alias_and_oversized_reads(self):
        (self.repo / 'public').mkdir()
        (self.repo / 'public/data').write_text('data')
        (self.repo / '.git').symlink_to(self.repo / 'public', target_is_directory=True)
        self.assertFalse(self.call('read_file', path='.git/data')['ok'])
        (self.repo / 'large').write_bytes(b'x' * (1024 * 1024 + 1))
        self.assertFalse(self.call('read_file', path='large')['ok'])

    def test_infrastructure_patterns_allow_harness(self):
        self.assertTrue(self.call('edit_file', path='harness/app.py', old='', new='code')['ok'])
        for path in ('eval/a.py', '.github/workflows/check.yml', 'unit_test.py', 'app.test.js', 'app.spec.ts'):
            self.assertFalse(self.call('edit_file', path=path, old='', new='code')['ok'])

    def test_fallback_skips_generated_directories(self):
        for directory in ('node_modules', '.venv', 'target', 'dist', '__pycache__'):
            (self.repo / directory).mkdir()
            (self.repo / directory / 'a.py').write_text('needle')
        (self.repo / 'app.py').write_text('needle')
        with patch('harness.tools.shutil.which', return_value=None):
            self.assertEqual(self.call('search_code', query='needle')['output'], 'app.py:1:needle')

    def test_logs_preserve_tail_failure(self):
        result = self.call('run_tests', command="python3 -c 'print(\"START\"); print(\"x\" * 5000); print(\"FINAL FAILURE\"); raise SystemExit(1)'")
        self.assertFalse(result['ok'])
        self.assertTrue(result['truncated'])
        self.assertIn('START', result['output'])
        self.assertIn('FINAL FAILURE', result['output'])

    def test_command_import_is_fresh_after_equal_size_edit(self):
        import os
        import shlex
        import sys
        module = self.repo / 'fresh_module.py'
        module.write_text('VALUE = 1\n')
        stamp = module.stat().st_mtime_ns
        command = shlex.quote(sys.executable) + " -c 'import fresh_module; print(fresh_module.VALUE)'"
        registry = ToolRegistry(self.repo, timeout=5)
        baseline = registry.execute('run_command', {'command': command})
        self.assertTrue(baseline['ok'])
        self.assertEqual(baseline['output'].strip(), '1')
        edit = registry.execute('edit_file', {'path': 'fresh_module.py', 'old': '1', 'new': '2'})
        self.assertTrue(edit['ok'])
        os.utime(module, ns=(stamp, stamp))
        updated = registry.execute('run_command', {'command': command})
        self.assertTrue(updated['ok'])
        self.assertEqual(updated['output'].strip(), '2')
        self.assertFalse((self.repo / '__pycache__').exists())

    def test_rg_records_relative_paths(self):
        import shutil
        if not shutil.which('rg'):
            self.skipTest('rg is unavailable')
        (self.repo / 'app.py').write_text('literal.a')
        result = self.call('search_code', query='literal.a')
        self.assertEqual(result['output'], 'app.py:1:literal.a')
        self.assertIn('app.py', self.tools.files_seen)

    def test_java_and_repository_hints(self):
        for name in ('pom.xml', 'build.gradle', 'gradlew', 'README.md'):
            (self.repo / name).write_text('')
        (self.repo / '.github/workflows').mkdir(parents=True)
        (self.repo / '.github/workflows/test.yml').write_text('run: danger')
        profile = profile_repository(self.repo)
        self.assertIn('mvn test', profile['test_commands'])
        self.assertIn('./gradlew test', profile['test_commands'])
        self.assertEqual(profile['extension_counts']['.yml'], 1)
        self.assertIn('.github/workflows/test.yml', profile['hints'])
        self.assertIn('README.md', profile['repo_map'])

    def test_empty_search_guides_alternate_literal_query(self):
        for available in (None, 'rg'):
            with self.subTest(available=available), patch('harness.tools.shutil.which', return_value=available):
                if available:
                    with patch.object(self.tools, '_process', side_effect=lambda *args: {'ok': False, 'output': '', 'returncode': 1}):
                        first = self.call('search_code', query='missing_' + str(available))
                        second = self.call('search_code', query='missing_' + str(available))
                else:
                    first = self.call('search_code', query='missing')
                    second = self.call('search_code', query='missing')
                self.assertTrue(first['ok'])
                self.assertIn('No literal matches', first['output'])
                self.assertIn('same search already', second['output'])
                self.assertIn('shorter symbol', second['output'])

    def test_source_search_not_hidden_by_test_volume(self):
        import shutil
        (self.repo / 'a_test.go').write_text('Range( test call\n' * 1000)
        (self.repo / 'req.go').write_text('func (c *DefaultReq) Range(size int) {}\n')
        for use_rg in (False, True):
            if use_rg and not shutil.which('rg'):
                continue
            with self.subTest(use_rg=use_rg):
                if use_rg:
                    result = self.call('search_code', query='Range(')
                else:
                    with patch('harness.tools.shutil.which', return_value=None):
                        result = self.call('search_code', query='Range(')
                self.assertIn('req.go:1:', result['output'])
                self.assertNotIn('a_test.go', result['output'])
        self.assertIn('a_test.go', self.call('search_code', query='test call')['output'])
        self.assertIn('a_test.go', self.call('search_code', query='Range(', scope='all')['output'])
        self.assertFalse(self.call('search_code', query='Range(', scope='invalid')['ok'])

    def test_guessed_receiver_falls_back_to_symbol_with_location(self):
        import shutil
        (self.repo / 'req.go').write_text('func (r *DefaultReq) Range(size int64) {}\n')
        for use_rg in (False, True):
            if use_rg and not shutil.which('rg'):
                continue
            with self.subTest(use_rg=use_rg):
                if use_rg:
                    result = self.call('search_code', query='func (c *Ctx) Range')
                else:
                    with patch('harness.tools.shutil.which', return_value=None):
                        result = self.call('search_code', query='func (c *Ctx) Range')
                self.assertIn('symbol fallback', result['output'])
                self.assertIn('req.go:1:', result['output'])

    def test_large_default_read_maps_definitions_explicit_range_is_exact(self):
        (self.repo / 'req.go').write_text('package p\n' + '\n' * 500 +
                                       'func (r *Req) Range(size int) {}\n')
        result = self.call('read_file', path='req.go')
        self.assertIn('DEFINITION MAP', result['output'])
        self.assertIn('502: func', result['output'])
        explicit = self.call('read_file', path='req.go', start=502, end=502)
        self.assertEqual(explicit['output'], '502: func (r *Req) Range(size int) {}')

    def test_noop_edit_rejected_without_modified_file(self):
        (self.repo / 'app.py').write_text('return 1')
        result = self.call('edit_file', path='app.py', old='return 1', new='return 1')
        self.assertFalse(result['ok'])
        self.assertIn('No-op', result['output'])
        self.assertEqual(self.tools.files_modified, set())
        self.assertEqual((self.repo / 'app.py').read_text(), 'return 1')

    def test_failed_exact_edit_gives_location_without_fuzzy_mutation(self):
        (self.repo / 'app.py').write_text('def f():\n    return 1\n')
        result = self.call('edit_file', path='app.py', old='def f():\n    return 2', new='def f():\n    return 3')
        self.assertFalse(result['ok'])
        self.assertIn('found 0', result['output'])
        self.assertIn('near line 1', result['output'])
        self.assertIn('No file changed', result['output'])
        self.assertEqual((self.repo / 'app.py').read_text(), 'def f():\n    return 1\n')
