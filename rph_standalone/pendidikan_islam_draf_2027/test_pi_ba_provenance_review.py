"""Second-hand pages must not be silently treated as approved BA page numbers."""
import unittest
from pi_ba_provenance_review import provenance_report


class ProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = provenance_report()
        cls.idx = {x["lesson_id"]: x for x in cls.report["rows"]}

    def test_source_types_and_count(self):
        r = self.report
        self.assertEqual(r["secondary_hints_total"], 42)
        self.assertEqual(r["source_classes"], {
            "OTHER_TEACHER_SOURCE_PAGE_CLAIM": 6,
            "SECONDARY_CONFLICT_SOURCE_PAGES": 1,
            "TEACHER_PDPR_BOOK_ACTIVITY_PAGE_CLAIM": 27,
            "VIDEO_PAGE_RANGE_UNCONFIRMED": 8,
        })
        self.assertEqual(r["direct_workbook_page_verified"], 0)
        self.assertEqual(r["exercise_matched_to_sp_verified"], 0)
        self.assertEqual(r["publishable_page_references"], 0)

    def test_conflict_and_evidence_not_approved(self):
        self.assertEqual(self.idx["T3-L004"]["source_classification"],
                         "SECONDARY_CONFLICT_SOURCE_PAGES")
        self.assertIn("p65-66", self.idx["T3-L004"]["recheck_note"])
        self.assertEqual(self.idx["T3-L097"]["source_classification"],
                         "TEACHER_PDPR_BOOK_ACTIVITY_PAGE_CLAIM")
        self.assertEqual(self.idx["T2-L002"]["source_classification"],
                         "VIDEO_PAGE_RANGE_UNCONFIRMED")
        for row in self.report["rows"]:
            self.assertIs(row["original_book_page_checked"], False)
            self.assertIs(row["exercise_checked"], False)
            self.assertIsNone(row["approved_rph_page"])
            self.assertIs(row["allowed_to_publish"], False)


if __name__ == "__main__":
    unittest.main()
