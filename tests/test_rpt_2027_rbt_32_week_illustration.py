"""Optional RBT 2027 32-week SIMULASI; never a user-approved school schedule."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from scripts.build_rpt_2027_rbt_32_week_illustration import rbt_32_week_scenario, build_all
from scripts.build_rpt_2027_standard_preview import rbt_records


class RBT32WeekIllustrationQA(unittest.TestCase):
    def test_all_three_years_and_source_unchanged(self):
        master = load_calendar_weeks()
        for year in (4, 5, 6):
            with self.subTest(year=year):
                originals = rbt_records(year)
                rows = rbt_32_week_scenario(year)
                self.assertEqual(len(rows), 32)
                self.assertEqual([r["id"] for r in rows], [r["id"] for r in originals])
                for i, (a, b) in enumerate(zip(rows, originals), 3):
                    week = f"M{i:02d}"
                    self.assertEqual(a["week"], week + " (SIMULASI)")
                    self.assertEqual(a["schedule_status"], "EDITORIAL_ILLUSTRATION_NOT_APPROVED")
                    self.assertEqual((a["a_start"], a["a_end"]), master["A"][week])
                    self.assertEqual((a["b_start"], a["b_end"]), master["B"][week])
                    for field in ("id", "unit", "topic", "sk", "sp", "sk_display", "sp_display"):
                        self.assertEqual(a[field], b[field])
                    self.assertEqual(a["original_week"], "")
                    self.assertEqual(a["original_a_start"], "")
                    self.assertEqual(a["original_b_start"], "")
                    self.assertEqual(a["source_note"], b["note"])
                    self.assertIn("SIMULASI SAHAJA", a["note"])
                    self.assertIn("BUKAN", a["note"].upper())
                self.assertTrue(all(
                    not item.get("week") and not item.get("a_start") and
                    not item.get("b_start") for item in originals
                ), "Original RBT source week/date must not be mutated")

    def test_start_week_is_editable_but_bounded(self):
        rows = rbt_32_week_scenario(4, start_week=10)
        self.assertEqual(rows[0]["week"], "M10 (SIMULASI)")
        self.assertEqual(rows[-1]["week"], "M41 (SIMULASI)")
        for start in (0, 14, -5, 45):
            with self.assertRaises(ValueError):
                rbt_32_week_scenario(4, start_week=start)
        with self.assertRaises(ValueError):
            rbt_32_week_scenario(3)

    def test_pdf_examples_are_separate_and_have_only_cover_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            built = build_all(Path(temp))
            self.assertEqual(len(built), 3)
            for year, count, path in built:
                self.assertEqual(count, 32)
                self.assertIn("SIMULASI_BUKAN_FINAL", path.name)
                self.assertTrue(path.exists())
                reader = PdfReader(str(path))
                first = reader.pages[0].extract_text()
                text = "\n".join(page.extract_text() for page in reader.pages[1:])
                for phrase in ("NAMA GURU", "NAMA SEKOLAH", "LOGO SEKOLAH"):
                    self.assertIn(phrase, first)
                self.assertIn("M03 (SIMULASI)", text)
                self.assertIn("M34 (SIMULASI)", text)
                self.assertIn("bukan tarikh kelas sebenar", " ".join(text.split()))
                self.assertIn("1.1" if year == 4 else "4.3" if year == 5 else "5.2", text)


if __name__ == "__main__":
    unittest.main()
