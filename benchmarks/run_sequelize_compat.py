"""Fresh task correcting compatibility regressions in an earlier harness patch."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.main import main

BASE = ROOT / 'artifacts/external/sequelize'
ISSUE = '''An earlier repair of isValidNumberSyntax rejected exponent-only strings
but introduced compatibility regressions: "1.", "-1.", "1.e3" and "-1.e-3"
are now accepted although the original public utility rejected them.
Correct the TypeScript implementation while keeping "e5", "-e5", "E+10",
empty strings, bare signs, malformed strings and whitespace rejected.
Preserve valid integers, decimal fractions including .5 and -.5, and
scientific notation such as 1e3, 1e+3 and -1.2E-3.
Inspect source and tests and make a minimal production repair. Do not edit
tests, dependencies, configuration or verification infrastructure.
The supplied command rebuilds source and runs original utility tests,
the five original issue checks and seventeen compatibility checks.
This is a regression introduced by the earlier harness patch, not a claim
of a new upstream bug. Preserve unrelated behavior.
'''


def prepare():
    config = json.loads((BASE / 'benchmark.json').read_text())
    source, node = BASE / 'source', Path(config['node'])
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != config['commit'] or not node.is_file():
        raise ValueError('Prepared revision/runtime unavailable')
    folder = BASE / 'compatibility-runs' / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    target = folder / 'target'
    # Copy dependency files; preserve relative workspace links without sharing writable files.
    shutil.copytree(source, target, symlinks=True,
                    ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
    protected = {}
    for path in target.rglob('*'):
        if 'node_modules' in path.parts or '.yarn' in path.parts or path.is_symlink():
            continue
        if path.is_file() and (any(part in ('test', 'tests', '.github') for part in path.relative_to(target).parts)
                               or path.name in ('package.json', 'yarn.lock', 'AGENTS.md', 'Makefile')
                               or path.name.startswith('tsconfig')):
            protected[str(path.relative_to(target))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder / 'task-manifest.json').write_text(json.dumps({'commit': commit, 'task_mode': 'prior-patch-compatibility',
                                                          'protected_hashes': protected}, indent=2))
    (folder / 'issue.txt').write_text(ISSUE)
    command = [sys.executable, str(ROOT / 'benchmarks/verify_sequelize_compat.py'),
               '--repo', str(target), '--node', str(node)]
    probe = subprocess.run(command, capture_output=True, text=True, timeout=240)
    log = probe.stdout + probe.stderr
    (folder / 'baseline.log').write_text(log)
    if probe.returncode != 1 or '158 passing' not in log or '# fail 4' not in log or '# pass 13' not in log:
        raise ValueError('Expected existing tests passing and 13/17 compatibility baseline: ' + str(folder / 'baseline.log'))
    print('Sequelize compatibility baseline: original checks pass; 13 pass / 4 fail. Fresh target: ' + str(target), flush=True)
    return folder, target, command


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-only', action='store_true')
    args, options = parser.parse_known_args(argv)
    folder, target, command = prepare()
    if args.baseline_only:
        return 0
    return main(['--repo', str(target), '--issue', ISSUE, '--artifacts', str(folder / 'evidence'),
                 '--test-command', shlex.join(command), *options, '--command-timeout', '240'])


if __name__ == '__main__':
    raise SystemExit(run())
