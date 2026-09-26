"""Helper API and scoped source-cleanup acceptance; does not modify target."""
import argparse
import ast
import importlib
import hashlib
import json
from pathlib import Path
import sys


def check(repo):
    repo = Path(repo).resolve()
    manifest_path = repo.parent / 'manifest.json'
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        for name, digest in manifest.get('protected_hashes', {}).items():
            path = repo / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('Protected test changed: ' + name)
    sys.path.insert(0, str(repo))
    sys.modules.pop('inventory', None)
    helper = importlib.import_module('inventory').can_fulfill
    cases = [
        ({'a': 2}, {'a': 2}, True),
        ({'a': 3, 'b': 2}, {'a': 1, 'b': 2}, True),
        ({'a': 3}, {'a': 2}, True),
        ({'a': 1}, {'a': 2}, False),
        ({'a': 3}, {'missing': 1}, False),
        ({}, {}, True),
        ({'a': 3}, {}, True),
    ]
    failures = []
    passed = 0
    for index, (stock, quantities, expected) in enumerate(cases, 1):
        before = (stock.copy(), quantities.copy())
        if helper(stock, quantities) is not expected or (stock, quantities) != before:
            failures.append(f'helper case {index}: expected {expected}, no mutation')
        else:
            passed += 1
    for name in ('orders.py', 'inventory.py', 'quantities.py'):
        text = (repo / name).read_text()
        if any(line != line.rstrip(' \t') for line in text.splitlines()):
            failures.append('trailing whitespace: ' + name)
    tree = ast.parse((repo / 'orders.py').read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module == 'inventory']
    used = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    if any((alias.asname or alias.name) not in used for node in imports for alias in node.names):
        failures.append('inventory helper import is unused; remove it or use the corrected helper')
    script = repo / 'reproduce_issue.py'
    if script.exists():
        tree = ast.parse(script.read_text())
        allowed = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        for node in tree.body:
            if isinstance(node, allowed) or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                continue
            if isinstance(node, ast.If) and ast.unparse(node.test) == "__name__ == '__main__'":
                continue
            failures.append('reproduction script has unguarded top-level executable code')
            break
        if '# Current implementation returns' in script.read_text():
            failures.append('reproduction script retains obsolete behavior comment')
    print(f'Helper acceptance: {passed}/{len(cases)} passed')
    for failure in failures:
        print('FAIL: ' + failure)
    return 1 if failures else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    raise SystemExit(check(parser.parse_args().repo))
