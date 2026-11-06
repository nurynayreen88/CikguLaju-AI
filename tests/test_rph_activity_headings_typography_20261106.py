"""RPH Word/PDF activity heading consistency across year/subject templates."""
import html
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from docx import Document
from web.rph_activity_headings_typography import (
    HEADING, bold_activity_headings_in_docx, bold_pdf_heading_markup,
    eligible_rph, install,
)


class ActivityHeadingTypographyTests(unittest.TestCase):
    def test_headings_varied_separators_and_plain_text(self):
        for sample in (
            "Aktiviti 1 : Bina Nombor (15 minit)",
            "Aktiviti 2 – Semak Rakan (15 minit)",
            "Aktiviti 3 — Pentaksiran",
            "Aktiviti 4 - Refleksi",
            "Aktiviti 1 :",
            "Activity 1: Guided Practice",
            "2. Aktiviti 2: Demonstrasi",
        ):
            with self.subTest(sample=sample):
                self.assertRegex(sample, HEADING)
        for sample in (
            "Guru meminta murid melaksanakan Aktiviti 2.",
            "Hari ini kami melakukan aktiviti 1",
            "Aktiviti",
            "Aktiviti 0: Salah",
            "1. Murid menyelesaikan lima item."
        ):
            self.assertIsNone(HEADING.match(sample), sample)

    def test_pdf_bolds_only_missing_heading_and_escapes_text(self):
        raw=("Aktiviti 1 : Susun & Banding\n"
             "Murid menggunakan kad < 10.\n"
             "Aktiviti 2 – Ukur (15 minit)\n"
             "Guru menyemak hasil.")
        already=("Aktiviti 1 : Susun &amp; Banding<br/>"
                 "Murid menggunakan kad &lt; 10.<br/>"
                 "<b>Aktiviti 2 – Ukur (15 minit)</b><br/>"
                 "Guru menyemak hasil.")
        result=bold_pdf_heading_markup(raw, already)
        self.assertIn("<b>Aktiviti 1 : Susun &amp; Banding</b>",result)
        self.assertIn("<b>Aktiviti 2 – Ukur (15 minit)</b>",result)
        self.assertNotIn("<b>Murid",result)
        self.assertIn("Murid menggunakan kad &lt; 10.",result)
        self.assertEqual(bold_pdf_heading_markup("a\nb","a"),"a")

    def test_document_keeps_all_content_and_bolds_each_heading(self):
        sample=("Aktiviti 1 : Teroka (10 minit)\n"
                "Murid menggunakan blok asas 10.\n"
                "Aktiviti 2 – Bina Nombor (20 minit)\n"
                "Guru menyemak murid secara berpasangan.\n"
                "Aktiviti 3: Penilaian\n"
                "Murid menjawab soalan.")
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"rph.docx"
            doc=Document()
            tbl=doc.add_table(rows=2,cols=3)
            tbl.cell(0,1).text="Aktiviti Pengajaran"
            tbl.cell(1,0).text="Aktiviti Utama"
            tbl.cell(1,1).text=sample
            tbl.cell(1,2).text="Catatan"
            doc.save(path)
            self.assertEqual(bold_activity_headings_in_docx(path),3)
            output=Document(path)
            phase=output.tables[0].cell(1,1).paragraphs[0]
            self.assertEqual(phase.text,sample)
            self.assertEqual([r.text for r in phase.runs if r.bold],
                             ["Aktiviti 1 : Teroka (10 minit)",
                              "Aktiviti 2 – Bina Nombor (20 minit)",
                              "Aktiviti 3: Penilaian"])
            self.assertEqual(bold_activity_headings_in_docx(path),0)
            self.assertEqual(Document(path).tables[0].cell(1,1).text,sample)

    def test_avoid_changing_styled_standalone_and_non_rph_material(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"styled.docx"
            doc=Document()
            row=doc.add_table(rows=1,cols=3).rows[0]
            p=row.cells[1].paragraphs[0]
            p.add_run("Aktiviti 1:").bold=True
            p.add_run("\nGuru menerangkan.")
            doc.save(path)
            self.assertEqual(bold_activity_headings_in_docx(path),0)
            self.assertEqual(Document(path).tables[0].cell(0,1).text,
                             "Aktiviti 1:\nGuru menerangkan.")
        self.assertTrue(eligible_rph({"task":"rph","subject":"Matematik"}))
        self.assertTrue(eligible_rph({"task":"rph","subject":"Sains"}))
        self.assertFalse(eligible_rph({"task":"rph","subject":"Pendidikan Islam"}))
        self.assertFalse(eligible_rph({"task":"rph","subject":"Bahasa Arab"}))
        self.assertFalse(eligible_rph({"task":"worksheet","subject":"Matematik"}))

    def test_runtime_installer_idempotent_and_preserves_jawi_pdf(self):
        calls=[]
        runtime=SimpleNamespace(
            create_word_file=lambda s,t,c: "existing.docx",
            _rph_activity_heading_markup_v25184=lambda s: html.escape(s),
            _CIKGULAJU_PI_RENDER_CONTEXT_V2593=False,
        )
        self.assertTrue(install(runtime))
        self.assertFalse(install(runtime))
        self.assertEqual(runtime._rph_activity_heading_markup_v25184(
            "Aktiviti 1: Uji"),"<b>Aktiviti 1: Uji</b>")
        runtime._CIKGULAJU_PI_RENDER_CONTEXT_V2593=True
        self.assertEqual(runtime._rph_activity_heading_markup_v25184(
            "Aktiviti 1: Uji"),"Aktiviti 1: Uji")


if __name__=="__main__":
    unittest.main()
