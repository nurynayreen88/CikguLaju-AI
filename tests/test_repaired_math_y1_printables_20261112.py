"""Reproducible Mathematics Year 1 candidate: PDF/DOCX, layout and no release."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from docx import Document
from pypdf import PdfReader
from tools import render_math_y1_worksheet_20261112 as maths


class MathY1PrintableWorksheetTests(unittest.TestCase):
    def test_source_is_exact_six_question_unpublished_candidate(self):
        data = maths.source()
        self.assertFalse(data["publish"])
        self.assertEqual(data["visibility"], "STAGING_INTERNAL")
        self.assertEqual(data["approval"], "NOT_APPROVED_FOR_PRODUCTION")
        self.assertFalse(data["qa"]["teacher_approved"])
        self.assertFalse(data["qa"]["lesson_mapping_approved"])
        self.assertIsNone(data["curriculum"]["lesson_token"])
        self.assertIsNone(data["curriculum"]["textbook_page"])
        self.assertEqual(len(data["student_copy"]["questions"]), 6)
        self.assertEqual(data["student_copy"]["questions"][-1]["group_a"], 4)
        self.assertEqual(data["student_copy"]["questions"][-1]["group_b"], 3)

    def test_actual_a4_pdf_and_editable_word_hide_internal_metadata(self):
        data = maths.source()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            pdf_file = folder / "math.pdf"
            docx_file = folder / "math.docx"
            maths.make_pdf(data, pdf_file)
            maths.make_docx(data, docx_file)
            self.assertTrue(pdf_file.read_bytes().startswith(b"%PDF-"))
            pdf = PdfReader(io.BytesIO(pdf_file.read_bytes()))
            self.assertEqual(len(pdf.pages), 1)
            self.assertAlmostEqual(float(pdf.pages[0].mediabox.width), 595.3, delta=1)
            self.assertAlmostEqual(float(pdf.pages[0].mediabox.height), 841.9, delta=1)
            text = pdf.pages[0].extract_text()
            self.assertIn("MATEMATIK TAHUN 1", text)
            self.assertIn("BANDING KUANTITI", text)
            self.assertIn("BUKAN UNTUK EDARAN", text)
            self.assertIn("Kumpulan A", text)
            self.assertIn("Kumpulan B", text)
            for number in range(1, 7):
                self.assertIn(str(number) + ".", text)

            word = Document(docx_file)
            self.assertEqual(round(word.sections[0].page_width.mm), 210)
            self.assertEqual(round(word.sections[0].page_height.mm), 297)
            word_text = "\n".join(p.text for p in word.paragraphs)
            self.assertIn("MATEMATIK TAHUN 1", word.sections[0].header.paragraphs[0].text)
            self.assertIn("BANDING KUANTITI", word_text)
            self.assertIn("Kumpulan A", word_text)
            self.assertIn("Kumpulan B", word_text)
            self.assertEqual(word_text.count("Kumpulan A:"), 6)
            self.assertEqual(word_text.count("Kumpulan B:"), 6)
            self.assertIn("kotak kosong", word_text)

            for protected in ("teacher_only", "lesson_mapping_approved",
                              "NOT_APPROVED_FOR_PRODUCTION",
                              "ds_kp_reference", "jawapan_betul",
                              "teacher_approved"):
                self.assertNotIn(protected, text)
                self.assertNotIn(protected, word_text)
            self.assertLess(pdf_file.stat().st_size, 300000)
            self.assertLess(docx_file.stat().st_size, 300000)

    def test_circle_counts_match_source_and_last_group_has_space_to_draw(self):
        # Spy on actual PDF drawing primitives: visual circles must equal the
        # question's two group quantities, not a summary number or answer key.
        data = maths.source()
        calls = []
        original_canvas = maths.canvas.Canvas

        def audited_canvas(*args, **kwargs):
            obj = original_canvas(*args, **kwargs)
            original_circle = obj.circle

            def audited_circle(*cargs, **ckwargs):
                calls.append((cargs, ckwargs))
                return original_circle(*cargs, **ckwargs)

            obj.circle = audited_circle
            return obj

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(maths.canvas, "Canvas", side_effect=audited_canvas):
                maths.make_pdf(data, Path(tmp) / "checked.pdf")
            expected = sum(q["group_a"] + q["group_b"]
                           for q in data["student_copy"]["questions"])
            self.assertEqual(len(calls), expected)
            self.assertTrue(all(len(x[0]) >= 3 and x[0][2] == 5.6 for x in calls))


if __name__ == "__main__":
    unittest.main()
