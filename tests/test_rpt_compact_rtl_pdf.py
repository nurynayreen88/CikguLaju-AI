import hashlib,json,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from flask import Flask
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint
from web.rpt_compact_pdf import read_rtl,RTL_PINS
from scripts.build_web_rpt_weekly_suggestions import read_weeks,SUBJECTS
class CompactRTLTest(unittest.TestCase):
    def test_ten_routes_and_covers(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint());client=app.test_client()
        m=json.loads((ROOT/"compact_rtl_pdf_2027"/"manifest.json").read_text())
        self.assertEqual(m["count"],10)
        self.assertEqual(set(m["files"]),set(RTL_PINS))
        for key,e in m["files"].items():
            subject,y=key.split(":");year=int(y)
            source=ROOT/"web_2027_pdfs"/e["path"]
            original=source.read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(),RTL_PINS[key])
            url=f"/api/rpt/2027/all/{subject}/{year}.pdf"
            with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"0"}),patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9},None)):
                self.assertEqual(client.get(url).data,original,key)
            with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"1"}):
                raw,digest=read_rtl(subject,year,original,root=ROOT)
                self.assertEqual(digest,e["sha256"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
                self.assertIsNone(read_rtl(subject,year,original+b"x",root=ROOT))
                with fitz.open(stream=original,filetype="pdf") as a,fitz.open(stream=raw,filetype="pdf") as b:
                    self.assertEqual(a[0].get_pixmap().samples,b[0].get_pixmap().samples)
                    self.assertEqual(len(b),e["pages"])
                    self.assertLessEqual(len(b),len(a))
                    self.assertTrue(all(p.get_text().strip() for p in list(b)[1:]))
                self.assertEqual(read_weeks(source,SUBJECTS[subject]),read_weeks(ROOT/"compact_rtl_pdf_2027"/e["path"],SUBJECTS[subject]))
                for paid in (False,True):
                    with patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"rakan_pembangun":paid},None)):
                        res=client.get(url);self.assertEqual(res.status_code,200,key)
                        self.assertEqual(res.data,raw,key)
                        self.assertEqual(res.headers["X-RPT-Source-SHA256"],digest)
                        self.assertEqual(res.headers["X-RPT-Personalization-Allowed"],"1" if paid else "0")
    def test_browser_cover(self):
        script=Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"rpt-personalize.js"
        lock=ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json"
        code="""const {validatedLayout}=require(process.argv[1]);const l=require(process.argv[2]);const c=l.compact_rtl_pdf_covers;
for(const [k,v] of Object.entries(c.source_sha256_by_subject_year)){if(validatedLayout(l,k,v)!==c)throw Error(k);}"""
        subprocess.run(["node","-e",code,str(script),str(lock)],check=True)
