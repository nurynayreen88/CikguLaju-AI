"""Fail-closed guard: KP2027 PI Year1 may not be published from training slides.

Only validates local audit metadata. No downloaded DK or private material in CI.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "kp2027_pi_t1_7_bidang_training_source_qa_20261123.json"

class KP2027PISourceGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_trainings_are_not_primary_dk(self):
        x = self.data
        self.assertEqual(x["status"], "QA_SOURCE_ONLY_NOT_READY")
        self.assertFalse(x["approved_to_publish"])
        self.assertFalse(x["training_source"]["is_primary_curriculum_document"])
        self.assertEqual(x["sp_codes_validated"], 0)

    def test_exact_seven_domains_nine_subfields(self):
        x = self.data
        self.assertEqual([d["name"] for d in x["domains"]], [
            "Al-Quran","Hadis","Akidah","Fiqah","Akhlak dan Tasawuf","Sirah","Jawi"])
        self.assertEqual(x["domain_count"], 7)
        self.assertEqual(x["subfield_count"], 9)
        codes = [c for d in x["domains"] for c in d["subfield_codes"]]
        self.assertEqual(codes, ["1.1","1.2","2.1","3.1","4.1","4.2","5.1","6.1","7.1"])
        self.assertTrue(all(len(c.split(".")) == 2 for c in codes),
                        "Do not mislabel subfields as Standard Pembelajaran codes")

    def test_primary_dk_metadata_is_not_content_approval(self):
        for key in ("official_dk_candidate","official_ppki_dk_candidate"):
            doc = self.data[key]
            self.assertTrue(doc["metadata_verified"])
            self.assertFalse(doc["pdf_text_verified"])
            self.assertEqual(doc["last_download_error"], "403")
            self.assertEqual(doc["status"], "FOUND_NOT_READ")
            self.assertTrue(doc["source_page"].startswith(
                "https://sites.google.com/moe-dl.edu.my/"))

    def test_suggested_six_periods_not_final(self):
        time = self.data["time_allocation"]
        self.assertEqual(time["suggested_periods_per_week"], 6)
        self.assertFalse(time["is_final"])
        self.assertEqual(time["source_page"], 51)

    def test_qa_files_owner_only(self):
        for ref in self.data["qa_files"].values():
            if isinstance(ref, str) and "drive" in ref:
                self.assertNotIn("http", ref)
        self.assertTrue(self.data["qa_files"]["visually_checked"])

if __name__ == "__main__":
    unittest.main()
