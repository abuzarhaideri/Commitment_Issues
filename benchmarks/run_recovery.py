"""Controlled live edit-conflict recovery; fault injection is explicitly labelled."""
import argparse
import json
from unittest.mock import patch
from pathlib import Path
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks.run_synthetic import prepare
from harness.main import main
from harness.orchestrator import protected
from harness.tools import ToolRegistry


class EditConflictTools(ToolRegistry):
    injected = False

    def _edit_file(self, path, old, new):
        target = self._path(path)
        eligible = (not self.injected and old != new and bool(old) and target.is_file() and
                    not protected(str(target.relative_to(self.repo))) and self._read(target).count(old) == 1)
        if eligible:
            self.injected = True
            raise ValueError('CONTROLLED BENCHMARK EDIT CONFLICT: first valid edit rejected before writing. '
                             'No file changed. Reread the target and retry the repair. This fault is injected, not a model mistake.')
        return super()._edit_file(path, old, new)


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-only', action='store_true')
    args, options = parser.parse_known_args(argv)
    folder, target, command = prepare('checkout', ROOT / 'artifacts/recovery')
    manifest_path = folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['task_mode'] = 'controlled-first-edit-conflict'
    manifest['fault'] = 'Reject first valid production replacement before writing; model is told this is injected'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    if args.baseline_only:
        return 0
    issue = (target / 'ISSUE.md').read_text() + (
        '\nControlled recovery evaluation: the first valid production edit will be rejected '
        'without modifying files. Recover by inspecting evidence and retrying. This is an '
        'injected tool conflict, not proof of recovery from a naturally incorrect model patch.\n')
    instances = []
    class RecordedTools(EditConflictTools):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            instances.append(self)
    with patch('harness.orchestrator.ToolRegistry', RecordedTools):
        result = main(['--repo', str(target), '--issue', issue,
                       '--artifacts', str(folder / 'evidence'), '--test-command', shlex.join(command), *options])
    injected = bool(instances and instances[0].injected)
    (folder / 'fault-result.json').write_text(json.dumps({'fault_injected': injected,
        'scope': 'Controlled tool conflict, not naturally failed patch recovery',
        'harness_exit': result}, indent=2) + '\n')
    if not injected:
        print('Recovery benchmark invalid: no eligible production edit reached the injected fault.')
        return 1
    return result


if __name__ == '__main__':
    raise SystemExit(run())
