"""Offline Word/PDF A/B RPT draft readback and no-fabricated-dates gate."""
import unittest
import tempfile
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader
from tools.kp2027_bmsjk_rpt_ab_qa import load_group,render_docx,render_pdf,export_all


class RPTABDocuments(unittest.TestCase):
    def test_52_rows_each_group_keep_all_dates_blank_and_exact_source(self):
        for group in ("A","B"):
            with self.subTest(group=group):
                cfg,rows=load_group(group)
                self.assertEqual(len(rows),52)
                self.assertEqual([r[0] for r in rows],
                                 [f"{n:03d}" for n in range(1,53)])
                self.assertEqual(len({r[3].split()[0] for r in rows}),26)
                self.assertTrue(all(not r[5] for r in rows))
                self.assertEqual(cfg["mula"],"2027-01-04")
                self.assertIn("2027-12-",cfg["akhir"])

    def test_word_pdf_real_readback_without_fake_lesson_dates(self):
        for group in ("A","B"):
            with self.subTest(group=group):
                word=render_docx(group)
                doc=Document(BytesIO(word))
                self.assertEqual(round(doc.sections[0].page_width.mm),297)
                self.assertEqual(round(doc.sections[0].page_height.mm),210)
                self.assertEqual(len(doc.tables),1)
                self.assertEqual(len(doc.tables[0].rows),53)
                self.assertEqual(len(doc.tables[0].columns),6)
                self.assertTrue(all(not row.cells[5].text for row in doc.tables[0].rows[1:]))
                self.assertIn("1.2.2",doc.tables[0].rows[9].cells[3].text)
                self.assertIn("permohonan maaf",doc.tables[0].rows[9].cells[3].text)
                pdf=render_pdf(group)
                self.assertTrue(pdf.startswith(b"%PDF-"))
                reader=PdfReader(BytesIO(pdf))
                self.assertGreater(len(reader.pages),1)
                self.assertLess(len(reader.pages),15)
                text=" ".join(page.extract_text() or "" for page in reader.pages)
                self.assertIn("Pemetaan 52 PdP",text)
                self.assertIn("4.2.2",text)
                self.assertIn("permohonan maaf",text)
                self.assertNotIn("QA_HOLD_RPT_ANNUAL_NOT_COMPLETE",text)
                for page in reader.pages:
                    self.assertAlmostEqual(float(page.mediabox.width),841.89,delta=.1)
                    self.assertAlmostEqual(float(page.mediabox.height),595.28,delta=.1)

    def test_export_four_independent_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=export_all(tmp)
            self.assertFalse(manifest["public"])
            self.assertEqual(manifest["status"],"QA_HOLD_RPT_ANNUAL_NOT_COMPLETE")
            self.assertEqual(len(manifest["files"]),4)
            self.assertEqual({f["name"].split("_KUMPULAN_")[1][0]
                              for f in manifest["files"]},{"A","B"})
            self.assertTrue(all(f["bytes"]>6000 for f in manifest["files"]))
            self.assertTrue(all((Path(tmp)/f["name"]).exists()
                                for f in manifest["files"]))


if __name__=="__main__":
    unittest.main()
