"""KP2027 Year 1 training evidence gate; advisory source discovery is not final DK validation."""
import json
from pathlib import Path
import re
import unittest

BASE = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "year1"


def data(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


class KP2027Year1EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = data("year1_editorial_master_36_20261107_v2.json")
        cls.bm = data("bm_year1_training_sp_page_index_20261107.json")
        cls.math = data("math_year1_training_30_codes_20261107.json")

    def test_unique_year1_only_and_hard_hold(self):
        records = self.master["records"]
        self.assertEqual(len(records), 36)
        self.assertEqual(len({r["id"] for r in records}), 36)
        self.assertEqual(self.master["release_status"], "DRAFT_HOLD_NOT_READY")
        counts = {}
        for row in records:
            with self.subTest(row=row["id"]):
                self.assertEqual(row["level"], "Tahun 1")
                counts[row["subject"]] = counts.get(row["subject"], 0) + 1
                self.assertEqual(row["readiness"], "DRAFT_HOLD_NOT_READY")
                for key in ("official_sk", "official_sp", "official_spi", "official_page"):
                    self.assertIsNone(row[key])
                for key in ("approved_by_teacher", "approved_for_web", "approved_for_telegram", "rpt_scheduled"):
                    self.assertIs(row[key], False)
        self.assertEqual(len(counts), 8)
        for k in ("Alam dan Manusia", "Bahasa Melayu", "Matematik"):
            self.assertEqual(counts[k], 7)
        for k in ("Pendidikan Islam", "Bahasa Arab", "Bahasa Inggeris", "Pendidikan Moral", "Pendidikan Jasmani dan Kesihatan"):
            self.assertEqual(counts[k], 3)

    def test_math_deferred_topics_replaced_and_period_corrected(self):
        records = {r["id"]: r for r in self.master["records"]}
        math = [r for r in records.values() if r["subject"] == "Matematik"]
        self.assertEqual(len(math), 7)
        self.assertTrue(all(r["minutes"] == 30 for r in math))
        forbidden = re.compile(r"pola|tertib bilangan|rangkaian|pecahan|nilai tempat|membundar|tambah berulang|tolak berturut", re.I)
        for row in math:
            self.assertIsNone(forbidden.search(row["title"]))
        self.assertIn("bentuk dua dimensi", records["KP27-Y1-MT-C03"]["title"].lower())
        self.assertIn("wang", records["KP27-Y1-MT-C07"]["title"].lower())
        self.assertEqual(len(self.master["curriculum_risk_fix"]["fixed_record_ids"]), 3)

    def test_bm_training_pdf_sp_index_is_unapproved(self):
        self.assertEqual(len(self.bm["code_page_index"]), 26)
        self.assertEqual(len({r["code"] for r in self.bm["code_page_index"]}), 26)
        self.assertFalse(self.bm["source"]["source_is_final_subject_DK"])
        self.assertFalse(self.bm["source"]["official_subject_standards_verified"])
        self.assertEqual(self.bm["source"]["pdf_page_count"], 118)
        self.assertEqual(self.bm["source"]["sha256"], "447b499db78253c4c3f0559afa791691a010c58d076666917a060531b9637691")
        for r in self.bm["code_page_index"]:
            self.assertFalse(r["exact_official_document_validated"])
            self.assertFalse(r["standard_text_verified_against_final_dk"])
            self.assertTrue(all(1 <= n <= 118 for n in r["pdf_pages_one_based"]))
        for row in self.bm["preliminary_rph_crosswalk"]:
            self.assertFalse(row["teacher_approved"])
            self.assertTrue(all(code in {r["code"] for r in self.bm["code_page_index"]} for code in row["suggested_codes"]))

    def test_math_training_codes_and_provenance_are_limited(self):
        self.assertEqual(len(self.math["training_codes"]), 30)
        self.assertEqual(len({r["code"] for r in self.math["training_codes"]}), 30)
        self.assertFalse(self.math["training_metrics"]["official_dk_text_verified"])
        self.assertEqual(self.math["training_metrics"]["topic_count"], 7)
        self.assertEqual(self.math["training_metrics"]["periods_per_week"], 7)
        self.assertEqual(self.math["training_metrics"]["minutes_per_period"], 30)
        self.assertTrue(self.math["live_release_blocked"])
        for row in self.math["training_codes"]:
            self.assertFalse(row["approved"])
            self.assertIsNone(row["exact_text"])
            self.assertIsNone(row["original_dk_page"])


if __name__ == "__main__":
    unittest.main()
