"""Unit tests for all 12 PJPK scopes and fail-closed summary behavior."""
import unittest
from scripts.pjpk_12_scope_summary_v2680 import summarize, YEARS, SUBJECTS

class PJPKScopeSummaryTests(unittest.TestCase):
    def test_empty_queue_retains_all_twelve_scopes(self):
        result = summarize([])
        self.assertEqual(result["scope_count"], 12)
        self.assertEqual(len(result["scopes"]), 12)
        self.assertEqual(result["review_rows"], 0)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["production_promoted"])
        self.assertEqual({(r["year"], r["subject"]) for r in result["scopes"]},
                         {(y, s) for y in YEARS for s in SUBJECTS})

    def test_batch_totals_and_scope_isolation(self):
        rows = [
            {"year": "Tahun 1", "subject": "Pendidikan Jasmani", "record_type": "SP_SOURCE_REVIEW"},
            {"year": "Tahun 1", "subject": "Pendidikan Jasmani", "record_type": "MISSING_SK_LINK"},
            {"year": "Tahun 6", "subject": "Pendidikan Kesihatan", "record_type": "SP_SOURCE_REVIEW"},
        ]
        result = summarize(rows)
        self.assertEqual((result["review_rows"], result["sp_source_review"], result["missing_sk_link"]), (3, 2, 1))
        by_scope = {(r["year"], r["subject"]): r for r in result["scopes"]}
        self.assertEqual(by_scope[("Tahun 1", "Pendidikan Jasmani")]["review_rows"], 2)
        self.assertEqual(by_scope[("Tahun 6", "Pendidikan Kesihatan")]["review_rows"], 1)
        self.assertEqual(by_scope[("Tahun 2", "Pendidikan Jasmani")]["review_rows"], 0)

    def test_reject_wrong_year_subject_and_record_type(self):
        for row in (
            {"year": "Tahun 7", "subject": "Pendidikan Jasmani", "record_type": "SP_SOURCE_REVIEW"},
            {"year": "Tahun 1", "subject": "Pendidikan Moral", "record_type": "SP_SOURCE_REVIEW"},
            {"year": "Tahun 1", "subject": "Pendidikan Jasmani", "record_type": "READY"},
        ):
            with self.subTest(row=row), self.assertRaises(ValueError):
                summarize([row])

if __name__ == "__main__":
    unittest.main()
