"""Compute a checkout summary without modifying the cart."""
from pricing import line_total

FREE_SHIPPING_CENTS = 5000
SHIPPING_CENTS = 500


def checkout(items, discount_cents=0):
    """Items is an iterable of (unit price in cents, quantity) pairs."""
    subtotal = sum(line_total(price, quantity) for price, quantity in items)
    discount = min(max(discount_cents, 0), subtotal)
    net = subtotal - discount
    shipping = 0 if subtotal >= FREE_SHIPPING_CENTS else SHIPPING_CENTS
    return {'subtotal': subtotal, 'discount': discount,
            'shipping': shipping, 'total': net + shipping}
