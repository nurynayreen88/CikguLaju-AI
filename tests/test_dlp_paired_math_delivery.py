"""Verify installed session payloads against the actual protected API.
Approval is mocked only in the test process; never rewrite release metadata.
"""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json,hashlib,unittest
import fitz
from docx import Document
from flask import Flask
from web.native_rph_telegram_api import create_native_rph_blueprint
from web import dlp_paired_session_delivery as paired

class PairedMathTests(unittest.TestCase):
    def test_real_private_downloads(self):
        app=Flask(__name__)
        app.register_blueprint(create_native_rph_blueprint(SimpleNamespace(create_word_file=lambda:None,create_pdf_file=lambda:None)))
        c=app.test_client()
        path="/internal/rph/v1/dlp"
        headers={"Authorization":"Bearer "+"t"*40}
        manifest=json.loads((paired.ROOT/"manifest.json").read_text())
        data={}
        for year in (3,4,5,6):
            raw=(paired.ROOT/f"MATH_DLP_{year}.json").read_bytes()
            assert hashlib.sha256(raw).hexdigest()==manifest["sets"][f"MATH_DLP:{year}"]["sha256"]
            data[year]=json.loads(raw)
        teacher={"class":"QA Bestari","date":"2027-01-12","time":"08:00 - 09:00","students":"30","reflection":""}
        env={"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1","CIKGULAJU_AUTHORITATIVE_API_TOKEN":"t"*40,"CIKGULAJU_DLP_PAIRED_MATH_YEARS":""}
        with patch.dict("os.environ",env):
            s={"year":3,"subject":"MATH_DLP","unit":"sessions","lesson":"SESSION-001"}
            self.assertEqual(c.get(path+"/availability",query_string=s,headers=headers).status_code,404)
            self.assertEqual(c.get(path+"/availability",query_string=s).status_code,401)
        env["CIKGULAJU_DLP_PAIRED_MATH_YEARS"]="3,4,5,6"
        with patch.dict("os.environ",env),patch.object(paired,"_load",side_effect=lambda y,s:data[y]):
            for y,rows in data.items():
                catalogue=c.get(path+f"/year{y}-mathematics/catalogue",headers=headers)
                self.assertEqual(catalogue.status_code,200)
                unit=next(u for u in catalogue.json["units"] if u["id"]=="sessions")
                self.assertEqual(len(unit["lessons"]),101)
                for row in rows:
                    with self.subTest(year=y,session=row["session"]):
                        s={"year":y,"subject":"MATH_DLP","unit":"sessions","lesson":f"SESSION-{row['session']:03d}"}
                        self.assertEqual(c.get(path+"/availability",query_string=s,headers=headers).status_code,200)
                        t=teacher|{"time":"08:00 - 08:30" if row["minutes"]==30 else teacher["time"]}
                        for fmt in ("word","pdf"):
                            resp=c.post(path+"/render",headers=headers,json={"format":fmt,"selection":s,"teacher":t})
                            self.assertEqual(resp.status_code,200,resp.data[:300])
                            if fmt=="word":
                                doc=Document(BytesIO(resp.data))
                                txt=" ".join(x.text for table in doc.tables for r in table.rows for x in r.cells)
                            else:
                                with fitz.open(stream=resp.data,filetype="pdf") as doc:
                                    self.assertEqual(len(doc),1)
                                    txt=doc[0].get_text()
                            self.assertIn("QA Bestari",txt)
                            self.assertIn("2027-01-12",txt)
                            self.assertIn("Obj. 1:",txt)
                        if row["session"]==1:
                            resp=c.post(path+"/render",headers=headers,json={"format":"word","selection":s,"teacher":t|{"reflection":"Manual QA reflection."}})
                            self.assertEqual(resp.status_code,200)
                            self.assertIn("Manual QA reflection.",Document(BytesIO(resp.data)).tables[-1].cell(0,1).text)
                s={"year":y,"subject":"MATH_DLP","unit":"sessions","lesson":"SESSION-102"}
                self.assertEqual(c.get(path+"/availability",query_string=s,headers=headers).status_code,404)

if __name__=="__main__":unittest.main()
