"""Non-release staging checkpoint guard; never touches runtime, DB, or Telegram."""
import json
import unittest
from pathlib import Path

CHECKPOINT = (
    Path(__file__).resolve().parents[1]
    / "audits/pendidikan_islam_2027_t2_t6_stage_gate_20261105.json"
)


class TestPendidikanIslamStagingCheckpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CHECKPOINT.read_text(encoding="utf-8"))

    def test_total_by_year(self):
        expected = {"2": 112, "3": 147, "4": 151, "5": 143, "6": 143}
        self.assertEqual(self.data["scope"]["rph_by_year"], expected)
        self.assertEqual(sum(expected.values()), self.data["scope"]["rph_total"])
        self.assertEqual(self.data["scope"]["rpt_word"], 5)

    def test_release_is_locked(self):
        self.assertEqual(self.data["status"], "DRAF_BELUM_READY")
        self.assertEqual(self.data["branch_policy"], "STAGING_ONLY")
        self.assertFalse(any(self.data["release_controls"].values()))

    def test_exactly_35_risky_lessons_and_no_overlap(self):
        self.assertEqual(self.data["qa_counts"], {
            "CALON_UJIAN_GURU_DRAF": 661,
            "SEMAKAN_KEUTAMAAN": 29,
            "TAHAN_SEMAKAN_KANDUNGAN": 6,
        })
        self.assertEqual(sum(self.data["qa_counts"].values()), 696)
        held = {tuple(p) for p in self.data["held"]}
        priority = {tuple(p) for p in self.data["priority"]}
        self.assertEqual(len(held), 6)
        self.assertEqual(len(priority), 29)
        self.assertFalse(held & priority)
        self.assertEqual(held, {
            ("2", "035"),
            ("6", "006"), ("6", "014"), ("6", "018"),
            ("6", "060"), ("6", "117"),
        })

    def test_structural_pass_not_misrepresented_as_semantic_pass(self):
        results = self.data["qa_verified"]
        self.assertEqual(results["unique_lesson_ids"], 696)
        self.assertEqual(results["word_docx_integrity"], 696)
        self.assertEqual(results["a4_layout_xml"], 696)
        self.assertEqual(results["rtl_markup_xml"], 696)
        self.assertEqual(results["rendered_one_page_samples"], 5)
        self.assertGreaterEqual(len(self.data["qa_not_verified"]), 4)


if __name__ == "__main__":
    unittest.main()
