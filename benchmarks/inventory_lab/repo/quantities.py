def aggregate_requests(lines):
    quantities = {}
    for sku, quantity in lines:
        if type(quantity) is not int:
            raise TypeError('quantity must be an integer')
        if quantity <= 0:
            raise ValueError('quantity must be positive')
        quantities[sku] = quantities.get(sku, 0) + quantity
    return quantities
