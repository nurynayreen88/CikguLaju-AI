import unittest

from web.math_unit_groups import grouped_math_units
from web.science_unit_groups import (
    grouped_science_units,
    matched_science_tokens,
    tagged_science_lessons,
)


class UnitNavigationTests(unittest.TestCase):
    def test_science_year_three_groups_the_units_shown_in_the_web_report(self):
        raw = [
            {"value": "acid", "label": "Asid dan Alkali • Asid dan Alkali / 8.1"},
            {"value": "teeth", "label": "Manusia • Manusia / 3.1 Gigi"},
            {"value": "food", "label": "Manusia • Manusia / 3.2 Kelas Makanan"},
            {"value": "machine", "label": "Mesin • Mesin / 10.1 Takal"},
            {"value": "solar", "label": "Sistem Suria • Sistem Suria / 9.1"},
            {"value": "animal", "label": "4.1 • Haiwan"},
            {"value": "plant", "label": "5.1 • Tumbuhan"},
            {"value": "measure", "label": "6.1 • Pengukuran"},
            {"value": "density", "label": "7.1 • Ketumpatan"},
            {"value": "digestion", "label": "3.3 • Manusia"},
        ]
        grouped = grouped_science_units(3, raw)
        self.assertEqual([row["label"] for row in grouped], [
            "Unit 3: Manusia", "Unit 4: Haiwan", "Unit 5: Tumbuh-tumbuhan",
            "Unit 6: Pengukuran", "Unit 7: Ketumpatan", "Unit 8: Asid dan Alkali",
            "Unit 9: Sistem Suria", "Unit 10: Mesin",
        ])
        self.assertEqual(matched_science_tokens(3, raw, "teeth"), ["teeth", "food", "digestion"])
        self.assertEqual(matched_science_tokens(3, raw, "digestion"), ["teeth", "food", "digestion"])
        self.assertEqual(matched_science_tokens(3, raw, "unlisted"), [])

    def test_conflicting_or_unnumbered_units_keep_their_original_identity(self):
        raw = [
            {"value": "conflict", "label": "3.1 • Tumbuhan / 5.1"},
            {"value": "plain", "label": "Bahan tambahan"},
            {"value": "matter", "label": "8.1 • Jirim"},
        ]
        self.assertEqual(grouped_science_units(5, raw),
                         [{"value": "matter", "label": "Unit 8: Jirim"}, *raw[:2]])
        self.assertEqual(matched_science_tokens(5, raw, "conflict"), ["conflict"])

    def test_pdp_order_and_native_source_unit_are_retained(self):
        lessons = tagged_science_lessons([
            ("a", [{"value": "S3-PDP-020", "label": "PdP 20 • Gigi"}]),
            ("b", [{"value": "S3-PDP-019", "label": "PdP 19 • Manusia"}]),
        ])
        self.assertEqual([(x["value"], x["origin_unit"]) for x in lessons],
                         [("S3-PDP-019", "b"), ("S3-PDP-020", "a")])

    def test_math_whole_number_standard_uses_the_unit_format(self):
        raw = [{"value": "a", "label": "1.0 • Nombor Bulat"},
               {"value": "b", "label": "Unit 1: Nombor Bulat"}]
        self.assertEqual(grouped_math_units(raw),
                         [{"value": "a", "label": "Unit 1: Nombor Bulat"}])
