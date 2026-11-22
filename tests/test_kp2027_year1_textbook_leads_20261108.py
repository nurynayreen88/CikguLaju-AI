"""KP2027 Year-1 textbook leads must never be mistaken for verified files or final catalog."""
import json
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "year1" / "textbook_2027_spbt_unverified_catalog_leads_20261108.json"

class KP2027Year1BookLeadsGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))

    def test_eight_subjects_have_source_provenance_and_no_live_book_mapping(self):
        d = self.data
        self.assertEqual(d["release_status"], "TITLE_CODE_LEAD_ONLY_NOT_VERIFIED")
        self.assertEqual(d["school_stream"], "SK")
        self.assertEqual(d["basis"]["year_for_use"], 2027)
        self.assertIn("SECONDARY_TRANSCRIPT", d["basis"]["kind"])
        self.assertEqual(len(d["items"]), 8)
        self.assertEqual(len({x["subject"] for x in d["items"]}), 8)
        for x in d["items"]:
            with self.subTest(subject=x["subject"]):
                self.assertTrue(x["candidate_textbook_code"])
                self.assertTrue(x["candidate_activity_book_code"])
                self.assertFalse(x["original_copy_acquired"])
                self.assertIsNone(x["original_copy_sha256"])
                self.assertEqual(x["pages_mapped"], 0)
                self.assertFalse(x["subject_dk_sp_mapping_verified"])
                self.assertEqual(x["approval_status"], "REFERENCE_LEAD_ONLY")

    def test_conflicting_math_activity_book_code_remains_unresolved(self):
        d = self.data
        math = next(x for x in d["items"] if x["subject"] == "Matematik SK")
        self.assertEqual(math["candidate_textbook_code"], "BT081007")
        self.assertEqual(math["candidate_activity_book_code"], "BA081005")
        issue = d["conflicts"][0]
        self.assertEqual(issue["candidate_from_2027_spbt_presentation"], "BA081005")
        self.assertEqual(issue["observed_in_schools_2026_statement"], "BA081009")
        self.assertIn("REQUIRE_AUTHENTIC", issue["resolution"])

    def test_no_kssr_fallback_or_unverified_pdf_downloads(self):
        policy = self.data["book_publishing_policy"]
        self.assertTrue(all(policy.values()))
        self.assertEqual(len(self.data["additional_variants"]), 3)
        self.assertIn("Tahun 4", self.data["nonrelevant_potential_hit"]["reason"])
        self.assertIn("Tingkatan 3", self.data["nonrelevant_potential_hit"]["reason"])

if __name__ == "__main__":
    unittest.main()
