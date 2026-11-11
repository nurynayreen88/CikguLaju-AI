"""Pedagogical tests: do not touch Telegram, DB, user accounts or Render."""
import unittest
from tools.rph_mathematics_year3_curriculum_audit_20261109 import (
    audit_math_year3_wang as audit,
)


def rph(edition="DSKP2017"):
    original = edition == "DSKP2017"
    return {
        "year": 3, "subject": "MATEMATIK", "edition": edition,
        "class": "4 Ikhlas",  # Teacher's test choice, not a defect.
        "sk": "4.4 Darab wang" if original else "4.2 Darab dan bahagi wang",
        "sp": "4.4.1" if original else "4.2.1",
        "objective": "Murid selesaikan 4 daripada 5 soalan dengan tepat.",
        "criteria": "Sekurang-kurangnya 4/5 betul.",
        "duration_minutes": 60,
        "phases": [
            {"title": "Set Induksi", "minutes": 5, "teacher": "Tunjuk darab",
             "pupils": "Anggar wang"},
            {"title": "Aktiviti 1", "minutes": 10, "teacher": "Model darab 10",
             "pupils": "Jawab"},
            {"title": "Aktiviti 2", "minutes": 15, "teacher": "Bimbing darab 100 1000",
             "pupils": "Selesaikan"},
            {"title": "Aktiviti 3", "minutes": 15,
             "teacher": "Banding darab dan bahagi wang" if not original
                        else "Selesaikan masalah darab wang",
             "pupils": "Beri alasan"},
            {"title": "Aktiviti 4", "minutes": 10, "teacher": "PBD individu",
             "pupils": "Jawab sendiri"},
            {"title": "Penutup", "minutes": 5, "teacher": "Rumusan",
             "pupils": "Nyatakan satu strategi"},
        ],
    }


class TestMathYear3CurriculumAudit(unittest.TestCase):
    def test_two_legal_edition_paths_not_auto_released(self):
        for edition in ("DSKP2017", "EDISI3"):
            result = audit(rph(edition))
            self.assertEqual(result["issues"], [])
            self.assertEqual(result["status"], "EDITORIAL_REVIEW_REQUIRED")
            self.assertFalse(result["publication_ready"])

    def test_edisi3_requires_division_not_just_multiplication(self):
        record = rph("EDISI3")
        record["phases"][3]["teacher"] = "Selesaikan darab wang sahaja"
        self.assertIn("SP_OPERATION_COVERAGE_MISSING", audit(record)["issues"])

    def test_cross_edition_codes_are_not_silently_changed(self):
        record = rph("EDISI3")
        record["sk"] = "4.4"
        record["sp"] = "4.4.1"
        issues = audit(record)["issues"]
        self.assertIn("SK_EDITION_MISMATCH", issues)
        self.assertIn("SP_EDITION_MISMATCH", issues)
        self.assertEqual(record["sk"], "4.4")

    def test_uploaded_example_issues_and_class_test_not_flagged(self):
        record = rph()
        record["sk"] = "4.4 4.4"
        record["objective"] = (
            "Pada akhir pembelajaran, murid dapat menunjukkan pengetahuan "
            "atau kemahiran berdasarkan Standard Pembelajaran 4.4.1."
        )
        record["criteria"] = "Murid mencapai ketepatan yang ditetapkan."
        record["phases"][1]["minutes"] = 12
        record["phases"][2]["minutes"] = 18
        record["phases"][3]["minutes"] = 20
        record["phases"][4]["minutes"] = 5
        result = audit(record)
        self.assertTrue({
            "DUPLICATE_SK", "GENERIC_OBJECTIVE", "NO_MEASURABLE_CRITERION",
            "ACTIVITIES_EXCEED_OR_UNDERFILL_SLOT",
        }.issubset(result["issues"]))
        self.assertEqual(result["minutes"], 65)
        self.assertEqual(record["class"], "4 Ikhlas")

    def test_no_unverified_book_pages_or_missing_edition(self):
        record = rph()
        record["textbook_page"] = "35"
        self.assertIn("UNVERIFIED_TEXTBOOK_PAGE", audit(record)["issues"])
        record["textbook_page_proof"] = "book print page independently verified"
        self.assertNotIn("UNVERIFIED_TEXTBOOK_PAGE", audit(record)["issues"])
        record["edition"] = ""
        self.assertIn("CURRICULUM_EDITION_UNKNOWN", audit(record)["issues"])

    def test_other_years_and_subjects_do_not_inherit_this_mapping(self):
        record = rph()
        record["year"] = 5
        with self.assertRaises(ValueError):
            audit(record)
        record["year"] = 3
        record["subject"] = "SAINS"
        with self.assertRaises(ValueError):
            audit(record)

    def test_missing_teacher_pupil_and_negative_minutes(self):
        record = rph()
        record["phases"][0]["pupils"] = ""
        record["phases"][0]["minutes"] = -3
        result = audit(record)
        self.assertIn("TEACHER_PUPIL_ACTIONS_MISSING", result["issues"])
        self.assertIn("INVALID_PHASE", result["issues"])


if __name__ == "__main__":
    unittest.main()
