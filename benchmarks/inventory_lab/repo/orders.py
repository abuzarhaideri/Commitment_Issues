from quantities import aggregate_requests
from inventory import can_fulfill


def reserve_order(stock, lines):
    quantities = aggregate_requests(lines)
    if not can_fulfill(stock, quantities):
        raise ValueError('insufficient stock')
    for sku, quantity in quantities.items():
        stock[sku] -= quantity
    return dict(quantities)
