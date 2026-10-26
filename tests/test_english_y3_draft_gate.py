"""Regression tests: unverified Year 3 RPH must never leak to users."""
import unittest
from english_standalone_adapter import load_english_rph, get_english_rph


class Year3DraftGateTest(unittest.TestCase):
    def test_unverified_year3_never_served(self):
        for lesson in (1, 19, 98, 127, 149):
            self.assertIsNone(load_english_rph(3, lesson))
            self.assertIsNone(get_english_rph(3, "English", lesson))

    def test_existing_years_still_work(self):
        self.assertIsNotNone(load_english_rph(1, 1))
        self.assertIsNotNone(load_english_rph(2, 1))

    def test_invalid_ids(self):
        self.assertIsNone(load_english_rph(3, "../1"))
        self.assertIsNone(load_english_rph(True, 1))


if __name__ == "__main__":
    unittest.main()
