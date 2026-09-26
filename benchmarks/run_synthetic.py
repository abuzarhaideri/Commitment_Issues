"""Fresh single-issue copies of a synthetic repo with full regression checks."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.main import main

ISSUES = {'label-order': 4, 'boolean-config': 3, 'pagination': 4, 'checkout': 5}
TOTAL_TESTS = 31


def prepare(issue, artifacts=None):
    lab = ROOT / 'benchmarks/synthetic_lab'
    base = Path(artifacts) if artifacts else ROOT / 'artifacts/synthetic'
    folder = base / (time.strftime('%Y%m%d-%H%M%S') + '-' + issue + '-' + uuid.uuid4().hex[:8])
    target = folder / 'target'
    shutil.copytree(lab / 'repo', target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for source in (lab / 'bugs' / issue).glob('*.py'):
        shutil.copyfile(source, target / source.name)
    shutil.copyfile(lab / 'issues' / (issue + '.md'), target / 'ISSUE.md')
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v']
    result = subprocess.run(command, cwd=target, capture_output=True, text=True, timeout=30)
    log = result.stdout + result.stderr
    (folder / 'baseline.log').write_text(log)
    count = re.search(r'Ran (\d+) tests?', log)
    if result.returncode != 1 or not count or int(count[1]) != TOTAL_TESTS or f'FAILED (failures={ISSUES[issue]})' not in log:
        raise ValueError('Unexpected synthetic baseline; inspect ' + str(folder))
    manifest = {'issue': issue, 'tests': TOTAL_TESTS, 'baseline_failures': ISSUES[issue],
                'command': command, 'target': str(target.resolve()),
                'baseline_hashes': {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in sorted(target.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}}
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Synthetic issue: {issue}. Baseline: {TOTAL_TESTS} tests, {ISSUES[issue]} expected failures. Fresh target: {target}', flush=True)
    return folder, target, command


def run(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--issue', choices=[*ISSUES, 'all'], required=True)
    parser.add_argument('--baseline-only', action='store_true')
    args, model_options = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    if args.issue == 'all' and not args.baseline_only:
        parser.error('Use one issue per live run; all is only for offline baseline checks')
    selected = list(ISSUES) if args.issue == 'all' else [args.issue]
    for issue in selected:
        folder, target, command = prepare(issue)
        if not args.baseline_only:
            return main(['--repo', str(target), '--issue', (target / 'ISSUE.md').read_text(),
                         '--artifacts', str(folder / 'evidence'), '--test-command', shlex.join(command), *model_options])
    print('Offline baseline checks passed. No model request made.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(run())
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
