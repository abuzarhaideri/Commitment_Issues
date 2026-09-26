"""Clean-clone startup and repair rehearsal using a local simulated HTTP model."""
import hashlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import threading
import zipfile
import uuid
from submission import ROOT, package


def rehearse():
    base = ROOT / 'artifacts/submission'
    output = base / 'rehearsals' / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    archive = package(base)
    record = {'scope': 'Local clean clone; simulated HTTP model, not live organiser/model validation', 'commands': []}
    env = {k: v for k, v in os.environ.items() if not k.startswith(('HARNESS_', 'AI_', 'GEMINI_', 'OPENAI_', 'GIT_'))}
    env.update(AI_API_KEY='REHEARSAL_PLACEHOLDER', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)

    def command(args, cwd, input_text=None):
        result = subprocess.run(args, cwd=cwd, env=env, input=input_text,
                                capture_output=True, text=True, timeout=120)
        record['commands'].append({'command': args, 'exit': result.returncode,
                                   'output': (result.stdout + result.stderr)[-14000:]})
        if result.returncode:
            raise RuntimeError(f'Rehearsal command failed: {args}; see rehearsal.json')
        return result

    try:
        with tempfile.TemporaryDirectory(prefix='harness-clean-clone-') as directory:
            temp = Path(directory)
            origin = temp / 'origin'
            origin.mkdir()
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(origin)
            command(['git', 'init', '-q'], origin)
            command(['git', 'add', '.'], origin)
            command(['git', '-c', 'user.name=Local Rehearsal', '-c', 'user.email=rehearsal@example.invalid',
                     'commit', '-qm', 'Temporary submission rehearsal'], origin)
            clone = temp / 'clone'
            command(['git', 'clone', '-q', str(origin), str(clone)], temp)
            command(['make', 'setup'], clone)
            command(['make', 'test'], clone)
            launch = command(['make', 'run', 'ARGS=--launch-check'], clone)
            if 'HARNESS READY' not in launch.stdout:
                raise RuntimeError('Startup did not emit readiness')
            target = temp / 'target'
            target.mkdir()
            (target / 'calc.py').write_text('def add(a, b):\n    return a - b\n')
            (target / 'tests').mkdir()
            tests = target / 'tests/test_calc.py'
            tests.write_text('import unittest\nfrom calc import add\nclass T(unittest.TestCase):\n'
                             '    def test_positive(self): self.assertEqual(add(2,3),5)\n'
                             '    def test_negative(self): self.assertEqual(add(-2,-3),-5)\n'
                             '    def test_zero(self): self.assertEqual(add(0,3),3)\n')
            original_hash = hashlib.sha256(tests.read_bytes()).hexdigest()

            class Handler(BaseHTTPRequestHandler):
                requests = 0

                def log_message(self, *args):
                    pass

                def do_POST(self):
                    self.rfile.read(int(self.headers['Content-Length']))
                    type(self).requests += 1
                    if self.requests == 1:
                        action = {'action': 'read_file', 'arguments': {'path': 'calc.py'}}
                    elif self.requests == 2:
                        action = {'action': 'edit_file', 'arguments': {
                            'path': 'calc.py', 'old': 'return a - b', 'new': 'return a + b'}}
                    else:
                        action = {'action': 'finish', 'arguments': {'summary': 'Fixed addition',
                            'semantic_review': 'Addition corrected; positive, negative and zero regression tests unchanged.'}}
                    body = json.dumps({'choices': [{'message': {'content': json.dumps(action)}}],
                                       'usage': {'prompt_tokens': 100, 'completion_tokens': 40}}).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                env.update(HARNESS_OFFICIAL_PROVIDER='local-compatible', HARNESS_OFFICIAL_MODEL='simulated-rehearsal',
                           HARNESS_OFFICIAL_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1')
                python = clone / '.venv/bin/python'
                task = {'repo': str(target), 'issue': 'Fix add: it subtracts instead of adding.',
                        'test_commands': [shlex.quote(str(python)) + ' -m unittest discover -s tests -v']}
                run = command(['make', 'run'], clone, json.dumps(task) + '\n')
                if 'Status: RESOLVED | Verification: PASS' not in run.stdout:
                    raise RuntimeError('Repair did not resolve')
                if hashlib.sha256(tests.read_bytes()).hexdigest() != original_hash:
                    raise RuntimeError('Fixture tests changed')
                record.update(status='PASS', simulated_http_requests=Handler.requests,
                              test_integrity='unchanged', default_profile_launch='validated without API request')
                # Persist the generated repair evidence before removing the clone.
                import shutil
                evidence = output / 'rehearsal-evidence'
                if evidence.exists():
                    raise RuntimeError('Rehearsal evidence already exists; choose/archive an earlier run explicitly')
                shutil.copytree(clone / 'artifacts', evidence)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
    except Exception as error:
        record.update(status='FAIL', error=str(error))
        raise
    finally:
        (output / 'rehearsal.json').write_text(json.dumps(record, indent=2) + '\n')
    print('PASS: clean clone/setup/test/launch and simulated HTTP repair. No paid/live model used.')
    print(f'Evidence: {output / "rehearsal.json"}')


if __name__ == '__main__':
    rehearse()
