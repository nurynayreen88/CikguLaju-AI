"""Actual paid/free download and cover checks for every KSSR SK Year 2–6 set."""
import io,json,unittest
from hashlib import sha256
from unittest.mock import patch
from docx import Document
from PIL import Image
import fitz
from flask import Flask
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint,catalog_data
from web.rpt_native_word_cover import cover_png
from web.rpt_native_word_batch import PINS,APPROVED_SCIENCE_PINS
from rpt_2027.matematik.sk_documents import DIGESTS
class AllSKDownloads(unittest.TestCase):
    def test_every_set(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        base=ROOT/"web_2027_pdfs"
        manifest=json.loads((base/"manifest.json").read_text())
        lock=json.loads((base/"original_cover_layout_verified.json").read_text())
        self.assertEqual(len(manifest["files"]),56)
        image=io.BytesIO();Image.new("RGB",(48,48),"#28553a").save(image,format="PNG")
        identity={"school":"SEKOLAH KEBANGSAAN CONTOH","teacher":"GURU CONTOH","state":"","logo":image.getvalue()}
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        flags={"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1","CIKGULAJU_RPT_NATIVE_RTL_WORD":"1","CIKGULAJU_RPT_BM_MERGED_WORD":"1","CIKGULAJU_RPT_COMPACT_PDF_BATCH":"1"}
        with patch.dict("os.environ",flags),patch("web.native_telegram_integrated_english_client.integrated_enabled",return_value=True),patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}),patch("web.rpt_school_cover.school_identity",return_value=identity):
            for key,entry in manifest["files"].items():
                with self.subTest(key=key):
                    subject,y=key.split(":");year=int(y)
                    url=f"/api/rpt/2027/all/{subject}/{year}"
                    source=base/entry["path"]
                    if subject=="english":
                        source=ROOT/"english"/f"RPT_English_SK_2027_Year_{year}_A_B.pdf"
                    elif subject=="matematik" and year in DIGESTS:
                        from rpt_2027.matematik.sk_documents import document_path
                        source=document_path(year,root=ROOT/"matematik")
                    elif subject=="sains" and year in APPROVED_SCIENCE_PINS:
                        from rpt_2027.sains.sk_documents import document_path
                        source=document_path(year,root=ROOT/"sains")
                    with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                        self.assertEqual(client.get(url+".docx").status_code,403)
                        pdf=client.get(url+".pdf")
                        self.assertEqual(pdf.status_code,200)
                        self.assertTrue(pdf.data.startswith(b"%PDF-"))
                    with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                        self.assertEqual(client.get(url+".pdf").data,pdf.data)
                        if subject=="bahasa_melayu":
                            from web.rpt_native_word_batch import bm_merged_document
                            bm_merged_document(year,source,paid,{"account_backend":"supabase"},root=ROOT)
                        word=client.get(url+".docx")
                        self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else key)
                        self.assertIn("attachment",word.headers["Content-Disposition"])
                        self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                        doc=Document(io.BytesIO(word.data))
                        self.assertGreater(len(doc.tables),1)
                        for table in doc.tables[:-1]:
                            self.assertTrue(table.rows[0]._tr.xpath(".//w:tblHeader"))
                        from docx.oxml.ns import qn
                        rid=doc.paragraphs[0]._p.xpath(".//a:blip")[0].get(qn("r:embed"))
                        self.assertEqual(doc.part.related_parts[rid].blob,cover_png(source.read_bytes(),lock,key,identity))
                        with fitz.open(stream=pdf.data,filetype="pdf") as released,fitz.open(source) as original:
                            self.assertEqual(released[0].get_pixmap().samples,original[0].get_pixmap().samples)
                        print("ALL_SK_DOWNLOAD_OK",key,flush=True)
            for access in (False,True):
                cat=catalog_data(root=ROOT,personalization_allowed=access)
                ready={f"{s['code']}:{y['year']}" for s in cat["subjects"] for y in s["years"] if y.get("docx_ready")}
                self.assertEqual(set(manifest["files"])&ready,set(manifest["files"]) if access else set())
if __name__=="__main__":unittest.main()
