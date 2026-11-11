"""Matematik v55: Year3 intro change ledger, source grounding and strict RPH-only release gate."""
import csv,json,unittest
from pathlib import Path
from rph_standalone.matematik import staging_preview_v55 as preview

A=Path(__file__).resolve().parents[1]/"audits"
class Year3V55(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (A/"matematik_v55_98_set_induksi_T3_RPH_sahaja_20261107.csv").open(encoding="utf-8",newline="") as f:
            cls.rows=list(csv.DictReader(f))
    def test_98_unique_intros_derived_from_activity_one(self):
        self.assertEqual(len(self.rows),98)
        self.assertEqual(len({r["lesson_id"] for r in self.rows}),98)
        self.assertEqual(len({r["after"] for r in self.rows}),98)
        self.assertEqual({r["year"] for r in self.rows},{"3"})
        self.assertEqual({r["section"] for r in self.rows},{"Set induksi (5 minit)"})
        for r in self.rows:
            with self.subTest(id=r["lesson_id"]):
                self.assertNotEqual(r["before"],r["after"])
                self.assertIn("mengaitkannya dengan tajuk",r["before"])
                self.assertNotIn("mengaitkannya dengan tajuk",r["after"])
                self.assertTrue(85<len(r["after"])<150)
                self.assertTrue(r["after"].startswith("Guru "))
                self.assertTrue(r["after"].endswith("."))
                self.assertTrue(r["source_activity_1"])
                self.assertEqual(r["review"],"RPH_ACT1_ANCHORED_NO_FORMAL_TEACHER_SIGNOFF")
    def test_sha_pinned_585_RPH_no_rpt_no_live(self):
        gate=json.loads((A/"matematik_v55_release_gate_RPH_only_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["archive_sha256"],"3913f179aa5690b8c2b550c5cb65c87aac16157f38db9f1001cb9c2fa9784d7e")
        self.assertEqual(preview.EXPECTED_SHA256,gate["archive_sha256"])
        self.assertEqual(gate["rph_count"],585)
        self.assertEqual(gate["year3_count"],117)
        self.assertEqual(gate["modified_rph_count"],98)
        self.assertEqual(gate["unchanged_rph_count"],487)
        self.assertEqual(gate["pdf_a4_one_page_count"],585)
        self.assertEqual(gate["merged_year3_page_count"],117)
        self.assertEqual(gate["BA_year2_3_ref_count"],234)
        self.assertEqual(gate["formal_academic_teacher_signoff_count"],0)
        for k in ("rpt_changed","production_modified","final_ready","real_telegram_web_staging_e2e"):
            self.assertIs(gate[k],False)
if __name__=="__main__":
    unittest.main()
