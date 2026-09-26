"""Rebuild source before database-free Sequelize utility verification."""
import argparse
import os
from pathlib import Path
import subprocess


def verify(repo, node):
    repo, node = Path(repo).resolve(), Path(node).resolve()
    if not repo.is_dir() or not node.is_file():
        raise ValueError('Existing Sequelize repository and Node runtime are required')
    env = dict(os.environ)
    env['PATH'] = str(node.parent) + os.pathsep + env.get('PATH', '')
    yarn = str(repo / '.yarn/releases/yarn-4.18.0.cjs')
    commands = [
        [str(node), yarn, 'workspace', '@sequelize/utils', 'build'],
        [str(node), yarn, 'workspace', '@sequelize/utils', 'test-unit'],
        [str(node), '--test', '--test-reporter=tap', str(repo / 'test/harness-number-syntax.test.cjs')],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=repo, env=env, timeout=120)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--node', required=True, type=Path)
    args = parser.parse_args()
    try:
        raise SystemExit(verify(args.repo, args.node))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        parser.error(str(exc))
