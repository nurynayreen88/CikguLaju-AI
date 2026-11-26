"""Actual protected RTL Word and unchanged PDF route tests for all ten sources."""
import io,json,unittest
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
from flask import Flask
from PIL import Image
from docx import Document
from docx.oxml.ns import qn
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint,catalog_data
from web.rpt_compact_pdf import RTL_PINS
from web.rpt_native_word_cover import cover_png
from tools.build_kssr_rpt_rtl_native_20261126 import HEADERS,build_word
class RTLNativeWordTest(unittest.TestCase):
    def test_real_downloads(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        base=ROOT/"web_2027_pdfs"
        lock=json.loads((base/"original_cover_layout_verified.json").read_text())
        crest=io.BytesIO();Image.new("RGB",(64,64),"#28553a").save(crest,format="PNG")
        identity={"school":"SEKOLAH KEBANGSAAN CONTOH","teacher":"GURU CONTOH","state":"","logo":crest.getvalue()}
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        flags={"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1","CIKGULAJU_RPT_NATIVE_RTL_WORD":"1","CIKGULAJU_RPT_COMPACT_PDF_BATCH":"1"}
        with patch.dict("os.environ",flags),patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}),patch("web.rpt_school_cover.school_identity",return_value=identity):
            for key,digest in RTL_PINS.items():
                with self.subTest(key=key):
                    subject,y=key.split(":");year=int(y);url=f"/api/rpt/2027/all/{subject}/{year}"
                    source=base/subject/f"tahun_{year}.pdf"
                    self.assertEqual(sha256(source.read_bytes()).hexdigest(),digest)
                    with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                        self.assertEqual(client.get(url+".docx").status_code,403)
                        pdf=client.get(url+".pdf");self.assertEqual(pdf.status_code,200)
                    with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                        self.assertEqual(client.get(url+".pdf").data,pdf.data)
                        word=client.get(url+".docx")
                        self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else key)
                        self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                        doc=Document(io.BytesIO(word.data))
                        expected=Document(io.BytesIO(build_word(subject,year)[0]))
                        self.assertEqual([t._tbl.xml for t in doc.tables],[t._tbl.xml for t in expected.tables])
                        for t in doc.tables:
                            self.assertEqual([c.text for c in t.rows[0].cells],list(HEADERS))
                            self.assertIsNotNone(t._tbl.tblPr.find(qn("w:bidiVisual")))
                        rid=doc.paragraphs[0]._p.xpath(".//a:blip")[0].get(qn("r:embed"))
                        self.assertEqual(doc.part.related_parts[rid].blob,cover_png(source.read_bytes(),lock,key,identity))
            for access in (True,False):
                data=catalog_data(root=ROOT,personalization_allowed=access)
                advertised={f"{s['code']}:{y['year']}" for s in data["subjects"] for y in s["years"] if y.get("docx_ready")}
                self.assertEqual(set(RTL_PINS)&advertised,set(RTL_PINS) if access else set())
if __name__=="__main__":unittest.main()
