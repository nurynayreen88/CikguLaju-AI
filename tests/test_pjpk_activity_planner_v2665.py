"""PJPK v26.65 activity planner tests (no production DB)."""
import unittest
from pjpk_activity_planner_v2665 import build_pjpk_activities, format_pjpk_activities

class PlannerTests(unittest.TestCase):
    def selection(self, subject, year):
        return dict(subject=subject,year=year,topic="Pergerakan Selamat",
                    sk_code="1.1",sk_text="Standard disahkan",
                    sp_code="1.1.1",sp_text="Melakukan kemahiran disahkan",
                    _pjpk_standards_complete_v2659=True)
    def test_six_years_both_subjects(self):
        for year in range(1,7):
            for subject in ("Pendidikan Jasmani","Pendidikan Kesihatan"):
                with self.subTest(year=year,subject=subject):
                    phases=build_pjpk_activities(self.selection(subject,year))
                    self.assertEqual(len(phases),4)
                    self.assertTrue(all(title and body for title,body in phases))
    def test_missing_verified_mapping_rejected(self):
        s=self.selection("Pendidikan Jasmani",1)
        s["_pjpk_standards_complete_v2659"]=False
        self.assertIsNone(format_pjpk_activities(s))
    def test_unrelated_subject_rejected(self):
        self.assertIsNone(build_pjpk_activities(self.selection("Matematik",2)))
    def test_missing_sp_rejected(self):
        s=self.selection("Pendidikan Kesihatan",3)
        s["sp_text"]=""
        self.assertIsNone(build_pjpk_activities(s))

if __name__=="__main__":
    unittest.main()
