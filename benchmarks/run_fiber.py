"""Fresh real Fiber issue target, with original source preserved and no injected bug."""
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
from harness.main import main as harness_main

BASE = ROOT / 'artifacts/external/fiber'
ISSUE = '''Inspect this Fiber checkout and identify a reproducible defect using its
source, documentation and test evidence. Diagnose the root cause yourself and
make a minimal production fix. This is a harness evaluation: no prewritten fix
or source-file diagnosis is supplied. Start with the focused diagnostic command
below, inspect failing evidence, and narrow your searches and tests.
Preserve existing behavior outside the defect and do not weaken verification.
Read AGENTS.md. Tests, dependency files, Makefile, contributor instructions and
evaluation infrastructure are read-only. The evaluator has added fixed regression
checks; they may be inspected but not changed. This is one prepared repair task,
not a claim that every bug in the repository will be discovered or repaired.
Use the supplied verifier for Go execution; it configures the project-local
runtime/caches. Run full suite/vet and targeted race checks before finishing.
'''


FOCUSED_ISSUE = '''Fix Fiber's HTTP Range parsing bug: trailing empty comma-separated
entries bypass MaxRanges. The documented contract says empty elements count
toward MaxRanges even though they do not represent actual ranges.

With MaxRanges=1, parsing "bytes=0-0," for a resource of size 10 currently
succeeds. It must return ErrRangeTooLarge, set HTTP status 416, and set
Content-Range to "bytes */10". Also reject "bytes=0-0,," and
"bytes=0-0,, \t" with MaxRanges=2. Preserve acceptance of "bytes=0-0,"
with MaxRanges=2, normal valid ranges and existing leading-empty behavior.

Find and inspect the implementation yourself and make a minimal production
fix. No patch or source-file location is supplied. Read AGENTS.md.
Tests, dependency files, Makefile, contributor instructions and evaluation
infrastructure are read-only. Inspect the fixed regression tests but do not
change them or weaken verification. Use the supplied focused diagnostic
command, then full suite/vet and targeted race verification before finishing.
This is an explicit issue-driven repair benchmark, separate from discovery.
'''



def prepare(issue=ISSUE, mode='discovery'):
    source = BASE / 'source'
    config = json.loads((BASE / 'benchmark.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != config['commit'] or subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Prepared Fiber source changed; preserve/review it before preparing another task')
    folder = BASE / 'runs' / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    target = folder / 'target'
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git'))
    shutil.copy2(ROOT / 'benchmarks/fiber_range_regression_test.go', target / 'harness_range_regression_test.go')
    (folder / 'issue.txt').write_text(issue)
    protected = {}
    for path in target.rglob('*'):
        if path.is_file() and (path.name.endswith('_test.go') or path.name in ('go.mod', 'go.sum', 'AGENTS.md', 'Makefile') or '.github' in path.parts):
            protected[str(path.relative_to(target))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder / 'task-manifest.json').write_text(json.dumps({'commit': commit, 'task_mode': mode, 'protected_hashes': protected}, indent=2) + '\n')
    probe = subprocess.run([sys.executable, str(ROOT / 'benchmarks/verify_fiber.py'), '--repo', str(target), '--scope', 'regression'],
                           capture_output=True, text=True, timeout=240)
    (folder / 'baseline.log').write_text(probe.stdout + probe.stderr)
    # Count leaf checks from the freshly captured raw JSON, excluding the parent.
    raw_path = next(line.removeprefix('Full raw log: ') for line in probe.stdout.splitlines() if line.startswith('Full raw log: '))
    events = [json.loads(line) for line in Path(raw_path).read_text().splitlines() if line.startswith('{')]
    counts = {action: sum(e.get('Action') == action and '/' in e.get('Test', '') for e in events) for action in ('pass', 'fail')}
    if probe.returncode != 1 or counts != {'pass': 4, 'fail': 3}:
        raise ValueError('Expected 4 passing / 3 failing regression checks; see ' + str(folder / 'baseline.log'))
    print('Fiber task mode: ' + mode, flush=True)
    print(f'Fiber baseline: 7 regression checks, 4 pass / 3 fail. Commit: {commit}', flush=True)
    print('Fresh target: ' + str(target), flush=True)
    return folder, target


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-only', action='store_true')
    parser.add_argument('--focused', action='store_true', help='Explicit Range issue; separate from discovery')
    args, model_args = parser.parse_known_args(argv)
    folder, target = prepare(FOCUSED_ISSUE, 'focused') if args.focused else prepare()
    if args.baseline_only:
        return 0
    commands = [shlex.join([sys.executable, str(ROOT / 'benchmarks/verify_fiber.py'), '--repo', str(target), '--scope', scope]) for scope in ('all', 'range-race')]
    diagnostic = shlex.join([sys.executable, str(ROOT / 'benchmarks/verify_fiber.py'),
                             '--repo', str(target), '--scope', 'regression'])
    issue = (FOCUSED_ISSUE if args.focused else ISSUE) + '\nFocused diagnostic command (expected failing baseline): ' + diagnostic + '\n'
    return harness_main(['--repo', str(target), '--issue', issue, '--artifacts', str(folder / 'evidence'),
                         '--test-command', commands[0], '--test-command', commands[1],
                         *model_args, '--command-timeout', '240'])


if __name__ == '__main__':
    try:
        raise SystemExit(run(sys.argv[1:]))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print('Fiber preparation failed: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
