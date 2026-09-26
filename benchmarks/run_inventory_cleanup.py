"""Fresh follow-up of the successful inventory patch; no developer source fix."""
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

ISSUE = '''The previous reserve_order repair passes its public acceptance checks,
but the can_fulfill(stock, quantities) helper remains wrong for exact stock.
For already-validated positive integer quantities, return True iff every
requested SKU has at least the requested stock; missing stock counts as zero.
Do not mutate either input; an empty request is fulfillable.

Preserve all working reserve_order behavior. Fix the helper, remove unused
imports (or use the corrected helper), and remove trailing whitespace in the
three production modules. Remove the temporary reproduce_issue.py, or retain
a useful script with a main guard, no import-time execution and no obsolete
comments describing old behavior. Tests and verification infrastructure are
read-only. Use all supplied acceptance commands. No source patch is supplied.
'''


def prepare():
    candidates = []
    for path in (ROOT / 'artifacts/inventory').glob('*/evidence/*/performance.json'):
        record = json.loads(path.read_text())
        if record.get('status') == 'RESOLVED' and record.get('verification') == 'PASS':
            candidates.append(path)
    if not candidates:
        raise ValueError('A successful inventory repair is required before its cleanup task')
    seed = max(candidates, key=lambda path: path.stat().st_mtime).parents[2] / 'target'
    folder = ROOT / 'artifacts/inventory-cleanup' / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    target = folder / 'target'
    shutil.copytree(seed, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    tests = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (target / 'tests').rglob('*') if p.is_file()}
    (folder / 'manifest.json').write_text(json.dumps({'task_mode': 'helper-and-cleanup', 'seed': str(seed),
                                                    'protected_hashes': tests}, indent=2))
    (folder / 'issue.txt').write_text(ISSUE)
    commands = [
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        [sys.executable, str(ROOT / 'benchmarks/verify_inventory.py'), '--repo', str(target)],
        [sys.executable, str(ROOT / 'benchmarks/verify_inventory_cleanup.py'), '--repo', str(target)],
    ]
    logs = []
    results = []
    for command in commands:
        result = subprocess.run(command, cwd=target, capture_output=True, text=True, timeout=30)
        results.append(result.returncode)
        logs.append(result.stdout + result.stderr)
    (folder / 'baseline.log').write_text('\n'.join(logs))
    if results != [0, 0, 1] or 'Helper acceptance: 5/7 passed' not in logs[-1]:
        raise ValueError('Unexpected helper/cleanup baseline: ' + str(folder / 'baseline.log'))
    print('Inventory follow-up: order checks pass; helper 5/7; cleanup defects reproduced. Fresh target: ' + str(target), flush=True)
    return folder, target, commands


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-only', action='store_true')
    args, options = parser.parse_known_args(argv)
    folder, target, commands = prepare()
    if args.baseline_only:
        return 0
    verification = [item for command in commands for item in ('--test-command', shlex.join(command))]
    return main(['--repo', str(target), '--issue', ISSUE, '--artifacts', str(folder / 'evidence'),
                 *verification, *options])


if __name__ == '__main__':
    raise SystemExit(run())
