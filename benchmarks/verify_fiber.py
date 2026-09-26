"""Verify a prepared Fiber repair with project-local Go caches and JSON evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/external/fiber'


def go_environment():
    runtime = BASE / 'runtime'
    go = runtime / 'go/bin/go'
    if not go.is_file():
        raise ValueError('Prepared project-local Go toolchain is unavailable')
    env = dict(os.environ)
    env.update(PATH=str(go.parent) + os.pathsep + env.get('PATH', ''),
               GOPATH=str(runtime / 'gopath'), GOMODCACHE=str(runtime / 'modcache'),
               GOCACHE=str(runtime / 'buildcache'), GOTOOLCHAIN='local', GOPROXY='off')
    return go, env


def summarize(lines):
    counts = {'pass': 0, 'fail': 0, 'skip': 0, 'top_level_pass': 0,
              'top_level_fail': 0, 'packages_pass': 0, 'packages_fail': 0}
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        action, test = event.get('Action'), event.get('Test')
        if action not in ('pass', 'fail', 'skip'):
            continue
        if test:
            counts[action] += 1
            if '/' not in test and action in ('pass', 'fail'):
                counts['top_level_' + action] += 1
        elif action in ('pass', 'fail'):
            counts['packages_' + action] += 1
    return counts


def verify(repo, scope='all'):
    repo = Path(repo).resolve()
    go, env = go_environment()
    if not (repo / 'go.mod').is_file():
        raise ValueError('Existing Fiber checkout required')
    manifest_path = repo.parent / 'task-manifest.json'
    if not manifest_path.is_file():
        raise ValueError('Prepared task manifest is required')
    manifest = json.loads(manifest_path.read_text())
    for name, digest in manifest['protected_hashes'].items():
        path = repo / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Protected prepared file changed: ' + name)
    command = [str(go), 'test', '-mod=readonly', '-json', '-count=1']
    if scope == 'regression':
        command += ['-run', '^Test_Harness_RangeMaxRanges$', '.']
    elif scope == 'range-race':
        command += ['-race', '-run', '^Test_(Ctx_Range|Harness_RangeMaxRanges)', '.']
    else:
        command += ['./...']
    logs = BASE / 'verification-logs'
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / (datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8] + '.jsonl')
    with log.open('w') as output:
        result = subprocess.run(command, cwd=repo, env=env, stdout=output,
                                stderr=subprocess.STDOUT, timeout=240)
    lines = log.read_text().splitlines()
    counts = summarize(lines)
    # Print failing test blocks and non-JSON compiler output, not thousands of
    # passing subtest lines. Full output remains outside the target checkout.
    failed = set()
    events = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            print(line)
            continue
        events.append(event)
        if event.get('Action') == 'fail' and event.get('Test'):
            failed.add((event.get('Package'), event['Test']))
    for event in events:
        if event.get('Action') == 'output' and (event.get('Package'), event.get('Test')) in failed:
            print(event.get('Output', ''), end='')
    print('Go verification:', json.dumps(counts), '| scope:', scope)
    print('Full raw log:', log)
    if counts['pass'] + counts['fail'] == 0:
        print('no tests ran')
        return 1
    if result.returncode:
        return result.returncode
    if scope == 'all':
        vet = subprocess.run([str(go), 'vet', '-mod=readonly', './...'], cwd=repo, env=env, timeout=120)
        if vet.returncode:
            return vet.returncode
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--scope', choices=['all', 'regression', 'range-race'], default='all')
    args = parser.parse_args()
    try:
        raise SystemExit(verify(args.repo, args.scope))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        parser.error(str(exc))
