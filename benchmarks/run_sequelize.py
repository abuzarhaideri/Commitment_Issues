"""Run the prepared real Sequelize source task; no download or injected defect."""
import json
import hashlib
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.main import main

ISSUE = '''The public utility isValidNumberSyntax incorrectly accepts scientific notation
without a mantissa: "e5", "-e5", and "E+10" currently return true.
Require a numeric mantissa while preserving valid integers, negative numbers,
fractions including .5 and -.5, and scientific notation with signed exponents.
Preserve rejection of malformed input and whitespace. Repair TypeScript source,
not just generated JavaScript. Do not modify tests, dependency/config files, or
the verification scripts. Run the supplied verification command, which rebuilds
the utility package and runs its existing unit suite plus regression checks.
'''


def run(argv):
    folder = ROOT / 'artifacts/external/sequelize'
    manifest_path = folder / 'benchmark.json'
    if not manifest_path.is_file():
        raise ValueError('Sequelize benchmark is not prepared; see docs/sequelize-benchmark.md')
    manifest = json.loads(manifest_path.read_text())
    target = folder / 'source'
    node = Path(manifest['node'])
    if not node.is_file():
        raise ValueError('Prepared Node runtime is unavailable')
    current = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
    if current != manifest['commit']:
        raise ValueError('Sequelize revision differs from the prepared benchmark')
    for name, digest in manifest['baseline_hashes'].items():
        if hashlib.sha256((target / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Prepared source/regression baseline changed; no model request made')
    command = shlex.join([sys.executable, str(ROOT / 'benchmarks/verify_sequelize.py'),
                          '--repo', str(target), '--node', str(node)])
    # Confirm the selected task is still broken before using model quota.
    probe = subprocess.run([sys.executable, str(ROOT / 'benchmarks/verify_sequelize.py'),
                           '--repo', str(target), '--node', str(node)],
                           cwd=target, capture_output=True, text=True, timeout=180)
    log = probe.stdout + probe.stderr
    (folder / 'baseline-current.log').write_text(log)
    if probe.returncode != 1 or '# fail 3' not in log or '# pass 2' not in log or '158 passing' not in log:
        raise ValueError('Prepared regression baseline changed or task is already repaired; no model request made')
    print('Sequelize: 158 existing unit tests pass; regression baseline 2 pass / 3 fail. Commit: ' + current, flush=True)
    return main(['--repo', str(target), '--issue', ISSUE,
                 '--artifacts', str(folder / 'evidence'), '--test-command', command,
                 '--command-timeout', '120', *argv])
