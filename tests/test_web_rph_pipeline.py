"""End-to-end isolated staging contract: approved DB row -> Word and PDF.

Synthetic fixture only. No production database, Telegram, or HTTP endpoint.
"""
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

from docx import Document
from web.approved_rph_reader import RPHLookupConfig, load_approved_rph
from web.rph_document_renderer import render_approved_rph


class StagingPipelineTests(unittest.TestCase):
    def test_approved_lesson_renders_both_formats(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.sqlite"
            with sqlite3.connect(path) as conn:
                conn.execute(
                    "CREATE TABLE approved_lessons "
                    "(lesson_id INTEGER PRIMARY KEY, title TEXT, body TEXT, "
                    "status TEXT, approval_ref TEXT)"
                )
                conn.execute(
                    "INSERT INTO approved_lessons VALUES (7, ?, ?, ?, ?)",
                    ("English Year 3 Lesson 7", "Teacher models a dialogue.\n"
                     "Pupils practise in pairs.", "approved", "fixture-approval-7"),
                )
                conn.execute(
                    "INSERT INTO approved_lessons VALUES (8, ?, ?, ?, ?)",
                    ("English Year 3 Lesson 8", "Unapproved draft", "draft", ""),
                )
            config = RPHLookupConfig(
                str(path), "approved_lessons", "lesson_id", "title", "body",
                "status", "approved", "approval_ref"
            )
            approved = load_approved_rph(config, 7)
            word, word_mime = render_approved_rph(approved, "docx")
            pdf, pdf_mime = render_approved_rph(approved, "pdf")
            self.assertTrue(word.startswith(b"PK"))
            self.assertIn("wordprocessingml", word_mime)
            self.assertIn("Pupils practise in pairs.",
                          "\n".join(p.text for p in Document(io.BytesIO(word)).paragraphs))
            self.assertTrue(pdf.startswith(b"%PDF-"))
            self.assertEqual(pdf_mime, "application/pdf")
            with self.assertRaises(LookupError):
                load_approved_rph(config, 8)


if __name__ == "__main__":
    unittest.main()
