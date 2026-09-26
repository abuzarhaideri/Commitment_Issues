"""Rebuild, existing/regression tests, then independent compatibility corpus."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.verify_sequelize import verify


def verify_compat(repo, node):
    repo = Path(repo).resolve()
    manifest = json.loads((repo.parent / 'task-manifest.json').read_text())
    for name, digest in manifest['protected_hashes'].items():
        path = repo / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Protected file changed: ' + name)
    result = verify(repo, node)
    if result:
        return result
    env = dict(os.environ, SEQUELIZE_REPO=str(repo))
    return subprocess.run([str(node), '--test', '--test-reporter=tap',
                           str(ROOT / 'benchmarks/check_number_compatibility.cjs')],
                          cwd=repo, env=env, timeout=120).returncode


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--node', required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(verify_compat(args.repo, args.node))
