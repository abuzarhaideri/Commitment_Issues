def can_fulfill(stock, quantities):
    return all(stock.get(sku, 0) >= quantity for sku, quantity in quantities.items())
