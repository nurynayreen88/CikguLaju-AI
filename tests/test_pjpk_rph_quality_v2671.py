"""Regression tests for PJPK RPH content; no DB writes or deployment."""
import unittest
from unittest.mock import patch
from pjpk_rph_composer_v2669 import compose_verified_pjpk_rph

class TestPJPKRPHQuality(unittest.TestCase):
    def test_unverified_selection_fails_closed(self):
        with patch("pjpk_rph_composer_v2669.prepare_pjpk_rph", return_value={}):
            self.assertIsNone(compose_verified_pjpk_rph({}, lambda: None))

    def test_incomplete_phases_fail_closed(self):
        selection = {"_pjpk_activity_verified_v2666": True,
                     "_pjpk_activity_phases_v2666": [("Set Induksi", "Pengenalan")]}
        with patch("pjpk_rph_composer_v2669.prepare_pjpk_rph", return_value=selection):
            self.assertIsNone(compose_verified_pjpk_rph({}, lambda: None))

    def test_verified_rph_has_required_sections(self):
        selection = {
            "_pjpk_activity_verified_v2666": True,
            "_pjpk_activity_phases_v2666": [
                ("Set Induksi", "Pengenalan selamat"),
                ("Aktiviti 1 – Latihan", "Murid mencuba kemahiran"),
                ("Aktiviti 2 – Aplikasi", "Murid mengaplikasikan kemahiran"),
                ("Penutup", "Guru menilai penguasaan"),
            ],
            "subject": "Pendidikan Jasmani", "year": "Tahun 4",
            "topic": "Imbangan", "sk_code": "1.1", "sk_text": "Kemahiran asas",
            "sp_code": "1.1.1", "sp_text": "Melakukan imbangan",
        }
        with patch("pjpk_rph_composer_v2669.prepare_pjpk_rph", return_value=selection):
            rph = compose_verified_pjpk_rph({}, lambda: None)
        self.assertIsNotNone(rph)
        self.assertEqual(len(rph["activities"]), 4)
        self.assertIn("Melakukan imbangan", rph["objective"])
        self.assertTrue(rph["source_verified"])

if __name__ == "__main__":
    unittest.main()
