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
        self.assertGreater(r["flags"].get("AKTIVITI_TERLALU_RINGKAS_PERLU_SEMAKAN", 0), 500)
        self.assertEqual(sum(r["domain_counts"].values()), 696)
        self.assertGreater(r["flags"].get("RUJUKAN_HALAMAN_BELUM_DISAHKAN", 0), 0)


if __name__ == "__main__":
    unittest.main()
