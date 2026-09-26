import unittest
from pricing import line_total
from checkout import checkout


class CheckoutTests(unittest.TestCase):
    def test_line_quantity(self):
        self.assertEqual(line_total(1200, 3), 3600)

    def test_zero_quantity(self):
        self.assertEqual(line_total(1200, 0), 0)
        self.assertEqual(checkout([(1200, 0)])['total'], 0)

    def test_single_unit(self):
        self.assertEqual(line_total(1200, 1), 1200)

    def test_quantity_reaches_free_shipping(self):
        self.assertEqual(checkout(iter([(2500, 2)])),
                         {'subtotal': 5000, 'discount': 0, 'shipping': 0, 'total': 5000})

    def test_discount_drops_below_threshold(self):
        self.assertEqual(checkout([(5000, 1)], 1000),
                         {'subtotal': 5000, 'discount': 1000, 'shipping': 500, 'total': 4500})

    def test_exact_threshold(self):
        self.assertEqual(checkout([(6000, 1)], 1000)['shipping'], 0)

    def test_below_threshold(self):
        self.assertEqual(checkout([(4900, 1)])['total'], 5400)

    def test_empty_cart(self):
        self.assertEqual(checkout([]),
                         {'subtotal': 0, 'discount': 0, 'shipping': 0, 'total': 0})

    def test_discount_clamping(self):
        self.assertEqual(checkout([(1000, 1)], 2000),
                         {'subtotal': 1000, 'discount': 1000, 'shipping': 500, 'total': 500})
        self.assertEqual(checkout([(1000, 1)], -100)['discount'], 0)

    def test_cart_not_mutated(self):
        items = [(1000, 1), (2000, 1)]
        before = items.copy()
        self.assertEqual(checkout(items)['subtotal'], 3000)
        self.assertEqual(items, before)
