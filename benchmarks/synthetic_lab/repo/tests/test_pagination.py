import unittest
from pagination import paginate


class PaginationTests(unittest.TestCase):
    def test_first_page(self):
        self.assertEqual(paginate([1, 2, 3, 4, 5], 1, 2), [1, 2])

    def test_middle_page(self):
        self.assertEqual(paginate([1, 2, 3, 4, 5], 2, 2), [3, 4])

    def test_partial_last_page(self):
        self.assertEqual(paginate([1, 2, 3, 4, 5], 3, 2), [5])

    def test_exact_last_page(self):
        self.assertEqual(paginate([1, 2, 3, 4], 2, 2), [3, 4])

    def test_beyond_end(self):
        self.assertEqual(paginate([1, 2], 4, 2), [])

    def test_empty(self):
        self.assertEqual(paginate([], 1, 2), [])

    def test_invalid_boundaries(self):
        for page, size in [(0, 2), (-1, 2), (1, 0), (1, -1)]:
            with self.subTest(page=page, size=size), self.assertRaises(ValueError):
                paginate([1, 2], page, size)

    def test_input_not_mutated(self):
        items = [1, 2, 3]
        before = items.copy()
        paginate(items, 1, 2)
        self.assertEqual(items, before)
