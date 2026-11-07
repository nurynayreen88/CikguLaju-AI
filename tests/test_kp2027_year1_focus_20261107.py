"""Year-1-only KP2027 editorial safeguard. No official standards or live access."""
import json
from pathlib import Path
import unittest

DATA = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "year1" / "candidate_rph_year1_24_20261107.json"

class Year1KP2027DraftTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_only_year1_and_eight_candidate_subjects(self):
        self.assertEqual(self.data["level"], "Tahun 1")
        self.assertEqual(self.data["release_status"], "DRAFT_HOLD_NOT_READY")
        rows = self.data["records"]
        self.assertEqual(len(rows), 24)
        self.assertEqual(len({r["id"] for r in rows}), 24)
        groups = {}
        for r in rows:
            self.assertEqual(r["level"], "Tahun 1")
            groups.setdefault(r["subject"], set()).add(r["sequence_candidate"])
        self.assertEqual(len(groups), 8)
        self.assertTrue(all(values == {1,2,3} for values in groups.values()))

    def test_never_publish_candidate_rph_as_official(self):
        self.assertTrue(self.data["policy"]["no_legacy_kssr_content"])
        for r in self.data["records"]:
            with self.subTest(rph=r["id"]):
                self.assertEqual(r["readiness"], "DRAFT_HOLD_NOT_READY")
                for key in ("official_sk", "official_sp", "official_spi", "official_page"):
                    self.assertIsNone(r[key])
                for key in ("approved_by_teacher", "approved_for_web", "approved_for_telegram", "rpt_scheduled"):
                    self.assertIs(r[key], False)
                self.assertEqual(r["curriculum_alignment"], "TO_VERIFY_AGAINST_ORIGINAL_DK")

    def test_subject_specific_activities_and_evidence(self):
        phases = ("Set induksi","Aktiviti 1","Aktiviti 2","Pengukuhan/PBD dan penutup")
        for r in self.data["records"]:
            with self.subTest(rph=r["id"]):
                self.assertTrue(r["objective_candidate"].strip())
                self.assertTrue(r["materials"])
                self.assertTrue(r["formative_assessment"].strip())
                self.assertTrue(r["differentiation"].strip())
                self.assertTrue(r["character_values"])
                self.assertEqual(tuple(s["phase"] for s in r["stages"]), phases)
                for step in r["stages"]:
                    self.assertGreater(len(step["teacher_action"]), 25)
                    self.assertGreater(len(step["pupil_action"]), 25)

if __name__ == "__main__":
    unittest.main()
