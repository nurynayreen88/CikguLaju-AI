import hashlib,json,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from flask import Flask
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint
from web.rpt_compact_pdf import read_language
class CompactLanguageTest(unittest.TestCase):
    def test_ten_routes_and_covers(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint());client=app.test_client()
        for code,subject in (("bm","bahasa_melayu"),("english","english")):
            m=json.loads((ROOT/f"compact_{code}_pdf_2027"/"manifest.json").read_text())
            self.assertEqual(m["count"],5)
            for key,e in m["files"].items():
                y=int(key.split(":")[1])
                source=ROOT/"web_2027_pdfs"/e["path"] if code=="bm" else ROOT/"english"/f"RPT_English_SK_2027_Year_{y}_A_B.pdf"
                original=source.read_bytes()
                url=f"/api/rpt/2027/all/{subject}/{y}.pdf"
                with patch("web.native_telegram_integrated_english_client.integrated_enabled",return_value=True):
                    with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"0"}),patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9},None)):
                        self.assertEqual(client.get(url).data,original,key)
                    with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"1"}):
                        raw,digest=read_language(subject,y,original,root=ROOT)
                        self.assertEqual(digest,e["sha256"])
                        self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
                        self.assertIsNone(read_language(subject,y,original+b"x",root=ROOT))
                        with fitz.open(stream=original,filetype="pdf") as a,fitz.open(stream=raw,filetype="pdf") as b:
                            self.assertEqual(a[0].get_pixmap().samples,b[0].get_pixmap().samples)
                            self.assertEqual(len(b),e["pages"])
                            self.assertTrue(all(p.get_text().strip() for p in list(b)[1:]))
                        for paid in (False,True):
                            with patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"rakan_pembangun":paid},None)):
                                res=client.get(url);self.assertEqual(res.status_code,200,key)
                                self.assertEqual(res.data,raw,key)
                                self.assertEqual(res.headers["X-RPT-Source-SHA256"],digest)
                                self.assertEqual(res.headers["X-RPT-Personalization-Allowed"],"1" if paid else "0")
    def test_browser_cover(self):
        script=Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"rpt-personalize.js"
        lock=ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json"
        code="""const {validatedLayout}=require(process.argv[1]);const l=require(process.argv[2]);
for(const type of ["bm","english"]){const c=l["compact_"+type+"_pdf_covers"];for(const [k,v] of Object.entries(c.source_sha256_by_subject_year)){if(validatedLayout(l,k,v)!==c)throw Error(k);}}"""
        subprocess.run(["node","-e",code,str(script),str(lock)],check=True)
