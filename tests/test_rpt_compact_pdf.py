import json
import hashlib
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from flask import Flask
from web import rpt_compact_pdf
from web.rpt_native_word_batch import PINS
from web.rpt_2027_all_http import ROOT,create_all_rpt_blueprint

class CompactPDFTests(unittest.TestCase):
    def test_all_sources_and_paid_free_route(self):
        manifest=json.loads((ROOT/"compact_free_pdf_2027"/"manifest.json").read_text())["files"]
        app=Flask(__name__)
        app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        for key,e in manifest.items():
            subject,year=key.split(":")
            original=(ROOT/"web_2027_pdfs"/e["path"]).read_bytes()
            url=f"/api/rpt/2027/all/{subject}/{year}.pdf"
            with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"0"}),patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9},None)):
                self.assertEqual(client.get(url).data,original)
            with patch.dict("os.environ",{"CIKGULAJU_RPT_COMPACT_PDF_BATCH":"1"}):
                result=rpt_compact_pdf.read(subject,int(year),original,root=ROOT)
                self.assertIsNotNone(result,key)
                raw,digest=result
                self.assertEqual(hashlib.sha256(raw).hexdigest(),e["sha256"])
                self.assertIsNone(rpt_compact_pdf.read(subject,int(year),original+b"x",root=ROOT))
                with fitz.open(stream=original,filetype="pdf") as old,fitz.open(stream=raw,filetype="pdf") as new:
                    self.assertEqual(old[0].get_pixmap().samples,new[0].get_pixmap().samples)
                for paid in (False,True):
                    with patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"rakan_pembangun":paid},None)):
                        res=client.get(url)
                        self.assertEqual(res.status_code,200,key)
                        self.assertEqual(res.data,raw,key)
                        self.assertEqual(res.headers["X-RPT-Source-SHA256"],digest)
                        self.assertEqual(res.headers["X-RPT-Personalization-Allowed"],"1" if paid else "0")
                        self.assertIn("attachment",res.headers["Content-Disposition"])
    def test_browser_accepts_both_original_and_compact_cover_digests(self):
        script=Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"rpt-personalize.js"
        layout=ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json"
        code="""const {validatedLayout}=require(process.argv[1]);
const layout=require(process.argv[2]);
const compact=layout.compact_pdf_covers;
for(const [key,hash] of Object.entries(compact.source_sha256_by_subject_year)){
 if(validatedLayout(layout,key,hash)!==compact)throw Error(key);
 if(validatedLayout(layout,key,layout.source_sha256_by_subject_year[key])!==layout)throw Error(key);
}"""
        subprocess.run(["node","-e",code,str(script),str(layout)],check=True)
if __name__=="__main__":unittest.main()
