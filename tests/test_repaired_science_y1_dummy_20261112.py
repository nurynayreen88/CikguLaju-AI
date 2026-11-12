"""Staging-only Sains Y1 pupil worksheet: substantive items, real A4 files and no leak."""
import io
import tempfile
import unittest
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from tools.render_science_y1_worksheet_20261112 import make_docx, make_pdf, source


class ScienceY1WorksheetRepairTests(unittest.TestCase):
    def test_six_pupil_tasks_are_complete_and_non_public(self):
        data = source()
        self.assertFalse(data["publish"])
        self.assertEqual(data["approval"], "NOT_APPROVED_FOR_PRODUCTION")
        self.assertEqual(data["visibility"], "STAGING_INTERNAL")
        self.assertEqual(data["curriculum"]["year"], 1)
        self.assertEqual((data["curriculum"]["sk"], data["curriculum"]["sp"]),
                         ("1.1", "1.1.1"))
        self.assertIsNone(data["curriculum"]["lesson_token"])
        self.assertIsNone(data["curriculum"]["textbook_page"])
        self.assertTrue(data["qa"]["no_public_routes"])
        self.assertFalse(data["qa"]["teacher_approved"])
        self.assertFalse(data["qa"]["lesson_mapping_approved"])
        q = data["student_copy"]["questions"]
        self.assertEqual(len(q), 6)
        self.assertEqual([x["no"] for x in q], list(range(1, 7)))
        self.assertEqual([x["response_type"] for x in q],
                         ["short_text", "checkboxes", "checkboxes",
                          "checkboxes", "checkboxes", "long_text"])
        self.assertTrue(all(len(x["task"]) > 20 for x in q))
        self.assertNotIn("ANSWERSPACE", str(q))
        self.assertIn("Telinga", q[4]["options"])

    def test_pupil_pdf_docx_are_a4_without_teacher_answers(self):
        data = source()
        with tempfile.TemporaryDirectory() as folder:
            pdf_path = Path(folder) / "science.pdf"
            docx_path = Path(folder) / "science.docx"
            make_pdf(data, pdf_path)
            make_docx(data, docx_path)
            binary = pdf_path.read_bytes()
            self.assertTrue(binary.startswith(b"%PDF-"))
            pdf = PdfReader(io.BytesIO(binary))
            self.assertEqual(len(pdf.pages), 1)
            self.assertAlmostEqual(float(pdf.pages[0].mediabox.width), 595.3, delta=1)
            self.assertAlmostEqual(float(pdf.pages[0].mediabox.height), 841.9, delta=1)
            student_text = pdf.pages[0].extract_text()
            for n in range(1, 7):
                self.assertIn(str(n) + ".", student_text)
            self.assertIn("SAINS TAHUN 1", student_text)
            self.assertIn("BELUM UNTUK EDARAN", student_text)
            docx = Document(docx_path)
            self.assertEqual(round(docx.sections[0].page_width.mm), 210)
            self.assertEqual(round(docx.sections[0].page_height.mm), 297)
            doc_text = "\n".join(p.text for p in docx.paragraphs)
            self.assertIn("SAINS", docx.sections[0].header.paragraphs[0].text)
            self.assertIn("Saya Memerhati".upper(), doc_text)
            self.assertIn("Telinga", doc_text)
            for protected in ("Teacher assessment", "assessment",
                              "Q5: telinga", "teacher_only",
                              "teacher_approved", "Jawapan Q1"):
                self.assertNotIn(protected, student_text)
                self.assertNotIn(protected, doc_text)
            self.assertGreater(len(doc_text), 550)
            self.assertLess(pdf_path.stat().st_size, 300000)
            self.assertLess(docx_path.stat().st_size, 300000)

    def test_no_curriculum_or_download_permissions_auto_issued(self):
        data = source()
        self.assertNotIn("READY", (data["approval"], data["visibility"]))
        self.assertNotIn("download_url", data)
        self.assertNotIn("approved_by", data)
        self.assertFalse(data["publish"])


if __name__ == "__main__":
    unittest.main()
