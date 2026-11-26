import hashlib,io,json,subprocess,unittest,re
from pathlib import Path
from unittest.mock import patch
import fitz
from PIL import Image
from docx import Document
from flask import Flask
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint
from web.rpt_compact_pdf import read_full_standards_dlp
from web.rpt_native_word_cover import cover_png
from tools.build_rpt_dlp_native_20261126 import PINS,document_path
from tools.build_rpt_dlp_full_standards_20261126 import build_word,HEADS
class FullDLPTest(unittest.TestCase):
    def test_ten_routes_and_profile(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint());client=app.test_client()
        m=json.loads((ROOT/"full_standards_dlp_pdf_2027"/"manifest.json").read_text())
        lock=json.loads((ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
        self.assertEqual(set(m["files"]),set(PINS))
        logo=io.BytesIO();Image.new("RGB",(64,64),"#2b6841").save(logo,format="PNG")
        identity={"school":"SEKOLAH KEBANGSAAN CONTOH","teacher":"GURU CONTOH","state":"","logo":logo.getvalue()}
        for key,e in m["files"].items():
            subject,y=key.split(":");year=int(y)
            source=document_path(subject,year,root=ROOT/"dlp")
            original=source.read_bytes();self.assertEqual(hashlib.sha256(original).hexdigest(),PINS[key])
            url=f"/api/rpt/2027/all/{subject}/{year}"
            with patch.dict("os.environ",{"CIKGULAJU_RPT_FULL_STANDARDS_DLP":"1","CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}):
                raw,digest=read_full_standards_dlp(subject,year,original,root=ROOT)
                self.assertEqual(digest,e["sha256"])
                self.assertIsNone(read_full_standards_dlp(subject,year,original+b"x",root=ROOT))
                with fitz.open(stream=raw,filetype="pdf") as pdf:
                    first=pdf[0].get_text()
                    self.assertIn("LOGO SEKOLAH",first);self.assertIn("NAMA SEKOLAH",first);self.assertIn("NAMA GURU",first)
                    self.assertNotRegex(first,r"(?i)cuti|school breaks|teaching allocation")
                    self.assertIn("Main school breaks",pdf[-1].get_text())
                with patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9},None)):
                    self.assertEqual(client.get(url+".pdf").data,raw)
                    self.assertEqual(client.get(url+".docx").status_code,403)
                with patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"rakan_pembangun":True},None)),patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}),patch("web.rpt_school_cover.school_identity",return_value=identity):
                    res=client.get(url+".pdf");self.assertEqual(res.data,raw)
                    self.assertEqual(res.headers["X-RPT-Source-SHA256"],digest)
                    self.assertEqual(res.headers["X-RPT-Personalization-Allowed"],"1")
                    from web.rpt_native_word_batch import dlp_document
                    dlp_document(subject,year,{"telegram_user_id":9,"rakan_pembangun":True},{"account_backend":"supabase"},root=ROOT)
                    word=client.get(url+".docx");self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else key)
                    doc=Document(io.BytesIO(word.data));self.assertEqual([c.text for c in doc.tables[0].rows[0].cells],list(HEADS))
                    self.assertGreater(len(doc.tables),2)
                    for table in doc.tables[:-1]:
                        self.assertEqual([c.text for c in table.rows[0].cells],list(HEADS))
                    for row in (r for t in doc.tables[:-1] for r in t.rows[1:]):
                        for cell in row.cells[2:4]:
                            self.assertRegex(cell.text,r"\d+\.\d+.*[A-Za-z]")
                    self.assertTrue(any("Main school breaks" in p.text for p in doc.paragraphs))
                    from docx.oxml.ns import qn
                    for table in doc.tables:
                        pr=table._tbl.tblPr
                        self.assertEqual(pr.find(qn("w:tblW")).get(qn("w:type")),"dxa")
                        self.assertEqual(int(pr.find(qn("w:tblW")).get(qn("w:w"))),sum(c.width.twips for c in table.columns))
                        self.assertIsNotNone(pr.find(qn("w:tblCellMar")))
                        self.assertIsNotNone(pr.find(qn("w:tblBorders")))
                    rid=doc.paragraphs[0]._p.xpath(".//a:blip")[0].get(qn("r:embed"))
                    self.assertEqual(doc.part.related_parts[rid].blob,cover_png(raw,lock,key,identity))
                with patch.dict("os.environ",{"CIKGULAJU_RPT_FULL_STANDARDS_DLP":"0"}):
                    self.assertIsNone(read_full_standards_dlp(subject,year,original,root=ROOT))
    def test_browser_cover(self):
        script=Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"rpt-personalize.js"
        lock=ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json"
        code="""const {validatedLayout}=require(process.argv[1]);const l=require(process.argv[2]);const c=l.full_standards_dlp_pdf_covers;for(const [k,v] of Object.entries(c.source_sha256_by_subject_year)){if(validatedLayout(l,k,v)!==c)throw Error(k);}"""
        subprocess.run(["node","-e",code,str(script),str(lock)],check=True)
