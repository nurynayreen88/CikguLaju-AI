"""Real DLP and pilot PPKI documents must match owner-approved RPH geometry.

This test loads reviewed source rows and renders Word/PDF without user login,
generation credit, Telegram, Supabase or HTTP.
"""
from io import BytesIO
import unittest

from docx import Document
from pypdf import PdfReader

from dlp_year2_rph import catalog, render
from staging.ppki.render_pengurusan_kehidupan import (
    load_catalog as ppki_catalog, render_lesson as ppki_render,
)
from web.rph_premium_readback_20261121 import premium_rph_details


class PremiumDlpPpkiProof(unittest.TestCase):
    def samples(self, teacher):
        for subject in ("SCIENCE_DLP", "MATH_DLP"):
            unit = catalog()[subject][0]
            yield subject, lambda fmt, subject=subject, unit=unit: render(
                subject, unit, unit["lessons"][0], fmt, teacher
            )
        ppki = ppki_catalog()
        yield "PPKI", lambda fmt: ppki_render(
            ppki, ppki["lessons"][0], "docx" if fmt == "word" else "pdf", teacher
        )

    def test_real_source_word_and_pdf_with_teacher_metadata(self):
        teacher = {"class": "2 Bestari", "date": "2027-01-20",
                   "time": "08:00 - 09:00", "students": "28",
                   "reflection": "Pencapaian murid direkod selepas PdP."}
        for subject, generate in self.samples(teacher):
            with self.subTest(subject=subject):
                word = generate("word")
                doc = Document(BytesIO(word))
                fields = premium_rph_details(doc)
                cls = "Class" if subject != "PPKI" else "Kelas"
                when = "Date" if subject != "PPKI" else "Tarikh"
                self.assertEqual(fields[cls], teacher["class"])
                self.assertTrue(fields[when])
                self.assertEqual(len(doc.tables), 4)
                self.assertNotIn("____", doc.tables[0].cell(0, 1).text)
                identity = doc.tables[0].cell(0, 0).text
                self.assertTrue("DLP" in identity if subject != "PPKI" else "PPKI" in identity)
                self.assertIn(teacher["reflection"], doc.tables[-1].cell(len(doc.tables[-1].rows)-1, 1).text)
                pdf_bytes = generate("pdf")
                pdf = PdfReader(BytesIO(pdf_bytes))
                self.assertGreaterEqual(len(pdf.pages), 1)
                self.assertLessEqual(len(pdf.pages), 2)
                for page in pdf.pages:
                    self.assertAlmostEqual(float(page.mediabox.width), 595.28, delta=2)
                    self.assertAlmostEqual(float(page.mediabox.height), 841.89, delta=2)
                text = " ".join(" ".join(page.extract_text().split()) for page in pdf.pages)
                for value in (teacher["class"], teacher["time"], teacher["students"]):
                    self.assertIn(value, text)
                self.assertNotIn("____", text.split("Learning objective")[0] if subject != "PPKI"
                                 else text.split("Standard Kandungan")[0])
                for label in ("Content Standards", "Learning Standards") if subject != "PPKI" else (
                        "Standard Kandungan", "Standard Pembelajaran"):
                    self.assertIn(label, fields)
                    self.assertIn(" ".join(fields[label].split()), text)

    def test_web_native_word_wrapper_does_not_reflow_premium_four_boxes(self):
        """Teacher Word downloads must preserve the 182 mm approved grid."""
        from web.native_rph_telegram_api import compact_web_word_notes

        teacher = {"class": "4 Bestari", "date": "2027-02-15",
                   "time": "08:00 - 09:00", "students": "29"}
        for subject, generate in self.samples(teacher):
            with self.subTest(subject=subject):
                word_bytes = generate("word")
                self.assertEqual(compact_web_word_notes(word_bytes), word_bytes)
                parsed = Document(BytesIO(word_bytes))
                fields = premium_rph_details(parsed)
                self.assertEqual(len(parsed.tables), 4)
                self.assertIn("Standard Kandungan" if subject == "PPKI"
                              else "Content Standards", fields)

    def test_blank_teacher_boxes_are_truly_blank(self):
        teacher = dict.fromkeys(("class", "date", "time", "students"), "")
        for subject, generate in self.samples(teacher):
            with self.subTest(subject=subject):
                doc = Document(BytesIO(generate("word")))
                fields = premium_rph_details(doc)
                labels = ("Class", "Date", "Time", "Number of pupils") if subject != "PPKI" else (
                    "Kelas", "Tarikh", "Masa", "Bilangan Murid"
                )
                for label in labels:
                    self.assertEqual(fields[label], "")
                header = doc.tables[0].cell(0, 1).text
                self.assertNotIn("____", header)
                self.assertNotIn("—", header)


if __name__ == "__main__":
    unittest.main()
