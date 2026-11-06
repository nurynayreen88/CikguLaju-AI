"""Regression: one displayed Mathematics Unit number, zero lost source PdPs."""
import unittest
from pathlib import Path

from web.math_unit_groups import (
    grouped_math_units, matched_math_tokens, tagged_math_lessons,
)

ROOT = Path(__file__).resolve().parents[1]
A = "u" + "a" * 24
B = "u" + "b" * 24
C = "u" + "c" * 24


class MathematicsUnitGroupTests(unittest.TestCase):
    def setUp(self):
        self.units = [
            {"value": A, "label": "Unit 01: Nombor Bulat"},
            {"value": B, "label": "Unit 1 — Nombor Bulat"},
            {"value": C, "label": "Unit 02: Operasi Asas"},
        ]

    def test_unit_one_once_without_mutating_original_source(self):
        before = [dict(row) for row in self.units]
        grouped = grouped_math_units(self.units)
        self.assertEqual(len(grouped), 2)
        self.assertEqual(grouped[0]["value"], A)
        self.assertEqual(grouped[0]["label"], "Unit 1: Nombor Bulat")
        self.assertEqual(grouped[1]["label"], "Unit 2: Operasi Asas")
        self.assertEqual(self.units, before)
        self.assertEqual(matched_math_tokens(self.units, A), [A, B])
        self.assertEqual(matched_math_tokens(self.units, B), [A, B])
        self.assertEqual(matched_math_tokens(self.units, C), [C])
        self.assertEqual(matched_math_tokens(self.units, "u" + "d" * 24), [])

    def test_different_titles_same_number_visible_once_but_both_preserved(self):
        items = [
            {"value": A, "label": "Unit 1: Nombor Bulat"},
            {"value": B, "label": "1 • Nombor dan Operasi"},
        ]
        grouped = grouped_math_units(items)
        self.assertEqual(len(grouped), 1)
        self.assertTrue(grouped[0]["label"].startswith("Unit 1:"))
        self.assertIn("Nombor Bulat", grouped[0]["label"])
        self.assertIn("Nombor dan Operasi", grouped[0]["label"])
        self.assertEqual(matched_math_tokens(items, A), [A, B])

    def test_all_lessons_keep_source_tokens_even_if_pdp_names_repeat(self):
        rows = tagged_math_lessons([
            (A, [
                {"value": "M2-PDP-001", "label": "PdP 001 — Nombor"},
                {"value": "M2-PDP-002", "label": "PdP 002 — Nilai tempat"},
            ]),
            (B, [
                {"value": "M2-PDP-003", "label": "PdP 003 — Perbandingan"},
                {"value": "M2-PDP-004", "label": "PdP 004 — Perbandingan"},
            ]),
        ])
        self.assertEqual(len(rows), 4)
        self.assertEqual([r["origin_unit"] for r in rows], [A, A, B, B])
        self.assertEqual([r["value"] for r in rows],
                         ["M2-PDP-001","M2-PDP-002",
                          "M2-PDP-003","M2-PDP-004"])
        self.assertNotIn("origin_unit", {"value": "M2-PDP-001"})
        with self.assertRaises(ValueError):
            tagged_math_lessons([(A,[rows[0],rows[0]])])

    def test_no_grouping_across_years_or_unnumbered_unrelated_units(self):
        year1 = grouped_math_units([{"value": A, "label": "Unit 1: Nombor"}])
        year2 = grouped_math_units([{"value": B, "label": "Unit 1: Nombor"}])
        self.assertEqual(year1[0]["value"], A)
        self.assertEqual(year2[0]["value"], B)
        distinct = grouped_math_units([
            {"value": A, "label": "Tema Algebra"},
            {"value": B, "label": "Tema Geometri"},
        ])
        self.assertEqual(len(distinct), 2)

    def test_runtime_uses_grouped_values_and_preserves_token_at_download(self):
        server=(ROOT/"tools"/"run_web_v1_preview.py").read_text("utf-8")
        manual=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf-8")
        daily=(ROOT/"web_v1_static_preview"/"rph-today.js").read_text("utf-8")
        self.assertIn('if subject == "MATH":', server)
        self.assertIn('grouped_math_units(source_units)', server)
        self.assertIn('matched_math_tokens(', server)
        self.assertIn('tagged_math_lessons([', server)
        self.assertIn('list_native_lessons(year, subject, token)',server)
        self.assertIn('option.dataset.originUnit=String(item.origin_unit||"")',daily)
        self.assertIn('v.lesson.selectedOptions[0]?.dataset.originUnit||v.unit.value',daily)
        self.assertIn('opt.dataset.originUnit=el===lesson?String(item.origin_unit||""):""',manual)
        self.assertIn('function currentLessonSourceUnit()',manual)
        self.assertIn('unit:currentLessonSourceUnit(),lesson:lesson.value',manual)


if __name__ == "__main__":
    unittest.main()
