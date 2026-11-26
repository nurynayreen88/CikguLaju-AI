import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from flask import Flask
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint
from web.rpt_compact_pdf import read_approved
from rpt_2027.matematik import sk_documents as math
from rpt_2027.sains import sk_documents as science

class ApprovedCompactTest(unittest.TestCase):
    def test_all_five_routes_and_covers(self):
        m=json.loads((ROOT/"compact_approved_pdf_2027"/"manifest.json").read_text())
        self.assertEqual(m["count"],5)
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        for key,e in m["files"].items():
            subject,y=key.split(":");year=int(y)
            old=(math if subject=="matematik" else science).document_path(year,root=ROOT/subject)
            original=old.read_bytes()
            url=f"/api/rpt/2027/all/{subject}/{year}.pdf"
            with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"0"}),patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9},None)):
                self.assertEqual(client.get(url).data,original)
            with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"1"}):
                raw,digest=read_approved(subject,year,original,root=ROOT)
                self.assertEqual(digest,e["sha256"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
                self.assertIsNone(read_approved(subject,year,original+b"x",root=ROOT))
                with fitz.open(old) as a,fitz.open(stream=raw,filetype="pdf") as b:
                    self.assertEqual(a[0].get_pixmap().samples,b[0].get_pixmap().samples)
                    self.assertEqual(len(b),e["pages"])
                    self.assertTrue(all(p.get_text().strip() for p in list(b)[1:]))
                for paid in (False,True):
                    with patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"rakan_pembangun":paid},None)):
                        result=client.get(url)
                        self.assertEqual(result.status_code,200,key)
                        self.assertEqual(result.data,raw)
                        self.assertEqual(result.headers["X-RPT-Source-SHA256"],digest)
                        self.assertEqual(result.headers["X-RPT-Personalization-Allowed"],"1" if paid else "0")
    def test_browser_cover_hashes(self):
        script=Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"rpt-personalize.js"
        layout=ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json"
        code="""const {validatedLayout}=require(process.argv[1]);const l=require(process.argv[2]);
for(const [k,v] of Object.entries(l.compact_approved_pdf_covers)){
 if(validatedLayout(l,k,v.source_sha256_by_subject_year[k])!==v)throw Error(k);
}"""
        subprocess.run(["node","-e",code,str(script),str(layout)],check=True)
