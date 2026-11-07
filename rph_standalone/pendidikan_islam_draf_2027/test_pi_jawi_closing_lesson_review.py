"""Jawi review ledger: all 690 SK/SP-linked rows, zero auto approvals."""
import hashlib
import unittest
from pi_jawi_closing_lesson_review import build


class PIJawiClosingLessonReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = build()

    def test_total_integrity_and_editor_status(self):
        r=self.result
        self.assertEqual(r["all_catalog_records"],696)
        self.assertEqual(r["fully_held_without_source"],6)
        self.assertEqual(r["candidate_lessons"],690)
        self.assertEqual(r["candidate_unique_groups"],78)
        self.assertEqual(len(r["rows"]),690)
        self.assertEqual(r["ready_lesson_count"],0)
        self.assertEqual(r["jawi_approved"],0)
        self.assertIsNone(r["academic_quality_percent"])
        self.assertIs(r["can_publish"],False)
        self.assertEqual(r["release"],"NO_GO")

    def test_all_source_hashes_and_review_hold(self):
        r=self.result
        self.assertEqual(sum(x["critical_source_hold"] for x in r["rows"]),3)
        self.assertEqual(sum(x["pbd_pending_expert"] for x in r["rows"]),43)
        self.assertEqual(sum(x["old_textbook_page_pending"] for x in r["rows"]),77)
        self.assertEqual(len(set(x["id"] for x in r["rows"])),690)
        self.assertEqual(len(set(x["candidate_group_id"] for x in r["rows"])),78)
        for row in r["rows"]:
            self.assertEqual(row["source_original_sha256"], hashlib.sha256(
                row["source_rumi_closing"].encode("utf-8")).hexdigest())
            self.assertTrue(row["source_sk_not_dskp_approved"].strip())
            self.assertTrue(row["source_sp_not_dskp_approved"].strip())
            self.assertTrue(row["candidate_jawi_closing"].strip())
            for name in ("jawi_reviewer","content_reviewer","source_reviewer"):
                self.assertIsNone(row[name])
            for name in ("jawi_spelling_verified","content_matches_sp_verified",
                         "original_dskp_source_verified","word_pdf_native_verified",
                         "can_publish"):
                self.assertIs(row[name],False)
            self.assertEqual(row["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
