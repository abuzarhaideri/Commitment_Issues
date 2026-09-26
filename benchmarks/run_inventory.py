"""Fresh three-module synthetic reservation repair, with independent acceptance."""
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

LAB = ROOT / 'benchmarks/inventory_lab'
BUGS = {
    'quantities.py': ('quantities.get(sku, 0) + quantity', 'quantity'),
    'inventory.py': ('>= quantity', '> quantity'),
    'orders.py': (
        "    if not can_fulfill(stock, quantities):\n        raise ValueError('insufficient stock')\n    for sku, quantity in quantities.items():\n        stock[sku] -= quantity",
        "    for sku, quantity in quantities.items():\n        if stock.get(sku, 0) < quantity:\n            raise ValueError('insufficient stock')\n        stock[sku] -= quantity\n    if not can_fulfill(stock, quantities):\n        raise ValueError('insufficient stock')"),
}


def prepare(base=None):
    folder = (Path(base) if base else ROOT / 'artifacts/inventory') / (
        datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
    target = folder / 'target'
    shutil.copytree(LAB / 'repo', target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name, (old, new) in BUGS.items():
        path = target / name
        assert path.read_text().count(old) == 1
        path.write_text(path.read_text().replace(old, new))
    distractors = target / 'legacy'
    distractors.mkdir()
    for i in range(12):
        (distractors / f'reservation_{i}.py').write_text(
            '# Legacy reporting helpers; not imported by the active order service.\n'
            f'def reserve_order_{i}(stock, lines):\n    return list(lines)\n')
    shutil.copy2(LAB / 'issue.md', target / 'ISSUE.md')
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v']
    result = subprocess.run(command, cwd=target, capture_output=True, text=True, timeout=30)
    log = result.stdout + result.stderr
    (folder / 'baseline.log').write_text(log)
    if result.returncode != 1 or 'Ran 8 tests' not in log or 'FAILED (failures=3, errors=1)' not in log:
        raise ValueError('Unexpected inventory baseline: ' + str(folder))
    hashes = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in target.rglob('*') if p.is_file()}
    (folder / 'manifest.json').write_text(json.dumps({'task_mode': 'synthetic-inventory', 'baseline_hashes': hashes,
                                                    'baseline': log}, indent=2))
    print('Synthetic inventory: 8 visible tests, baseline reproduced. Fresh target: ' + str(target), flush=True)
    return folder, target, command


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-only', action='store_true')
    args, options = parser.parse_known_args(argv)
    folder, target, command = prepare()
    if args.baseline_only:
        return 0
    acceptance = shlex.join([sys.executable, str(ROOT / 'benchmarks/verify_inventory.py'), '--repo', str(target)])
    issue = (target / 'ISSUE.md').read_text()
    return main(['--repo', str(target), '--issue', issue, '--artifacts', str(folder / 'evidence'),
                 '--test-command', shlex.join(command), '--test-command', acceptance, *options])


if __name__ == '__main__':
    raise SystemExit(run())
