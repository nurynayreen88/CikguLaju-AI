"""Non-destructive SJKC RPT source, route and page layout inventory."""
from pathlib import Path
import io
import json
import unittest
from unittest.mock import patch
from hashlib import sha256
from flask import Flask
from docx import Document
import fitz
from web.rpt_2027_all_http import ROOT,SJK_RPTS,create_all_rpt_blueprint,catalog_data

class SJKCExisting(unittest.TestCase):
    def test_existing_documents(self):
        app=Flask(__name__)
        app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        counts={}
        for slug,definition in SJK_RPTS.items():
            counts[slug]=len(definition.YEARS)
            for year in definition.YEARS:
                with self.subTest(subject=slug,year=year):
                    url=f"/api/rpt/2027/sjkc/{slug}/{year}"
                    folder=ROOT/"sjkc"/slug.replace("-","_")
                    pdf_path=definition.document_path(year,"pdf",root=folder)
                    word_path=definition.document_path(year,"docx",root=folder)
                    self.assertIsNotNone(pdf_path)
                    self.assertIsNotNone(word_path)
                    with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                        for fmt in ("pdf","docx"):
                            self.assertEqual(client.get(url+"."+fmt).status_code,403)
                    with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                        pdf=client.get(url+".pdf")
                        word=client.get(url+".docx")
                        self.assertEqual(pdf.status_code,200)
                        self.assertEqual(word.status_code,200)
                        self.assertEqual(pdf.data,pdf_path.read_bytes())
                        self.assertEqual(word.data,word_path.read_bytes())
                        self.assertEqual(pdf.headers["X-RPT-Source-SHA256"],sha256(pdf.data).hexdigest())
                        for response in (pdf,word):
                            self.assertIn("attachment",response.headers["Content-Disposition"])
                            self.assertEqual(response.headers["Cache-Control"],"no-store, private")
                    doc=Document(io.BytesIO(word.data))
                    tables=doc.tables
                    self.assertTrue(tables,"No editable table in Word")
                    repeated=sum(bool(t.rows[0]._tr.xpath(".//w:tblHeader")) for t in tables if t.rows)
                    with fitz.open(stream=pdf.data,filetype="pdf") as f:
                        self.assertGreater(len(f),1)
                        sizes=sorted(set((round(p.rect.width),round(p.rect.height)) for p in f))
                        print("SJKC_INVENTORY",json.dumps({"subject":slug,"year":year,"pdf_pages":len(f),"editable_tables":len(tables),"header_marked_tables":repeated,"page_sizes":sizes,"pdf_sha":sha256(pdf.data).hexdigest(),"word_sha":sha256(word.data).hexdigest()}),flush=True)
                    for access in (False,True):
                        cat=catalog_data(root=ROOT,personalization_allowed=access)
                        entry=next(y for s in cat["subjects"] if s["code"]==definition.CODE for y in s["years"] if y["year"]==year)
                        self.assertEqual(entry["docx_ready"],access)
                        self.assertEqual(entry["download_enabled"],access)
        self.assertEqual(sum(counts.values()),17)
        print("SJKC_SCOPE",json.dumps(counts),flush=True)

if __name__=="__main__":unittest.main()
