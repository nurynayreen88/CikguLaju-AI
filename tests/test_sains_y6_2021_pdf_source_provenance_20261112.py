"""Offline tests: Sains Year6 2021 PDF provenance must never grant release."""
import copy
import unittest
from unittest.mock import patch

from scripts.audit_sains_y6_2021_pdf_source_provenance_20261112 import (
    official_codes, pdf_code_page_audit, pdf_coverage_complete, probe,
)


class OriginalBPK2021PdfEvidenceTests(unittest.TestCase):
    def good_code_index(self):
        codes = official_codes()
        return {
            "source_type": "ORIGINAL_EDITION_PDF_FACSIMILE",
            "year6_2021_masthead_seen": True,
            "source_pdf_sha256": "a"*64,
            "sp_table_pages_with_extracted_text": 20,
            "expected_unique_sp": 96,
            "official_unique_code_hits": 96,
            "missing_codes": [],
            "code_to_pdf_page_numbers": {c: [60] for c in codes},
            "academic_release_approved": False,
            "source_visual_sp_text_signoff": False,
            "teacher_pdf_ready": False,
            "copyright_redistribution_permission_verified": False,
        }

    def test_96_code_binary_evidence_is_never_academic_signoff(self):
        report = self.good_code_index()
        self.assertTrue(pdf_coverage_complete(report))
        self.assertFalse(report["academic_release_approved"])
        self.assertFalse(report["teacher_pdf_ready"])
        self.assertFalse(report["copyright_redistribution_permission_verified"])

    def test_missing_or_short_sp_source_is_hold(self):
        for key, value in (
            ("official_unique_code_hits", 95),
            ("sp_table_pages_with_extracted_text", 2),
            ("missing_codes", ["2.2.2"]),
            ("code_to_pdf_page_numbers", {}),
            ("year6_2021_masthead_seen", False),
            ("expected_unique_sp", 95),
            ("source_pdf_sha256", ""),
        ):
            with self.subTest(defect=key):
                report = self.good_code_index()
                report[key] = value
                self.assertFalse(pdf_coverage_complete(report))

    def test_approved_status_or_rights_claim_cannot_be_auto_inferred(self):
        for key in (
            "academic_release_approved",
            "source_visual_sp_text_signoff",
            "teacher_pdf_ready",
            "copyright_redistribution_permission_verified",
        ):
            with self.subTest(key=key):
                report = self.good_code_index()
                report[key] = True
                self.assertFalse(pdf_coverage_complete(report))

    def test_malformed_or_unexpected_binary_blocks(self):
        for invalid in (b"", b"%PDF", b"notpdf" + b"0"*150000):
            with self.subTest(size=len(invalid)):
                with self.assertRaises(ValueError):
                    pdf_code_page_audit(invalid)

    def test_unavailable_pdf_does_not_become_success(self):
        with patch("scripts.audit_sains_y6_2021_pdf_source_provenance_20261112.download_pdf",
                   side_effect=RuntimeError("HTTP 403 blocked")):
            report = probe()
        self.assertEqual(report["status"], "SOURCE_COVERAGE_BLOCKED")
        self.assertFalse(report["academic_release_approved"])
        self.assertEqual(len(report["pdf_sources"]), 1)
        self.assertIn("HTTP 403", report["pdf_sources"][0]["error"])


if __name__ == "__main__":
    unittest.main()
