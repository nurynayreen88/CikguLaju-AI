"""A repaired historical worksheet becomes a manual-review candidate only."""
import json
import unittest
from pathlib import Path

from web.legacy_worksheet_quality_gate_20261112 import assess_legacy_blueprint


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "supplementary_materials/math/year1/repair_demo_sk1_1_sp1_1_1_20261112.json"


class MathY1WorksheetRepairDemoTests(unittest.TestCase):
    def test_original_six_pupil_items_never_become_public_automatically(self):
        data = json.loads(SAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(data["visibility"], "STAGING_INTERNAL")
        self.assertFalse(data["publish"])
        self.assertEqual(data["approval"], "NOT_APPROVED_FOR_PRODUCTION")
        self.assertEqual(data["curriculum"]["year"], 1)
        self.assertEqual(data["curriculum"]["subject"], "Matematik")
        self.assertEqual((data["curriculum"]["sk"], data["curriculum"]["sp"]),
                         ("1.1", "1.1.1"))
        self.assertIsNone(data["curriculum"]["lesson_token"])
        self.assertIsNone(data["curriculum"]["textbook_page"])
        self.assertEqual(len(data["student_copy"]["questions"]), 6)
        for i, q in enumerate(data["student_copy"]["questions"], 1):
            self.assertEqual(q["no"], i)
            self.assertGreater(q["group_a"], 0)
            self.assertGreater(q["group_b"], 0)
            self.assertTrue(q["task"].strip())
            self.assertNotIn("ANSWERSPACE", json.dumps(q).upper())
            self.assertNotIn("jawapan_betul", q)
        self.assertFalse(data["qa"]["teacher_approved"])
        self.assertFalse(data["qa"]["lesson_mapping_approved"])
        self.assertTrue(data["qa"]["no_public_routes"])

    def test_repair_is_a_review_candidate_not_automatically_ready(self):
        data = json.loads(SAMPLE.read_text(encoding="utf-8"))
        pupil = data["student_copy"]
        items = "\n".join(
            str(x["no"]) + ". " + x["task"] + " Kumpulan A: " +
            str(x["group_a"]) + " objek; Kumpulan B: " + str(x["group_b"]) +
            " objek."
            for x in pupil["questions"]
        )
        row = {
            "year_label": "Tahun 1", "subject": "Matematik",
            "sk_code": "1.1", "sp_code": "1.1.1",
            "title": pupil["title"], "instructions": pupil["instruction"],
            "question_pattern": items, "answer_space": "Ruang murid",
            "verified_alignment": 1,
        }
        outcome = assess_legacy_blueprint(row)
        self.assertEqual(outcome["status"], "REVIEW_REQUIRED")
        self.assertEqual(outcome["reasons"], [])
        self.assertFalse(outcome["public"])
        self.assertFalse(outcome["approved"])


if __name__ == "__main__":
    unittest.main()
