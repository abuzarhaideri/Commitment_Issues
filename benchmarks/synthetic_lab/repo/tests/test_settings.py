import unittest
from settings import parse_bool


class SettingsTests(unittest.TestCase):
    def test_boolean_values(self):
        self.assertIs(parse_bool(True), True)
        self.assertIs(parse_bool(False), False)

    def test_true_strings(self):
        for value in ['true', '1', 'YES', ' On ']:
            with self.subTest(value=value):
                self.assertIs(parse_bool(value), True)

    def test_false_strings(self):
        for value in ['false', '0', 'NO', ' Off ']:
            self.assertIs(parse_bool(value), False)

    def test_invalid_strings(self):
        for value in ['', ' ', 'maybe', 'false-ish']:
            with self.assertRaises(ValueError):
                parse_bool(value)

    def test_non_string_values(self):
        for value in [0, 1, [], {}]:
            with self.assertRaises(TypeError):
                parse_bool(value)

    def test_missing_default_false(self):
        self.assertIs(parse_bool(None), False)

    def test_missing_custom_default(self):
        self.assertIs(parse_bool(None, default=True), True)
