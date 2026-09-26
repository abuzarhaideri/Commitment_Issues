import unittest
from orders import reserve_order


class ReservationTests(unittest.TestCase):
    def test_regular_order(self):
        stock = {'a': 5, 'b': 4}
        self.assertEqual(reserve_order(stock, [('a', 2), ('b', 1)]), {'a': 2, 'b': 1})
        self.assertEqual(stock, {'a': 3, 'b': 3})

    def test_duplicate_skus_are_added(self):
        stock = {'a': 10}
        self.assertEqual(reserve_order(stock, [('a', 2), ('a', 3)]), {'a': 5})
        self.assertEqual(stock, {'a': 5})

    def test_exact_stock_is_allowed(self):
        stock = {'a': 2}
        self.assertEqual(reserve_order(stock, [('a', 2)]), {'a': 2})
        self.assertEqual(stock, {'a': 0})

    def test_rejected_order_is_atomic(self):
        stock = {'a': 5, 'b': 1}
        original = stock.copy()
        with self.assertRaises(ValueError):
            reserve_order(stock, [('a', 2), ('b', 2)])
        self.assertEqual(stock, original)

    def test_zero_quantity_rejected(self):
        stock = {'a': 5}
        with self.assertRaises(ValueError):
            reserve_order(stock, [('a', 0)])
        self.assertEqual(stock, {'a': 5})

    def test_bool_is_not_quantity(self):
        with self.assertRaises(TypeError):
            reserve_order({'a': 5}, [('a', True)])

    def test_empty_order(self):
        stock = {'a': 5}
        self.assertEqual(reserve_order(stock, []), {})
        self.assertEqual(stock, {'a': 5})

    def test_generator_input(self):
        stock = {'a': 10}
        self.assertEqual(reserve_order(stock, ((sku, qty) for sku, qty in [('a', 2), ('a', 1)])), {'a': 3})
