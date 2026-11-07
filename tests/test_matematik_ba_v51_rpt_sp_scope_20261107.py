"""Matematik v51: full RPT 2027 v28 crosswalk, source-scoped RPH fixes, no false release.
These tests verify indexed evidence/metadata, not individual textbook exercise approval.
"""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path
from rph_standalone.matematik import staging_preview_v51

ROOT=Path(__file__).resolve().parents[1] / "audits"
def rows(filename):
    with (ROOT/filename).open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

class V51CrosswalkGate(unittest.TestCase):
    def test_585_lesson_and_sp_codes_identical_across_rpt_and_rph(self):
        data=rows("matematik_v51_585_rpt2027_vs_rph_20261107.csv")
        self.assertEqual(len(data),585)
        self.assertEqual(Counter(x["year"] for x in data), {str(y):117 for y in range(2,7)})
        self.assertEqual(len({(x["year"],x["lesson"]) for x in data}),585)
        for x in data:
            with self.subTest(y=x["year"],lesson=x["lesson"]):
                self.assertEqual(x["rpt_lessons_found"],"1")
                self.assertEqual(x["rph_sp"],x["rpt_sp"])
                self.assertEqual(x["match"],"MATCH")
                self.assertTrue(x["rpt_page"])

    def test_585_week_links_consistent_with_44_week_schedule(self):
        weeks=rows("matematik_v51_585_rpt_week_vs_rph_20261107.csv")
        self.assertEqual(len(weeks),585)
        for x in weeks:
            self.assertEqual(x["match"],"True")
            self.assertEqual(x["rpt_week"],x["rph_week"])
            self.assertGreaterEqual(int(x["rpt_week"]),1)
            self.assertLessEqual(int(x["rpt_week"]),44)

    def test_16_rph_50_sections_are_source_scoped(self):
        changes=rows("matematik_v51_16_rph_sp_objektif_aktiviti_semakan_20261107.csv")
        self.assertEqual(len(changes),50)
        lesson_keys={(x["year"],x["lesson"]) for x in changes}
        self.assertEqual(len(lesson_keys),16)
        self.assertEqual(Counter(y for y,n in lesson_keys),{"3":2,"4":8,"5":6})
        self.assertEqual(sum(x["section"]=="SP" for x in changes),16)
        for x in changes:
            with self.subTest(year=x["year"],lesson=x["lesson"],section=x["section"]):
                self.assertNotEqual(x["old"],x["new"])
                self.assertRegex(x["primary_source"],r"DSKP Matematik Tahun [3-5], PDF page \d+")
                self.assertEqual(x["signoff"],"PENDING")
        self.assertTrue(any(x["year"]=="5" and x["lesson"]=="57" and
           x["section"]=="Aktiviti 1" and "1 hari 2 jam" in x["new"] for x in changes))
        self.assertTrue(any(x["year"]=="5" and x["lesson"]=="70" and
           x["section"]=="Aktiviti 2" and "3/4 km" in x["new"] for x in changes))
        self.assertTrue(any(x["year"]=="4" and x["lesson"]=="18" and
           x["section"]=="SP" and "darab dan bahagi" in x["new"] for x in changes))

    def test_release_gate_remains_staging_only(self):
        gate=json.loads((ROOT/"matematik_v51_release_gate_20261107.json").read_text(encoding="utf-8"))
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["changed_lessons_total"],16)
        self.assertEqual(gate["changed_sections"],50)
        self.assertEqual(gate["unchanged_lessons"],569)
        self.assertEqual(gate["rpt_lesson_sp_matches"],585)
        self.assertEqual(gate["rpt_week_matches"],585)
        self.assertEqual(gate["PDF_A4_one_page"],585)
        self.assertEqual(gate["rpt_source_version"].split()[-2:],["v28","SEMENTARA"])
        self.assertEqual(gate["academic_signoffs_for_all_585"],0)
        self.assertFalse(gate["academic_exercise_item_verification_all_completed"])
        self.assertFalse(gate["year4_34_split_paired_books_fully_reviewed"])
        self.assertFalse(gate["telegram_web_real_staging_e2e_passed"])
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])
        self.assertEqual(staging_preview_v51.EXPECTED_SHA256,gate["archive_sha256"])

if __name__=="__main__":
    unittest.main()
