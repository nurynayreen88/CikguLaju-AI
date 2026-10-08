import unittest
from unittest.mock import patch
from pjpk_rph_composer_v2669 import compose_verified_pjpk_rph

class ComposerRefinementTests(unittest.TestCase):
    def sample(self, subject):
        return {
            "subject": subject, "year": "Tahun 4", "topic": "Imbangan",
            "sk_code": "1.1", "sk_text": "Standard kandungan ujian",
            "sp_code": "1.1.1", "sp_text": "Standard pembelajaran ujian",
            "_pjpk_activity_verified_v2666": True,
            "_pjpk_activity_phases_v2666": [
                ("Set Induksi", "Pengenalan"),
                ("Aktiviti 1", "Latihan"),
                ("Aktiviti 2", "Aplikasi"),
                ("Penutup", "Rumusan"),
            ],
        }

    def test_subject_specific_refinement(self):
        for subject in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
            with self.subTest(subject=subject):
                with patch("pjpk_rph_composer_v2669.prepare_pjpk_rph", return_value=self.sample(subject)):
                    result = compose_verified_pjpk_rph({}, lambda: None)
                self.assertIsNotNone(result)
                self.assertEqual(len(result["activities"]), 4)
                self.assertIn("1.1.1", result["objective"])
                self.assertIn("situasi" if subject == "Pendidikan Kesihatan" else "keselamatan", result["assessment"])

if __name__ == "__main__":
    unittest.main()
