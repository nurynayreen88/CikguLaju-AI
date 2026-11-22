"""KP2027 editorial pilot validation: candidates must never masquerade as official standards."""
import json
from pathlib import Path
import unittest

SRC = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "candidate_rph_batch_20261107.json"


class KP2027CandidateDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SRC.read_text(encoding="utf-8"))

    def test_count_and_subject_scope(self):
        items = self.data["records"]
        self.assertEqual(len(items), 24)
        self.assertEqual(self.data["release_status"], "DRAFT_HOLD_NOT_READY")
        self.assertEqual(len({x["id"] for x in items}), 24)
        groups = {}
        for row in items:
            groups.setdefault((row["level"], row["subject"]), set()).add(row["sequence_candidate"])
        self.assertEqual(len(groups), 8)
        self.assertEqual(len([k for k in groups if k[0] == "Tahun 1"]), 5)
        self.assertEqual(len([k for k in groups if k[0] == "Tingkatan 1"]), 3)
        self.assertTrue(all(seq == {1, 2, 3} for seq in groups.values()))

    def test_no_official_claims_or_runtime_release(self):
        for row in self.data["records"]:
            with self.subTest(id=row["id"]):
                for key in ("official_sk", "official_sp", "official_spi", "official_page"):
                    self.assertIsNone(row[key])
                self.assertEqual(row["curriculum_alignment"], "TO_VERIFY_AGAINST_ORIGINAL_DK")
                self.assertEqual(row["content_type"], "ORIGINAL_EDITORIAL_TEACHER_DRAFT")
                self.assertEqual(row["readiness"], "DRAFT_HOLD_NOT_READY")
                for key in ("approved_by_teacher", "approved_for_web", "approved_for_telegram", "rpt_scheduled"):
                    self.assertIs(row[key], False)

    def test_each_candidate_has_teaching_and_assessment(self):
        expected = ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Pengukuhan/PBD dan penutup")
        for row in self.data["records"]:
            with self.subTest(id=row["id"]):
                self.assertTrue(row["objective_candidate"].strip())
                self.assertEqual(row["minutes"], 60)
                self.assertGreaterEqual(len(row["materials"]), 3)
                self.assertTrue(row["formative_assessment"].strip())
                self.assertTrue(row["differentiation"].strip())
                self.assertGreaterEqual(len(row["character_values"]), 1)
                self.assertEqual(tuple(s["phase"] for s in row["stages"]), expected)
                for stage in row["stages"]:
                    self.assertTrue(stage["teacher_action"].startswith("Guru"))
                    self.assertTrue(stage["pupil_action"].startswith("Murid"))
                    self.assertGreater(len(stage["teacher_action"]), 25)
                    self.assertGreater(len(stage["pupil_action"]), 25)
                self.assertTrue(row["source_index_url"].startswith("https://sites.google.com/"))


if __name__ == "__main__":
    unittest.main()
