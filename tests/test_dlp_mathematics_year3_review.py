"""Verify the Mathematics DLP Year 3 draft against its published RPT."""
from io import BytesIO
import unittest

from docx import Document
from pypdf import PdfReader

from dlp_year2_rph import _pdf, _word
from staging.dlp.year3.render_mathematics import render_plan, verify_drafts


class MathematicsYear3DlpReviewTests(unittest.TestCase):
    def test_all_plans_match_rpt_and_export_both_formats(self):
        drafts = verify_drafts()
        self.assertEqual(len(drafts), 82)
        for draft in drafts:
            identifier, title, _, label, dates, _, _, _ = draft
            with self.subTest(lesson=identifier):
                word = BytesIO()
                render_plan(word, draft, _word)
                document = Document(word)
                details = {row.cells[0].text: row.cells[1].text for row in document.tables[0].rows}
                self.assertEqual(details["Topic"], title)
                self.assertEqual(details["RPT 2027 dates"], dates)
                self.assertEqual(details["Lesson / PdP"], label)
                self.assertAlmostEqual(document.sections[0].page_width.mm, 210, places=1)
                self.assertAlmostEqual(document.sections[0].page_height.mm, 297, places=1)
                pdf = BytesIO()
                render_plan(pdf, draft, _pdf)
                pages = PdfReader(pdf).pages
                self.assertEqual(len(pages), 1)
                self.assertAlmostEqual(float(pages[0].mediabox.width), 595.28, places=1)
                self.assertAlmostEqual(float(pages[0].mediabox.height), 841.89, places=1)
                self.assertIn("Year 3 SK", pages[0].extract_text())
                self.assertIn("Reflection", pages[0].extract_text())
