"""Offline tests: Sains Year6 2021 PDF provenance must never grant release."""
import unittest
from io import BytesIO
from unittest.mock import patch

from reportlab.pdfgen.canvas import Canvas

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

    def generated_pdf(self, omit=None, edition="SEPTEMBER 2021"):
        """Generate a 94-page synthetic *non-DSKP* PDF, no source text."""
        buffer = BytesIO()
        pdf = Canvas(buffer, pagesize=(595, 842), pageCompression=1)
        codes = sorted(official_codes(), key=lambda code: tuple(
            map(int, code.split("."))))
        if omit is not None:
            codes.remove(omit)
        for index in range(94):
            if index == 0:
                pdf.drawString(30, 750,
                               "KURIKULUM STANDARD SEKOLAH RENDAH")
                pdf.drawString(30, 730,
                               "SAINS TAHUN 6 " + edition)
            if 54 <= index < 70:
                pdf.drawString(30, 770, "STANDARD PEMBELAJARAN")
                start = (index - 54) * 6
                for n, code in enumerate(codes[start:start+6]):
                    pdf.drawString(30, 750 - n * 23, code + " Ujian kod.")
            pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def test_real_pdf_parser_finds_exact_96_synthetic_codes(self):
        data = self.generated_pdf()
        with patch(
            "scripts.audit_sains_y6_2021_pdf_source_provenance_20261112.MIN_PDF_BYTES",
            0,
        ):
            report = pdf_code_page_audit(data)
        self.assertEqual(report["pdf_pages"], 94)
        self.assertEqual(report["official_unique_code_hits"], 96)
        self.assertEqual(report["missing_codes"], [])
        self.assertTrue(report["source_code_coverage_ready"])
        self.assertEqual(report["sp_table_pages_with_extracted_text"], 16)
        self.assertFalse(report["academic_release_approved"])
        self.assertFalse(report["teacher_pdf_ready"])
        self.assertNotIn("pdf_binary", report)

    def test_real_pdf_parser_blocks_missing_code_and_wrong_edition(self):
        absent = sorted(official_codes())[0]
        with patch(
            "scripts.audit_sains_y6_2021_pdf_source_provenance_20261112.MIN_PDF_BYTES",
            0,
        ):
            missing = pdf_code_page_audit(self.generated_pdf(omit=absent))
            self.assertFalse(missing["source_code_coverage_ready"])
            self.assertEqual(missing["missing_codes"], [absent])
            with self.assertRaisesRegex(ValueError, "masthead"):
                pdf_code_page_audit(self.generated_pdf(edition="SEPTEMBER 2020"))

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
