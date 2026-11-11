"""Proposals must stay staging-only, complete, and never revive held lessons."""
import unittest
from collections import Counter
from pi_pedagogy_review import generate
from pi_quality_audit import HELD


class PIPedagogyReviewTests(unittest.TestCase):
    def test_all_drafts_have_subject_specific_proposals_no_held(self):
        rows = generate()
        self.assertEqual(len(rows), 690)
        self.assertEqual(len({r["id"] for r in rows}), 690)
        self.assertEqual(len({r["domain"] for r in rows}), 7)
        for r in rows:
            self.assertNotIn((r["year"], r["lesson"]), HELD)
            self.assertEqual(r["approval"], "BELUM_DIUJI_BELUM_DILULUSKAN")
            self.assertIn("DRAF", r["note"])
            self.assertGreaterEqual(len(r["proposed_teacher_actions_rumi"]), 3)
            self.assertTrue(r["source_sp_jawi"].strip())
            self.assertTrue(r["existing_activity_jawi"].strip())

    def test_templates_different_by_domain_and_no_external_verses(self):
        r = generate()
        by_domain = {}
        for row in r:
            by_domain.setdefault(row["domain"], row["proposed_teacher_actions_rumi"])
        self.assertEqual(len({tuple(x) for x in by_domain.values()}), 7)
        self.assertTrue(all("sah" in x["note"] for x in r))
        self.assertEqual(Counter(row["domain"] for row in r)["Jawi"], 179)


if __name__ == "__main__":
    unittest.main()
