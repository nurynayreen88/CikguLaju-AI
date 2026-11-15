"""Keep 49 tiny Quran copyedits reversible; leave morphological ellipses alone."""
import unittest
from pi_tajwid_double_period_copyedit_review import EXPECTED, audit


class PITajwidCopyeditReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = audit()

    def test_number_and_source_preservation(self):
        d = self.data
        self.assertEqual(d["exact_punctuation_repairs"], 49)
        self.assertEqual(d["by_year"], {str(y): n for y, n in EXPECTED.items()})
        self.assertEqual(d["affix_examples_preserved"], 8)
        self.assertEqual(len({row["id"] for row in d["rows"]}), 49)
        self.assertTrue(d["originals_preserved_in_metadata"])
        self.assertEqual(d["source_sk_sp_fields_modified"], 0)
        self.assertEqual(d["official_quran_verses_modified"], 0)

    def test_copyedit_never_counts_as_academic_signoff(self):
        d = self.data
        self.assertEqual(d["publication"], "HOLD")
        self.assertEqual(d["verified_ready"], 0)
        self.assertEqual(d["expert_approvals"], 0)
        self.assertIsNone(d["academic_quality_percent"])
        self.assertEqual(d["release"], "NO_GO")
        self.assertTrue(all(r["exact_punctuation_correction_only"]
                            and not r["content_and_jawi_expert_approved"]
                            for r in d["rows"]))


if __name__ == "__main__":
    unittest.main()
