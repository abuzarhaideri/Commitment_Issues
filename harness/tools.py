"""Repository tools with bounded output and a basic shell guard (not a sandbox)."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import sys
import subprocess
import tempfile

MAX_FILE_BYTES = 1024 * 1024
SKIP_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'target', 'dist'}


def repository_files(root, limit=5000):
    count = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(base) / d).is_symlink())
        for name in sorted(files):
            p = Path(base) / name
            if name == '.git' or p.is_symlink():
                continue
            yield p
            count += 1
            if count >= limit:
                return


def bounded_text(path):
    with path.open('rb') as source:
        data = source.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError('File exceeds 1 MB read limit')
    return data.decode(errors='replace')


def profile_repository(repo: Path) -> dict:
    repo = Path(repo)
    markers, commands = [], []
    for marker in ('pyproject.toml', 'pytest.ini', 'setup.cfg', 'requirements.txt', 'package.json', 'go.mod', 'Cargo.toml', 'Makefile', 'pom.xml', 'build.gradle', 'build.gradle.kts', 'gradlew'):
        if (repo / marker).is_file():
            markers.append(marker)
    files = list(repository_files(repo))
    tests = [p for p in files if p.name.startswith('test') and p.suffix == '.py']
    if any('unittest' in bounded_text(p) for p in tests if p.stat().st_size <= MAX_FILE_BYTES):
        commands.append(shlex.quote(sys.executable) + ' -m unittest discover -s tests -v' if (repo / 'tests').is_dir() else shlex.quote(sys.executable) + ' -m unittest discover -v')
    if 'pytest.ini' in markers or any('pytest' in bounded_text(repo / p) for p in markers if p in ('pyproject.toml', 'setup.cfg', 'requirements.txt')):
        commands.append(shlex.quote(sys.executable) + ' -m pytest')
    if 'package.json' in markers:
        try:
            scripts = json.loads(bounded_text(repo / 'package.json')).get('scripts', {})
            commands.extend('npm test' if key == 'test' else 'npm run ' + shlex.quote(key) for key in scripts if key == 'test' or key.startswith('test:'))
        except (ValueError, OSError, AttributeError):
            pass
    if 'go.mod' in markers:
        commands.append('go test ./...')
    if 'Cargo.toml' in markers:
        commands.append('cargo test')
    if 'Makefile' in markers and re.search(r'^test\s*:', bounded_text(repo / 'Makefile'), re.M):
        commands.append('make test')
    if 'pom.xml' in markers:
        commands.append('mvn test')
    if 'build.gradle' in markers or 'build.gradle.kts' in markers:
        commands.append('./gradlew test' if 'gradlew' in markers else 'gradle test')
    extensions = {}
    for p in files:
        ext = p.suffix or '(none)'
        extensions[ext] = extensions.get(ext, 0) + 1
    hints = [str(p.relative_to(repo)) for p in files if p.name.lower().startswith('readme') or '.github' in p.parts or p.name in ('.gitlab-ci.yml', 'Jenkinsfile', '.travis.yml', 'azure-pipelines.yml')]
    return {'markers': markers, 'test_commands': commands, 'extension_counts': extensions,
            'repo_map': [str(p.relative_to(repo)) for p in files[:100]], 'files_scanned': len(files),
            'map_truncated': len(files) > 100, 'scan_capped': len(files) >= 5000, 'hints': hints[:100]}


class ToolRegistry:
    SPECS = {
        'repo_overview': {}, 'list_dir': {'path': 'string'}, 'get_file_info': {'path': 'string'},
        'read_file': {'path': 'string', 'mode': 'string', 'start': 'integer', 'end': 'integer'},
        'search_code': {'query': 'string', 'path': 'string', 'scope': 'string'},
        'edit_file': {'path': 'string', 'old': 'string', 'new': 'string'},
        'run_command': {'command': 'string'}, 'run_tests': {'command': 'string'}, 'git_diff': {},
    }
    REQUIRED = {'get_file_info': ['path'], 'read_file': ['path'], 'search_code': ['query'], 'edit_file': ['path', 'old', 'new'], 'run_command': ['command'], 'run_tests': ['command']}

    DEFAULT_DENIED_PATTERN = r'\b(rm|sudo|printenv|env|curl|wget|nc|scp|ssh)\b|\bgit\s+(?:\S+\s+)*(reset|clean)\b|\b(set|export)\b|/dev/tcp|\$\{|\$\(|`'

    def __init__(self, repo: Path, timeout=30, max_output=12000, denied_pattern=None):
        self.repo = Path(repo).resolve()
        self.timeout = timeout
        self.max_output = max_output
        self.denied_pattern = self.DEFAULT_DENIED_PATTERN if denied_pattern is None else denied_pattern
        self.cache_hits = self.cache_misses = 0
        self.files_seen, self.files_modified = set(), set()
        self._cache = {}
        self._empty_searches = set()

    def schemas(self) -> list:
        return [{'type': 'function', 'function': {'name': name, 'description': name.replace('_', ' '), 'parameters': {'type': 'object', 'properties': {key: {'type': kind} for key, kind in params.items()}, 'required': self.REQUIRED.get(name, []), 'additionalProperties': False}}} for name, params in self.SPECS.items()]

    def execute(self, name, arguments) -> dict:
        try:
            if name not in self.SPECS:
                raise ValueError('Unknown tool: ' + str(name))
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            if not isinstance(arguments, dict):
                raise ValueError('Arguments must be an object')
            spec = self.SPECS[name]
            if set(arguments) - set(spec) or set(self.REQUIRED.get(name, [])) - set(arguments):
                raise ValueError('Unexpected or missing arguments')
            for key, value in arguments.items():
                expected = str if spec[key] == 'string' else int
                if type(value) is not expected:
                    raise ValueError('Invalid type for ' + key)
            result = getattr(self, '_' + name)(**arguments)
            if isinstance(result, str):
                result = {'ok': True, 'output': result}
            output = result['output']
            if len(output) > self.max_output:
                result['output'] = output[:self.max_output]
                result['truncated'] = True
            return result
        except Exception as exc:
            return {'ok': False, 'output': str(exc)[:self.max_output], 'error': type(exc).__name__}

    def _path(self, path='.'):
        original = self.repo / path
        if '.git' in original.parts:
            raise ValueError('.git access is prohibited')
        p = original.resolve()
        try:
            rel = p.relative_to(self.repo)
        except ValueError:
            raise ValueError('Path escapes repository')
        if '.git' in rel.parts:
            raise ValueError('.git access is prohibited')
        return p

    def _read(self, p):
        with p.open('rb') as source:
            data = source.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise ValueError('File exceeds 1 MB read limit')
        if b'\0' in data:
            raise ValueError('Binary file')
        key = str(p.relative_to(self.repo))
        self.files_seen.add(key)
        digest = hashlib.sha256(data).hexdigest()
        if key in self._cache and self._cache[key][0] == digest:
            self.cache_hits += 1
            return self._cache[key][1]
        self.cache_misses += 1
        content = data.decode('utf-8', errors='replace')
        self._cache[key] = digest, content
        return content

    def _repo_overview(self):
        return json.dumps({'profile': profile_repository(self.repo), 'entries': sorted(p.name for p in self.repo.iterdir() if p.name != '.git')}, indent=2)

    def _list_dir(self, path='.'):
        return '\n'.join(p.name + ('/' if p.is_dir() else '') for p in sorted(self._path(path).iterdir()) if p.name != '.git')

    def _get_file_info(self, path):
        p = self._path(path)
        return json.dumps({'path': str(p.relative_to(self.repo)), 'size': p.stat().st_size, 'is_dir': p.is_dir()})

    def _read_file(self, path, mode='range', start=1, end=None):
        lines = self._read(self._path(path)).splitlines()
        if mode == 'outline' or (mode == 'range' and start == 1 and end is None and len(lines) > 400):
            definitions = [f'{i}: {line[:180]}' for i, line in enumerate(lines, 1)
                           if re.match(r'\s*(class |(?:async )?def |function |export |func |type |#)', line)]
            if definitions:
                return ('DEFINITION MAP: request read_file with explicit start/end to inspect exact source.\n' +
                        '\n'.join(definitions))
            if mode == 'outline':
                return 'No recognized definitions; request an explicit line range.'
        if mode != 'range' or start < 1 or (end is not None and end < start):
            raise ValueError('Invalid range or mode')
        end = min(end if end is not None else start + 199, start + 199)
        return '\n'.join(f'{i}: {lines[i-1]}' for i in range(start, min(end, len(lines)) + 1))

    def _search_code(self, query, path='.', scope='auto'):
        if scope not in ('auto', 'all', 'source'):
            raise ValueError('Search scope must be auto, source, or all')
        p = self._path(path)
        if not query:
            raise ValueError('Query must not be empty')
        # Search production files first so test output cannot hide implementations.
        test_globs = ['!**/*_test.go', '!**/test_*.py', '!**/*_test.py',
                      '!**/*.test.*', '!**/*.spec.*', '!**/tests/**', '!**/test/**']
        source_only = scope != 'all' and p.is_dir()
        # Python traversal validates each symlink; rg does not follow symlinks.
        if shutil.which('rg'):
            result = self._process(['rg', '-n', '-H', '-F', '--max-filesize', '1M', *[item for glob in (test_globs if source_only else []) for item in ('--glob', glob)], *[item for directory in sorted(SKIP_DIRS) for item in ('--glob', '!' + directory + '/**')], '--', query, str(p.relative_to(self.repo))])
            if result.get('returncode') == 1:
                if scope == 'auto' and source_only:
                    # A guessed receiver can hide a method that exists on another type.
                    symbol = re.search(r'\b(?:func|def|function)\s+(?:\([^)]*\)\s*)?(\w+)', query)
                    if symbol:
                        relaxed = ' ' + symbol.group(1) + '('
                        fallback = self._search_code(relaxed, path, scope='source')
                        if not fallback['output'].startswith('No literal matches') and fallback.get('ok'):
                            fallback['output'] = ('No exact signature match; symbol fallback for ' +
                                                  repr(relaxed) + ':\n' + fallback['output'])
                            return fallback
                    return self._search_code(query, path, scope='all')
                result['ok'] = True
            lines = []
            for line in result['output'].splitlines():
                name, separator, remainder = line.partition(':')
                if separator:
                    try:
                        relative = str(self._path(name).relative_to(self.repo))
                        self.files_seen.add(relative)
                        line = relative + ':' + remainder
                    except ValueError:
                        continue
                lines.append(line)
            result['output'] = '\n'.join(lines)
            if result.get('ok') and not lines:
                result['output'] = self._empty_search_hint(query, path)
            return result
        matches = []
        files = [p] if p.is_file() else repository_files(p)
        files = sorted(files, key=lambda candidate: (self._is_test_path(candidate), str(candidate)))
        for candidate in files:
            try:
                if not candidate.is_file():
                    continue
                candidate = self._path(str(candidate))
                if source_only and self._is_test_path(candidate):
                    continue
                for i, line in enumerate(self._read(candidate).splitlines(), 1):
                    if query in line:
                        matches.append(f'{candidate.relative_to(self.repo)}:{i}:{line}')
                        if sum(map(len, matches)) >= self.max_output:
                            return '\n'.join(matches)
            except (OSError, ValueError):
                continue
        if not matches and scope == 'auto' and source_only:
            symbol = re.search(r'\b(?:func|def|function)\s+(?:\([^)]*\)\s*)?(\w+)', query)
            if symbol:
                relaxed = ' ' + symbol.group(1) + '('
                fallback = self._search_code(relaxed, path, scope='source')
                if isinstance(fallback, str):
                    fallback = {'ok': True, 'output': fallback}
                if not fallback['output'].startswith('No literal matches') and fallback.get('ok'):
                    fallback['output'] = ('No exact signature match; symbol fallback for ' +
                                          repr(relaxed) + ':\n' + fallback['output'])
                    return fallback
            return self._search_code(query, path, scope='all')
        return '\n'.join(matches) if matches else self._empty_search_hint(query, path)

    @staticmethod
    def _is_test_path(path):
        return (any(part in ('test', 'tests') for part in path.parts) or
                path.name.startswith('test_') or path.name.endswith(('_test.go', '_test.py')) or
                '.test.' in path.name or '.spec.' in path.name)

    def _empty_search_hint(self, query, path):
        repeated = (query, path) in self._empty_searches
        self._empty_searches.add((query, path))
        return ('No literal matches. ' + ('This same search already returned no matches. ' if repeated else '') +
                'Search a shorter symbol or error fragment; do not guess an exact signature or receiver type. '
                'Narrow the path after locating the implementation. An empty search is not a repository failure.')

    def _edit_file(self, path, old, new):
        if old == new:
            raise ValueError('No-op edit rejected: old and new are identical; no file changed')
        p = self._path(path)
        parts = p.relative_to(self.repo).parts
        if any(x.lower() in ('tests', 'test', 'eval', 'evaluation', 'evals', '.github', '.agents', '.codex') for x in parts) or p.name.startswith('test_') or p.name.endswith(('_test.py', '_test.go', '.test.js', '.spec.ts')):
            raise ValueError('Protected test or evaluation infrastructure')
        if not p.exists():
            if old:
                raise ValueError('Creation requires empty old text')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(new)
        else:
            if not old:
                raise ValueError('Empty old text only permitted for new files')
            content = self._read(p)
            matches = content.count(old)
            if matches != 1:
                first = next((line.strip() for line in old.splitlines() if line.strip()), '')
                locations = [i for i, line in enumerate(content.splitlines(), 1) if first and line.strip() == first]
                hint = f' near line {locations[0]}' if locations else ''
                raise ValueError(f'Old text must occur exactly once; found {matches}. No file changed. '
                                 f'Reread {path}{hint} with explicit start/end, then use a smaller exact unique block. '
                                 'Do not run verification as though this edit succeeded.')
            p.write_text(content.replace(old, new, 1))
        self.files_modified.add(str(p.relative_to(self.repo)))
        return 'File updated'

    def _guard(self, command):
        if not command.strip():
            raise ValueError('Empty command')
        if re.search(self.denied_pattern, command, re.I):
            raise ValueError('Command rejected by basic safety guard')

    def _process(self, command):
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR', 'SYSTEMROOT', 'PYTHONPATH')}
        with tempfile.TemporaryDirectory(prefix='harness-pycache-') as cache_dir, tempfile.TemporaryFile() as capture:
            env['PYTHONPYCACHEPREFIX'] = cache_dir
            proc = subprocess.Popen(command, cwd=self.repo, shell=isinstance(command, str), stdout=capture, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            timed_out = False
            try:
                proc.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            size = capture.seek(0, os.SEEK_END)
            capture.seek(0)
            head = capture.read(self.max_output * 4 + 1).decode(errors='replace')
            truncated = size > self.max_output or len(head) > self.max_output
            if truncated:
                marker = '\n... output truncated ...\n'
                budget = max(0, self.max_output - len(marker))
                capture.seek(max(0, size - self.max_output * 4))
                tail = capture.read(self.max_output * 4).decode(errors='replace')
                output = head[:budget // 2] + marker + tail[-(budget - budget // 2):]
                output = output[:self.max_output]
            else:
                output = head
            return {'ok': proc.returncode == 0 and not timed_out, 'output': output, 'returncode': proc.returncode, 'timed_out': timed_out, 'truncated': truncated}

    def _run_command(self, command):
        self._guard(command)
        return self._process(command)

    def _run_tests(self, command):
        return self._run_command(command)

    def _git_diff(self):
        tracked = self._process(['git', 'diff', 'HEAD', '--', '.', ':!.git'])
        listing = self._process(['git', 'ls-files', '--others', '--exclude-standard', '-z'])
        chunks = [tracked['output']]
        for name in listing['output'].split('\0'):
            if not name:
                continue
            try:
                content = self._read(self._path(name))
                chunks.append('--- /dev/null\n+++ b/' + name + '\n' + '\n'.join('+' + line for line in content.splitlines()))
            except (ValueError, OSError):
                continue
        return {'ok': tracked['ok'], 'output': '\n'.join(chunks)}
