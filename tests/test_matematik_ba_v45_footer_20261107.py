"""Evidence-only BA SP-footers audit for Matematik v45. No copyrighted page scans."""
import csv
import json
import re
from pathlib import Path
from collections import Counter
import unittest

ROOT = Path(__file__).resolve().parents[1] / "audits"

def read(name):
    with (ROOT/name).open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def bounds(s):
    numbers = [int(n) for n in re.findall(r"\d+", s)]
    return (numbers[0],numbers[-1])

class V45BAFooterTests(unittest.TestCase):
    def test_scanned_page_footer_index(self):
        data=read("matematik_v45_44_sp_footer_visual_20261107.csv")
        self.assertEqual(len(data),44)
        self.assertEqual(Counter(r["year"] for r in data),{"2":19,"3":25})
        self.assertEqual(len({(x["year"],x["ba_printed_page"]) for x in data}),44)
        for x in data:
            self.assertEqual(x["evidence"],"VISUAL_FOOTER_CODE")
            self.assertEqual(x["approval"],"PAGE_FOOTER_ONLY_NOT_EXERCISE_SIGNOFF")
            self.assertRegex(x["source_footer_SP_codes"],r"\d+\.\d+\.\d+")

    def test_48_refinements_only_narrow_existing_page_range(self):
        footers=read("matematik_v45_44_sp_footer_visual_20261107.csv")
        code_index={(x["year"],int(x["ba_printed_page"])):set(x["source_footer_SP_codes"].split(";")) for x in footers}
        rows=read("matematik_v45_48_ba_page_refinements_20261107.csv")
        self.assertEqual(len(rows),48)
        self.assertEqual(Counter(x["year"] for x in rows),{"2":29,"3":19})
        self.assertEqual(len({(x["year"],x["lesson"]) for x in rows}),48)
        for x in rows:
            old_a,old_b=bounds(x["old_printed_pages"])
            new_a,new_b=bounds(x["new_printed_pages"])
            self.assertLessEqual(old_a,new_a)
            self.assertLessEqual(new_b,old_b)
            self.assertLessEqual(new_a,new_b)
            self.assertNotEqual(x["old_printed_pages"],x["new_printed_pages"])
            self.assertTrue(any(x["sp"] in code_index.get((x["year"],p),set()) for p in range(new_a,new_b+1)))
            self.assertEqual(x["evidence"],"BA_PRINTED_FOOTER_SP_VISUAL")
            self.assertEqual(x["exercise_item_approved"],"NO")
            self.assertEqual(x["release_status"],"DRAFT")

    def test_v45_release_not_falsely_ready(self):
        gate=json.loads((ROOT/"matematik_v45_release_gate_20261107.json").read_text(encoding="utf-8"))
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["BA_page_footer_records_inspected"],44)
        self.assertEqual(gate["BA_reference_narrowed_lesson_count"],48)
        self.assertEqual(gate["technical_QA_585_pdf_A4"],585)
        self.assertEqual(gate["academic_exercise_items_approved"],0)
        self.assertFalse(gate["live_staging_telegram_web_tests"])
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])

if __name__ == "__main__":
    unittest.main()
