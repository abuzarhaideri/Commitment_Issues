"""Independent acceptance corpus outside the agent target; not a secured hidden suite."""
import argparse
import importlib
from pathlib import Path
import sys


def verify(repo):
    sys.path.insert(0, str(Path(repo).resolve()))
    for name in ('orders', 'inventory', 'quantities'):
        sys.modules.pop(name, None)
    reserve = importlib.import_module('orders').reserve_order
    checks = 0
    for stock, lines in [
        ({'a': 6}, [('a', 1), ('a', 2), ('a', 3)]),
        ({'a': 3, 'b': 2}, [('b', 2), ('a', 3)]),
        ({'a': 20, 'b': 10}, [('a', 4), ('b', 2), ('a', 5)]),
    ]:
        expected = {}
        for sku, quantity in lines:
            expected[sku] = expected.get(sku, 0) + quantity
        before = stock.copy()
        receipt = reserve(stock, iter(lines))
        assert receipt == expected, 'incorrect aggregation'
        assert stock == {sku: value - expected.get(sku, 0) for sku, value in before.items()}, 'incorrect stock'
        receipt['sentinel'] = 100
        assert 'sentinel' not in stock, 'receipt aliases stock'
        checks += 1
    for stock, lines in [
        ({'a': 3}, [('a', 2), ('a', 2)]),
        ({'a': 5}, [('a', 1), ('missing', 1)]),
        ({'a': 5}, [('missing', 1), ('a', 1)]),
        ({'a': 5}, [('a', 1), ('a', -1)]),
    ]:
        before = stock.copy()
        try:
            reserve(stock, iter(lines))
        except ValueError:
            pass
        else:
            raise AssertionError('invalid order accepted')
        assert stock == before, 'rejected order changed stock'
        checks += 1
    for quantity in (False, 1.0, '1', None):
        stock = {'a': 5}
        try:
            reserve(stock, [('a', 1), ('a', quantity)])
        except TypeError:
            pass
        else:
            raise AssertionError('invalid quantity accepted')
        assert stock == {'a': 5}, 'invalid quantity changed stock'
        checks += 1
    print(f'Independent inventory acceptance: {checks}/{checks} checks passed')
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
    verify(args.repo)
