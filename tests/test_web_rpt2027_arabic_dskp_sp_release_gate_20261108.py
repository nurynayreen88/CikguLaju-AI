"""Real Web 56-catalog release integrity for source-visual Arabic Year2-6 PDFs.
All academic statements remain draft, staged artifacts must never auto-approve.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import re
import unicodedata
import unittest
import fitz
from web.rpt_2027_all_http import catalog_data

BASE=Path(__file__).resolve().parents[1]/"rpt_2027/web_2027_pdfs"
COUNTS={2:(60,58),3:(60,54),4:(58,54),5:(60,60),6:(60,60)}

class ArabicWeb2027SourceSPDraft(unittest.TestCase):
    def test_five_arabic_source_page_draft_pdf_and_unmodified_56_catalog(self):
        manifest=json.loads((BASE/"manifest.json").read_text("utf-8"))
        cover=json.loads((BASE/"original_cover_layout_verified.json").read_text("utf-8"))
        self.assertEqual(manifest["status"],"DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL")
        self.assertIs(manifest["academic_final_approved"],False)
        self.assertEqual(manifest["count"],len(manifest["files"]))
        self.assertEqual(manifest["count"],56)
        self.assertEqual(set(manifest["files"]),set(cover["source_sha256_by_subject_year"]))
        catalog=catalog_data(allowed=True)
        self.assertEqual(catalog["total_rpt"],catalog["available_rpt"])
        self.assertEqual(catalog["total_rpt"],56)
        arabic=next(x for x in catalog["subjects"] if x["code"]=="bahasa_arab")
        self.assertIn("290/298",arabic["years"][0]["note"])
        for year,(pdp,minvisual) in COUNTS.items():
            with self.subTest(year=year):
                key=f"bahasa_arab:{year}"
                entry=manifest["files"][key]
                self.assertEqual(entry["status"],"DRAF")
                self.assertIn("NOT_ACADEMIC_FINAL",entry["source_stage"])
                self.assertEqual(cover["source_sha256_by_subject_year"][key],entry["sha256"])
                pdf=(BASE/entry["path"]).read_bytes()
                self.assertTrue(pdf.startswith(b"%PDF-"))
                self.assertEqual(len(pdf),entry["bytes"])
                self.assertEqual(hashlib.sha256(pdf).hexdigest(),entry["sha256"])
                with fitz.open(stream=pdf,filetype="pdf") as document:
                    self.assertEqual(document.page_count,entry["pages"])
                    cover_text=document[0].get_text()
                    for name in ("LOGO SEKOLAH","NAMA SEKOLAH","NAMA GURU"):
                        self.assertIn(name,cover_text)
                    self.assertEqual(cover_text.count("__________________________________________"),2)
                    text=unicodedata.normalize("NFKC","\n".join(page.get_text() for page in document))
                    self.assertEqual(text.count("PdP "),pdp)
                    self.assertEqual(text.count("Buka DSKP asal"),pdp)
                    self.assertGreaterEqual(text.count("القدرة"),minvisual)
                    for token in ("Pernyataan penuh","teks belum disahkan","AMARAN:"):
                        self.assertNotIn(token,text)

if __name__=="__main__":
    unittest.main()
