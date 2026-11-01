"""Contract tests for the isolated web document renderer.

Run: python -m unittest discover -s tests -p 'test_web_rph_renderer.py'
These tests use synthetic fixtures and do not establish production DB approval.
"""
import io
import unittest
from unittest.mock import patch

from web.rph_document_renderer import ApprovedRPH, render_approved_rph


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.rph = ApprovedRPH(
            lesson_id=1,
            title="English Year 3 - Lesson 1",
            content="Set induction\nTeacher introduces vocabulary.\nPupils practise.",
            approval_reference="synthetic-test-only",
        )

    def test_word_is_openable(self):
        from docx import Document

        data, mime = render_approved_rph(self.rph, "docx")
        self.assertTrue(data.startswith(b"PK"))
        self.assertIn("wordprocessingml", mime)
        document = Document(io.BytesIO(data))
        self.assertIn("English Year 3", document.paragraphs[0].text)
        self.assertTrue(any("Pupils practise." in p.text for p in document.paragraphs))

    def test_pdf_is_openable(self):
        data, mime = render_approved_rph(self.rph, "pdf")
        self.assertTrue(data.startswith(b"%PDF-"))
        self.assertEqual(mime, "application/pdf")
        self.assertIn(b"%%EOF", data[-1024:])

    def test_missing_approval_reference_rejected(self):
        with self.assertRaises(ValueError):
            render_approved_rph(ApprovedRPH(1, "Title", "Content", ""), "pdf")

    def test_invalid_lesson_rejected(self):
        with self.assertRaises(ValueError):
            render_approved_rph(ApprovedRPH(0, "Title", "Content", "test"), "docx")

    def test_invalid_format_rejected(self):
        with self.assertRaises(ValueError):
            render_approved_rph(self.rph, "txt")

    def test_does_not_import_telegram_app(self):
        import sys

        self.assertNotIn("app", sys.modules)


if __name__ == "__main__":
    unittest.main()
