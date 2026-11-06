"""Regression checks for isolated Pendidikan Islam staging QA."""
import unittest
from pi_quality_audit import audit, HELD, COUNT


class PIQualityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_no_loss_no_release_no_fake_score(self):
        r = self.result
        self.assertEqual(r["total"], sum(COUNT.values()))
        self.assertEqual(r["drafts"], 690)
        self.assertEqual(r["held"], 6)
        self.assertEqual(r["release"], "NO_GO")
        self.assertIsNone(r["quality_score_percent"])
        self.assertIs(r["quality_80_certified"], False)

    def test_numbering_fixed_without_unlocking_holds(self):
        flags = self.result["flags"]
        self.assertNotIn("NOMBOR_AKTIVITI_TIDAK_BERMULA_1", flags)
        for year, lesson in HELD:
            row = next(x for x in self.result["records"] if x["id"] == f"T{year}-L{lesson:03}")
            self.assertEqual(row["flags"], ["TAHAN_KANDUNGAN"])
        self.assertEqual(flags["TAHAN_KANDUNGAN"], 6)

    def test_remaining_short_content_is_not_masked(self):
        r = self.result
        self.assertEqual(r["short_activity_count"], 3)
        self.assertEqual(r["expanded_activity_draft_count"], 560)
        self.assertEqual(r["critical_source_review_count"], 3)
        self.assertAlmostEqual(r["mechanical_three_step_coverage_percent"], 99.57, places=2)
        self.assertEqual(sum(r["domain_counts"].values()), 696)
        self.assertGreater(r["flags"].get("RUJUKAN_HALAMAN_BELUM_DISAHKAN", 0), 0)

    def test_source_blockers_are_explicit_not_silently_approved(self):
        blocked = sorted(row["id"] for row in self.result["records"]
                         if "SUMBER_KRITIKAL_BELUM_LENGKAP" in row["flags"])
        self.assertEqual(blocked, ["T4-L083", "T6-L137", "T6-L141"])
        self.assertEqual(self.result["release"], "NO_GO")
        self.assertIsNone(self.result["quality_score_percent"])

    def test_document_content_still_unapproved(self):
        self.assertEqual(self.result["flags"]["PENAMBAHAN_PDP_BELUM_SAH_PAKAR"], 560)
        self.assertIs(self.result["quality_80_certified"], False)


if __name__ == "__main__":
    unittest.main()
