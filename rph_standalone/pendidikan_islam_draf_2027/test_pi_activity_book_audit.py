"""Regressions: no activity-book pages may be invented or published."""
import unittest

from pi_activity_book_audit import audit_activity_books


class ActivityBookAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = audit_activity_books()

    def test_all_years_and_year_specific_policy(self):
        a = self.audit
        self.assertEqual(a["reviewed_records"], 696)
        self.assertEqual(a["open_drafts"], 690)
        self.assertEqual(a["withheld"], 6)
        self.assertEqual(a["year2_year3_active_drafts"], 258)
        self.assertEqual(a["mapping_candidates"], 191)
        self.assertEqual(a["quran_tasmi_no_forced_workbook"], 67)
        self.assertEqual(a["year4_year6_no_book_confirmed"], 432)
        self.assertEqual(a["approval_state"], "HOLD_NOT_READY")

    def test_no_unverified_book_reference_is_sent_to_teacher(self):
        a = self.audit
        self.assertEqual(a["book_mentions"], 0)
        self.assertEqual(a["verified_exercise_links"], 0)
        self.assertEqual(len(a["rows"]), 696)
        for row in a["rows"]:
            self.assertIsNone(row["page"])
            self.assertIsNone(row["exercise"])
            self.assertIs(row["verified"], False)
            if row["disposition"] != "WITHHELD":
                self.assertIs(row["can_show_to_teacher"], False)
                self.assertIs(row["can_download_from_cikgulaju"], False)
                self.assertIs(row["source_page_matches_sp"], False)
                self.assertIs(row["licence_verified_for_distribution"], False)

    def test_no_forced_ba_to_tasmi_or_years_four_to_six(self):
        for r in self.audit["rows"]:
            if r["disposition"] == "MUSHAF_PRIMARY_NO_ASSUMED_BA":
                self.assertIn(r["year"], (2,3))
            if r["year"] in (4,5,6) and r["disposition"] != "WITHHELD":
                self.assertEqual(r["disposition"], "NO_STANDARD_BOOK_CONFIRMED_FOR_YEAR")
                self.assertIsNone(r["book_title_candidate"])
                self.assertEqual(r["source_urls"], [])

    def test_priority_jawi_year2_year3_must_be_in_candidate_queue(self):
        jawi = [r for r in self.audit["rows"]
                if r.get("domain") == "جاوي" and r["year"] in (2,3)]
        self.assertEqual(len(jawi), 73)
        self.assertTrue(all(r["disposition"] == "REVIEW_FOR_EXERCISE_MATCH" for r in jawi))


if __name__ == "__main__":
    unittest.main()
