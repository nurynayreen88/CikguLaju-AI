"""Route regression for DPK-only Word; no production or user-data access."""
import io
import json
import unittest
from unittest.mock import patch
from hashlib import sha256
from docx import Document
from PIL import Image
from flask import Flask
from rpt_2027.matematik import sk_documents
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint,catalog_data
from web.rpt_native_word_cover import cover_png
from web import rpt_math_dpk_word

class DPKWordDownloads(unittest.TestCase):
    def test_real_documents_and_paid_only_gate(self):
        app=Flask(__name__)
        app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        lock=json.loads((ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
        image=io.BytesIO()
        Image.new("RGB",(48,48),"#28553a").save(image,format="PNG")
        identity={"school":"SEKOLAH KEBANGSAAN CONTOH","teacher":"GURU CONTOH","state":"","logo":image.getvalue()}
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}),patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}),patch("web.rpt_school_cover.school_identity",return_value=identity):
            for year,digest in sk_documents.DPK_DIGESTS.items():
                key=f"matematik_dpk:{year}"
                url=f"/api/rpt/2027/all/matematik_dpk/{year}"
                source=sk_documents.document_path(year,dpk=True,root=ROOT/"matematik").read_bytes()
                self.assertEqual(sha256(source).hexdigest(),digest)
                with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                    self.assertEqual(client.get(url+".docx").status_code,403)
                    self.assertEqual(client.get(url+".pdf").data,source)
                with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                    response=client.get(url+".docx")
                    self.assertEqual(response.status_code,200,response.get_data(as_text=True) if response.status_code!=200 else year)
                    self.assertIn("attachment",response.headers["Content-Disposition"])
                    self.assertEqual(response.headers["Cache-Control"],"no-store, private")
                    self.assertEqual(response.headers["X-RPT-Source-SHA256"],digest)
                    self.assertEqual(client.get(url+".pdf").data,source)
                    doc=Document(io.BytesIO(response.data))
                    self.assertEqual(len(doc.tables),1)
                    self.assertTrue(doc.tables[0].rows[0]._tr.xpath(".//w:tblHeader"))
                    from docx.oxml.ns import qn
                    rid=doc.paragraphs[0]._p.xpath(".//a:blip")[0].get(qn("r:embed"))
                    self.assertEqual(doc.part.related_parts[rid].blob,cover_png(source,lock,key,identity))
                    self.assertEqual(client.get("/api/rpt/2027/all/matematik_dpk/4.docx").status_code,404)
                for access in (True,False):
                    cat=catalog_data(root=ROOT,personalization_allowed=access)
                    dpk=next(x for x in cat["subjects"] if x["code"]=="matematik_dpk")
                    entry=next(x for x in dpk["years"] if x["year"]==year)
                    self.assertEqual(entry["docx_ready"],access)
                    self.assertEqual(entry["docx_url"],url+".docx" if access else None)
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"0"}):
            self.assertFalse(rpt_math_dpk_word.eligible(2,root=ROOT))
            with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                self.assertEqual(client.get("/api/rpt/2027/all/matematik_dpk/2.docx").status_code,503)

if __name__=="__main__":
    unittest.main()
