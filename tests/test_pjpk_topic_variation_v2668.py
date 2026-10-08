"""Regression checks for PJPK v26.68 topic-sensitive planning."""
import unittest
from pjpk_activity_planner_v2665 import build_pjpk_activities

class TopicVariationTests(unittest.TestCase):
    def sample(self, subject, topic, year):
        return {"subject": subject, "topic": topic, "year": year,
                "sk_code": "1.1", "sk_text": "Standard kandungan sah",
                "sp_code": "1.1.1", "sp_text": "Standard pembelajaran sah",
                "_pjpk_standards_complete_v2659": True}

    def test_both_subjects_all_years(self):
        for year in range(1, 7):
            for subject in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
                with self.subTest(year=year, subject=subject):
                    phases = build_pjpk_activities(self.sample(subject, "Keselamatan", year))
                    self.assertEqual(len(phases), 4)
                    self.assertTrue(all(a and b for a,b in phases))

    def test_pj_variation(self):
        balance = str(build_pjpk_activities(self.sample("Pendidikan Jasmani", "Imbangan", 2)))
        throwing = str(build_pjpk_activities(self.sample("Pendidikan Jasmani", "Baling Bola", 2)))
        self.assertNotEqual(balance, throwing)
        self.assertIn("imbangan", balance.lower())
        self.assertIn("bola", throwing.lower())

    def test_pk_variation(self):
        hygiene = str(build_pjpk_activities(self.sample("Pendidikan Kesihatan", "Kebersihan Diri", 4)))
        emotions = str(build_pjpk_activities(self.sample("Pendidikan Kesihatan", "Pengurusan Emosi", 4)))
        self.assertNotEqual(hygiene, emotions)
        self.assertIn("kebersihan", hygiene.lower())
        self.assertIn("emosi", emotions.lower())

    def test_unverified_rejected(self):
        sample = self.sample("Pendidikan Jasmani", "Lari Pantas", 1)
        sample["_pjpk_standards_complete_v2659"] = False
        self.assertIsNone(build_pjpk_activities(sample))

if __name__ == "__main__":
    unittest.main()
