"""Guard the exact 696 PI Bidang/PdP identities from the reviewed v2 archive."""
import unittest
from web.pi_696_catalog_20261121 import (
    YEAR_FIELDS, FIELD_LABELS, unit_options, pdp_options, valid_choice,
)
from web.pi_696_private_bundle import YEARS


class TestPIV2OrdinaryMenu(unittest.TestCase):
    def test_all_696_are_unique_and_selectable(self):
        self.assertEqual(sum(YEARS.values()), 696)
        for year, count in YEARS.items():
            rows = unit_options(year)
            self.assertNotIn("RPH Premium", str(rows))
            self.assertEqual(len(rows), len({item["value"] for item in rows}))
            numbers = []
            for unit in rows:
                opts = pdp_options(year, unit["value"])
                self.assertTrue(opts)
                numbers.extend(int(item["value"]) for item in opts)
                for item in opts:
                    self.assertEqual(valid_choice(year, unit["value"], item["value"]),
                                     item["pdp_no"])
            self.assertEqual(sorted(numbers), list(range(1, count + 1)))
            self.assertEqual(len(YEAR_FIELDS[year]), count)

    def test_mismatched_bidang_and_pdp_fail_closed(self):
        for year, sequence in YEAR_FIELDS.items():
            source = FIELD_LABELS[sequence[0]]
            different = next(name for key, name in FIELD_LABELS.items() if key != sequence[0])
            self.assertEqual(valid_choice(year, source, "1"), 1)
            with self.assertRaises(ValueError):
                valid_choice(year, different, "1")
            with self.assertRaises(ValueError):
                valid_choice(year, source, str(len(sequence)+1))
        with self.assertRaises(ValueError):
            pdp_options(2, "RPH Premium 2027")
        self.assertEqual(unit_options(1), [])
        self.assertEqual(unit_options(7), [])


if __name__ == "__main__":
    unittest.main()
