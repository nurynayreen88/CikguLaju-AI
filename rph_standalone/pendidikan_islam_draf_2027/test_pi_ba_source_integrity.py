"""Prevent accidentally using special education workbook in mainstream lesson plans."""
import unittest
from pi_ba_source_integrity import EXPECTED, BLOCKED, check_source, source_integrity_report


class SourceIntegrityTests(unittest.TestCase):
    def test_expected_mainstream_review_viewers_not_published(self):
        report = source_integrity_report()
        self.assertEqual(len(report["accepted_mainstream_viewer_candidates"]),2)
        self.assertEqual(len(report["rejected_cross_curriculum_sources"]),2)
        self.assertIs(report["safe_for_pdf_distribution"],False)
        self.assertIs(report["direct_page_verification_completed"],False)
        for year, source in EXPECTED.items():
            self.assertEqual(source["stream"],"KSSR_SEMAKAN_ARUS_PERDANA")
            self.assertIs(check_source(year,source["url"])["allowed_for_review"],True)
            self.assertTrue(source["school_subject_panel_viewer_page"].startswith("https://sites.google.com/moe-dl.edu.my/"))
            self.assertTrue(source["school_panel_lists_buku_aktiviti_title"])
            self.assertFalse(source["school_panel_proves_exact_printed_page"])
            self.assertIs(check_source(year,source["url"])["ready_for_teacher"],False)

    def test_kssrpk_aliases_are_explicitly_blocked(self):
        for url, source in BLOCKED.items():
            self.assertEqual(source["book_isbn"],"978-983-49-1622-0")
            self.assertIs(check_source(2,url)["allowed_for_review"],False)
            self.assertIn("KSSRPK",check_source(2,url)["reason"])

    def test_cross_year_and_unrecognised_sources_not_accepted(self):
        self.assertIs(check_source(2,EXPECTED[3]["url"])["allowed_for_review"],False)
        self.assertIs(check_source(3,EXPECTED[2]["url"])["allowed_for_review"],False)
        self.assertIs(check_source(2,"https://invalid.example/file.pdf")["allowed_for_review"],False)


if __name__ == "__main__":
    unittest.main()
