"""Run the real adapter on a fresh, intentionally broken fixture."""
from pathlib import Path
import argparse
import re
import shutil
import subprocess
import sys
import time
import uuid

# Allows python benchmarks/run_live.py from any working directory.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.main import main

FIXTURES = {'label_normalization': (6, 4), 'cart_checkout': (10, 5)}


def run(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--fixture', choices=sorted(FIXTURES), default='label_normalization')
    options, harness_args = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    expected_tests, expected_failures = FIXTURES[options.fixture]
    folder = ROOT / 'artifacts' / 'benchmarks' / (time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
    target = folder / 'target'
    shutil.copytree(ROOT / 'benchmarks' / options.fixture, target,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v']
    baseline = subprocess.run(command, cwd=target, capture_output=True, text=True, timeout=30)
    (folder / 'baseline.log').write_text(baseline.stdout + baseline.stderr)
    test_count = re.search(r'Ran (\d+) tests?', baseline.stderr)
    if baseline.returncode != 1 or not test_count or int(test_count[1]) != expected_tests or f'FAILED (failures={expected_failures})' not in baseline.stderr:
        print('Fixture baseline did not match expected test/failure counts; inspect ' + str(folder))
        return 1
    print(f'Fixture: {options.fixture}. Baseline: {expected_tests} tests, {expected_failures} expected failures. Fresh repair target: ' + str(target), flush=True)
    import shlex
    return main(['--repo', str(target), '--issue', (target / 'ISSUE.md').read_text(),
                 '--artifacts', str(folder / 'evidence'),
                 '--test-command', shlex.join(command),
                 '--max-steps', '30', '--wall-seconds', '300', '--budget', '60000', *harness_args])


if __name__ == '__main__':
    raise SystemExit(run())
