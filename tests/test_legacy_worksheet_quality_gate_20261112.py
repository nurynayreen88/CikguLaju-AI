"""Historical worksheet sources must not enter live materials because of generic placeholders."""
import unittest
from web.legacy_worksheet_quality_gate_20261112 import assess_legacy_blueprint


BASE = {
    "year_label": "Tahun 1", "subject": "Matematik",
    "sk_code": "1.1", "sp_code": "1.1.1",
    "title": "Aras 1", "instructions": "Jawab semua soalan.",
    "question_pattern": (
        "Lengkapkan item asas berkaitan Nombor Bulat hingga 100. "
        "Tunjukkan jawapan pada ruang yang disediakan. [ANSWERSPACE: 2]"
    ),
    "answer_space": "2", "verified_alignment": 1,
}


class LegacyWorksheetQualityGateTests(unittest.TestCase):
    def test_old_template_is_not_an_actual_pupil_exercise(self):
        result = assess_legacy_blueprint(BASE)
        self.assertEqual(result["status"], "REPAIR_REQUIRED")
        self.assertIn("INSTRUCTION_TO_GENERATOR", result["reasons"])
        self.assertIn("RENDER_PLACEHOLDER", result["reasons"])
        self.assertIn("GENERIC_LEVEL_TITLE", result["reasons"])
        self.assertIn("NO_EXPLICIT_ITEM_SEQUENCE", result["reasons"])
        self.assertFalse(result["public"])
        self.assertFalse(result["approved"])

    def test_explicit_complete_items_still_require_human_release(self):
        obj = dict(BASE)
        obj.update(title="Mengira objek dalam lingkungan 10",
                   question_pattern=(
                       "1. Kira lima bintang yang dilukis oleh guru. "
                       "Tulis bilangannya pada petak di sebelah.\n"
                       "2. Kira tujuh titik pada kad. Tulis nombor yang mewakili "
                       "bilangan titik tersebut dan terangkan jawapan kamu."
                   ))
        result = assess_legacy_blueprint(obj)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["reasons"], [])
        self.assertFalse(result["public"])
        self.assertFalse(result["approved"])

    def test_secondary_and_unknown_subject_are_not_primary(self):
        for change in ({"year_label": "Tingkatan 1"},
                       {"year_label": "Year 7"},
                       {"subject": "Physics"},
                       {"year_label": "Tahun 9"}):
            with self.subTest(change=change):
                result = assess_legacy_blueprint({**BASE, **change})
                self.assertIn("OUTSIDE_PRIMARY_SCOPE", result["reasons"])
                self.assertFalse(result["public"])

    def test_curriculum_verified_does_not_mean_question_verified(self):
        result = assess_legacy_blueprint({**BASE, "verified_alignment": 1})
        self.assertEqual(result["status"], "REPAIR_REQUIRED")
        self.assertFalse(result["approved"])
        result = assess_legacy_blueprint({**BASE, "verified_alignment": 0})
        self.assertIn("CURRICULUM_ALIGNMENT_UNCONFIRMED", result["reasons"])

    def test_missing_fields_and_malformed_record_fail_closed(self):
        self.assertIn("INVALID_RECORD", assess_legacy_blueprint(None)["reasons"])
        self.assertIn("MISSING_SP_CODE",
                      assess_legacy_blueprint({**BASE, "sp_code": ""})["reasons"])
        self.assertFalse(assess_legacy_blueprint({})["public"])


if __name__ == "__main__":
    unittest.main()
