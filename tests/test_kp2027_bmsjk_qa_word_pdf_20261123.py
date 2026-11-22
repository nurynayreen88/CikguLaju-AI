"""Readback checks for offline KP2027 BM SJK 52-document QA Word/PDF generator."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import ast
import re
import tempfile
import unittest

from docx import Document
from pypdf import PdfReader
from tools.kp2027_bmsjk_qa_word_pdf import (
    OUTER_WIDTH_MM, qa_records, render_docx, render_pdf, export_all
)

ROOT = Path(__file__).resolve().parents[1]


def squeeze(text):
    return re.sub(r"\s+", " ", text or "").strip()


class QAOnlyWordPDF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = qa_records()

    def test_never_import_production_api_or_change_release_gate(self):
        self.assertEqual(len(self.records), 52)
        self.assertTrue(all(r["status"] == "QA_HOLD_NOT_READY" for r in self.records))
        self.assertEqual(len({r["sp_code"] for r in self.records}),26)
        self.assertEqual(len({r["proposed_pdp"] for r in self.records}),52)
        for r in self.records:
            self.assertEqual(r["status"],"QA_HOLD_NOT_READY")
            add=r["editorial_supplement"]
            self.assertEqual(len(add),8)
            pbd=r["editorial_assessment"]
            self.assertEqual(set(pbd),{"pbd_evidence","enrichment_action"})
            self.assertTrue(all(len(value)>=85 for value in pbd.values()))
            self.assertGreater(len(add["guided_pdp"]),90)
            self.assertGreater(len(add["application_pdp"]),90)
            self.assertNotEqual(add["guided_pdp"],add["application_pdp"])
            for key in ("prior_knowledge","success_criterion","emk_nilai",
                        "kbat","pak21","closure"):
                self.assertGreaterEqual(len(add[key]),28)
        self.assertEqual(len({r["editorial_assessment"]["pbd_evidence"]
                              for r in self.records}),26)
        self.assertEqual(len({r["editorial_assessment"]["enrichment_action"]
                              for r in self.records}),26)
        self.assertEqual(len({r["editorial_supplement"]["guided_pdp"]
                             for r in self.records}),26)
        self.assertEqual(len({r["editorial_supplement"]["application_pdp"]
                             for r in self.records}),26)
        self.assertEqual(
            self.records[8]["sp_components"],
            ["ucapan selamat; ucapan penghargaan; permohonan maaf"]
        )

        source = (ROOT / "tools/kp2027_bmsjk_qa_word_pdf.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(x.name.split(".")[0] for x in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertTrue({"flask","supabase","requests","httpx","boto3"}.isdisjoint(imports))
        self.assertNotIn("api/rph",source)
        self.assertNotIn("status = 'READY'", source)

    def test_word_pdf_source_identity_and_four_equal_width_tables(self):
        for r in (self.records[0], self.records[8], self.records[51]):
            with self.subTest(number=r["proposed_pdp"]):
                word = render_docx(r)
                self.assertTrue(word.startswith(b"PK"))
                document = Document(BytesIO(word))
                self.assertEqual(len(document.tables),4)
                self.assertEqual(round(document.sections[0].page_width.mm),210)
                self.assertEqual(round(document.sections[0].page_height.mm),297)
                for tbl in document.tables:
                    total=sum(c.width.mm for c in tbl.columns)
                    self.assertAlmostEqual(total,OUTER_WIDTH_MM,delta=0.6)
                text = "\n".join(
                    cell.text
                    for tbl in document.tables for row in tbl.rows
                    for cell in row.cells
                )
                for exact in (
                    r["sk_code"],r["sk_description"],
                    r["sp_code"],r["sp_description"],
                    r["set_induksi"]["guru"],r["editorial_supplement"]["closure"],
                    r["aktiviti_utama"][0]["guru"],r["aktiviti_utama"][2]["murid"],
                    r["editorial_assessment"]["pbd_evidence"],
                    r["pemulihan"],r["editorial_assessment"]["enrichment_action"],
                    r["editorial_supplement"]["success_criterion"],
                    r["editorial_supplement"]["emk_nilai"],
                    r["editorial_supplement"]["kbat"],
                    r["editorial_supplement"]["pak21"],
                    r["editorial_supplement"]["guided_pdp"] if r["phase"]=="penerokaan"
                    else r["editorial_supplement"]["application_pdp"]
                ):
                    self.assertIn(exact,text)
                self.assertEqual(text.count("Refleksi"),1)
                self.assertNotIn(r["penutup"]["murid"],text)
                self.assertNotIn(r["pengayaan"],text)
                self.assertNotIn(r["penilaian"],text)
                for bad in ("Auto / Manual","QA_HOLD_NOT_READY","SEMAKAN PELAKSANAAN",
                            "RPT", "______"):
                    self.assertNotIn(bad,text)
                activities=[c for row in document.tables[2].rows for c in row.cells
                            if re.search(r"^Aktiviti [123]:",c.text)]
                self.assertEqual(len(activities),3)
                self.assertTrue(all(next(run.bold for run in c.paragraphs[0].runs if run.text.strip()) for c in activities))
                self.assertTrue("Kelas:" in document.tables[0].cell(0,1).text)
                self.assertNotIn("_",document.tables[0].cell(0,1).text)

                pdf=render_pdf(r)
                self.assertTrue(pdf.startswith(b"%PDF-"))
                reader=PdfReader(BytesIO(pdf))
                self.assertGreaterEqual(len(reader.pages),1)
                self.assertLessEqual(len(reader.pages),4)
                # Visible PDF QA: a lone Refleksi row must never occupy page 2.
                if len(reader.pages)>1:
                    last=squeeze(reader.pages[-1].extract_text() or "")
                    self.assertGreater(len(last),150, "Reflection-only orphan page")
                for page in reader.pages:
                    self.assertAlmostEqual(float(page.mediabox.width),595.28,delta=0.1)
                    self.assertAlmostEqual(float(page.mediabox.height),841.89,delta=0.1)
                pdf_text=squeeze(" ".join(page.extract_text() or "" for page in reader.pages))
                for exact in (r["sk_description"],r["sp_description"],
                              r["aktiviti_utama"][0]["guru"],
                              r["aktiviti_utama"][2]["murid"],r["editorial_supplement"]["closure"],
                              r["editorial_assessment"]["pbd_evidence"],
                              r["editorial_assessment"]["enrichment_action"],
                              r["editorial_supplement"]["success_criterion"],
                              r["editorial_supplement"]["kbat"],
                              r["editorial_supplement"]["guided_pdp"] if r["phase"]=="penerokaan"
                              else r["editorial_supplement"]["application_pdp"]):
                    self.assertIn(squeeze(exact),pdf_text)
                self.assertEqual(pdf_text.count("Refleksi"),1)
                self.assertNotIn(squeeze(r["penutup"]["murid"]),pdf_text)
                self.assertNotIn(squeeze(r["pengayaan"]),pdf_text)
                self.assertNotIn("Auto / Manual",pdf_text)
                self.assertNotIn("QA_HOLD_NOT_READY",pdf_text)

    def test_offline_all_104_files_only_when_qa_gate_is_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=export_all(tmp)
            self.assertEqual(manifest["release_gate"],"QA_HOLD_NOT_READY")
            self.assertEqual(manifest["ready"],0)
            self.assertEqual(len(manifest["files"]),104)
            names={v["name"] for v in manifest["files"]}
            self.assertEqual(len(names),104)
            for entry in manifest["files"]:
                self.assertEqual(entry["status"],"QA_HOLD_NOT_READY")
                self.assertGreater(entry["bytes"],6000)
                self.assertTrue((Path(tmp)/entry["name"]).is_file())
                if entry["name"].endswith(".pdf"):
                    pages=PdfReader(str(Path(tmp)/entry["name"])).pages
                    self.assertEqual(len(pages),1,
                                     "QA A4 PDF unexpectedly more than one page: "+entry["name"])
                    if len(pages)>1:
                        self.assertGreater(len(squeeze(pages[-1].extract_text() or "")),150,
                                           "Orphan page in "+entry["name"])


if __name__ == "__main__":
    unittest.main()
