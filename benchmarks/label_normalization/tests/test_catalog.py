import unittest
from catalog import normalize_labels


class LabelTests(unittest.TestCase):
    def test_preserves_first_occurrence_order(self):
        self.assertEqual(normalize_labels(['Beta', 'alpha', 'BETA', 'Gamma']),
                         ['beta', 'alpha', 'gamma'])

    def test_whitespace_and_blanks(self):
        self.assertEqual(normalize_labels(['  Zebra ', '', '  ', 'alpha', 'ZEBRA']),
                         ['zebra', 'alpha'])

    def test_casefold_unicode(self):
        self.assertEqual(normalize_labels(['Straße', 'STRASSE', 'Café']),
                         ['strasse', 'café'])

    def test_empty(self):
        self.assertEqual(normalize_labels([]), [])

    def test_input_not_mutated(self):
        original = [' B ', 'a', 'B']
        before = original.copy()
        normalize_labels(original)
        self.assertEqual(original, before)

    def test_generator(self):
        self.assertEqual(normalize_labels(x for x in ['z', 'a', 'Z']), ['z', 'a'])


if __name__ == '__main__':
    unittest.main()
