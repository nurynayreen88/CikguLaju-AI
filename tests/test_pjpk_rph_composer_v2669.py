"""PJPK v26.69 composer checks with simulated verified mapping."""
import unittest
from unittest.mock import patch
from pjpk_rph_composer_v2669 import compose_verified_pjpk_rph, render_verified_pjpk_text

class ComposerTests(unittest.TestCase):
    def sample(self, subject, year):
        return {"subject": subject, "year": str(year), "topic": "Imbangan" if subject == "Pendidikan Jasmani" else "Kebersihan Diri",
                "sk_code": "1.1", "sk_text": "Standard kandungan ujian",
                "sp_code": "1.1.1", "sp_text": "Standard pembelajaran ujian",
                "_pjpk_standards_complete_v2659": True}
    def test_twelve_subject_year_combinations(self):
        for subject in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
            for year in range(1, 7):
                s = self.sample(subject, year)
                with self.subTest(subject=subject, year=year):
                    with patch("pjpk_activity_adapter_v2666.enrich_pjpk_rph", return_value=s):
                        data = compose_verified_pjpk_rph(s, lambda: None)
                        self.assertIsNotNone(data)
                        self.assertEqual(len(data["activities"]), 4)
                        self.assertIn("1.1.1", data["sp"])
                        self.assertIn("refleksi", render_verified_pjpk_text(s, lambda: None).lower())
    def test_missing_mapping_no_rph(self):
        s = self.sample("Pendidikan Jasmani", 1)
        s["_pjpk_standards_complete_v2659"] = False
        with patch("pjpk_activity_adapter_v2666.enrich_pjpk_rph", return_value=s):
            self.assertIsNone(compose_verified_pjpk_rph(s, lambda: None))
    def test_unrelated_subject_no_rph(self):
        self.assertIsNone(compose_verified_pjpk_rph({"subject":"Matematik"}, lambda: None))

if __name__ == "__main__":
    unittest.main()
