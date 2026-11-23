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

    def test_master_design_teacher_panel_only_is_neutral_without_extra_rows(self):
        """Approved BM SK KP2027 master: pastel identity, neutral teacher box.

        Test actual reviewed DLP Science, DLP Math and PPKI native Word.
        Keep the original outer width, the exact number of source detail
        rows, the teacher values, and every curriculum paragraph.
        """
        from docx.oxml.ns import qn
        from dlp_year2_rph import _TEACHER_PANEL_FILL

        teacher = {"class": "4 Amanah", "date": "2027-03-02",
                   "time": "09:00 - 10:00", "students": "24",
                   "reflection": "Catatan guru selepas PdP."}
        palettes = {"SCIENCE_DLP": "DFF1E3",
                    "MATH_DLP": "DCEBFA", "PPKI": "EEE6F7"}
        for subject, generate in self.samples(teacher):
            with self.subTest(subject=subject):
                parsed = Document(BytesIO(generate("word")))
                self.assertEqual(len(parsed.tables), 4)
                head = parsed.tables[0]
                self.assertAlmostEqual(sum(c.width.mm for c in head.columns), 182, delta=1)
                left_shade = head.cell(0, 0)._tc.get_or_add_tcPr().find(qn("w:shd"))
                right_shade = head.cell(0, 1)._tc.get_or_add_tcPr().find(qn("w:shd"))
                self.assertIsNotNone(left_shade)
                self.assertIsNotNone(right_shade)
                self.assertEqual(left_shade.get(qn("w:fill")), palettes[subject])
                self.assertEqual(right_shade.get(qn("w:fill")), _TEACHER_PANEL_FILL)
                self.assertGreater(head.columns[0].width, head.columns[1].width)
                fields = premium_rph_details(parsed)
                self.assertEqual(fields["Kelas" if subject=="PPKI" else "Class"],
                                 teacher["class"])
                self.assertIn(teacher["reflection"],
                              parsed.tables[3].cell(len(parsed.tables[3].rows)-1,1).text)
                # The new style must not add artificial curriculum sections
                # on top of those already rendered by the source generator.
                self.assertNotIn("Mata Pelajaran",
                                 [r.cells[0].text for r in parsed.tables[1].rows])
                self.assertNotIn("Subject",
                                 [r.cells[0].text for r in parsed.tables[1].rows])

    def test_external_centre_title_and_two_aligned_source_panels_a4(self):
        """Actual reviewed DLP/PPKI native Word and PDF, not example overlay."""
        import fitz
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn

        teacher = {"class": "", "date": "", "time": "", "students": ""}
        for subject, generate in self.samples(teacher):
            with self.subTest(subject=subject):
                document = Document(BytesIO(generate("word")))
                assert len(document.tables) == 4
                assert document.paragraphs[0].text.strip().casefold() in (
                    "daily lesson plan", "rancangan pengajaran harian")
                assert document.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER
                head = document.tables[0]
                left, right = head.rows[0].cells
                assert len(left.paragraphs) == 3
                assert len(right.paragraphs) >= 4
                left_labels = ["Mata Pelajaran:", "Tahun/Tingkatan:", "Tajuk:"] if subject == "PPKI" else (
                    ["Subject:", "Year:", "Topic:"])
                assert all(p.text.startswith(label) for p, label in
                           zip(left.paragraphs, left_labels)), subject
                for cell, expected in ((left, 32), (right, 34)):
                    for para in cell.paragraphs:
                        tabs = para._p.find(qn("w:pPr")).find(qn("w:tabs"))
                        assert tabs is not None, (subject, para.text)
                        tab = tabs.find(qn("w:tab"))
                        assert tab is not None
                        assert abs(int(tab.get(qn("w:pos"))) / 56.6929 - expected) < .3
                assert "____" not in right.text
                pdf_bytes = generate("pdf")
                with fitz.open(stream=pdf_bytes, filetype="pdf") as pages:
                    assert len(pages) == 1, (subject, "one A4 page required")
                    page = pages[0]
                    title = "RANCANGAN PENGAJARAN HARIAN" if subject == "PPKI" else "Daily Lesson Plan"
                    titles = page.search_for(title)
                    assert titles, (subject, title)
                    assert abs((titles[0].x0+titles[0].x1)/2 - page.rect.width/2) < 14
                    assert page.rect.width > 590 and page.rect.height > 840
                    assert any(d["rect"].y0 > titles[0].y1-1 and
                               abs(d["rect"].width - 182*72/25.4) < 3
                               for d in page.get_drawings()
                               if d.get("fill") is not None), subject

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
