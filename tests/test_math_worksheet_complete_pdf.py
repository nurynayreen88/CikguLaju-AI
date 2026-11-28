import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from web import math_worksheet_complete_pdf as m
from web.unified_rph_web import create_blueprint

class MathWorksheetTests(unittest.TestCase):
    def setUp(self):
        self.unit="u"+"1"*24
        self.token="M2-PDP-TEST"
        self.row={"available":True,"year":2,"subject":"MATH",
                  "unit":self.unit,"token":self.token,
                  "topic":"Nilai Tempat dan Nilai Digit",
                  "standards":[{"sk":"1.4","sp":"1.4.1"}]}
        self.catalog=json.loads(m.CATALOG.read_text())
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"catalog.json"
        self.patch=patch.object(m,"CATALOG",self.path)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.path.write_text(json.dumps(self.catalog))

    def test_unmapped_is_hidden(self):
        with patch.object(m,"_read",return_value=self.row):
            self.assertIsNone(m.resolve_math(2,self.unit,self.token))

    def test_exact_mapping_only(self):
        rec=self.catalog["records"][0]
        rec.update(runtime_unit=self.unit,runtime_lesson=self.token)
        self.path.write_text(json.dumps(self.catalog))
        with patch.object(m,"_read",return_value=self.row):
            self.assertIsNotNone(m.resolve_math(2,self.unit,self.token))
            with patch.object(m,"_pdf",return_value=b"%PDF-1.7") as pdf:
                for kind,key in (("murid","student"),("skema","teacher_key")):
                    raw,name=m.complete_math_pdf(2,self.unit,self.token,kind)
                    self.assertTrue(name.endswith(kind.upper()+".pdf"))
                    asset=rec[key]
                    pdf.assert_called_with(asset["drive_file_id"],asset["sha256"],asset["size_bytes"])
            self.assertIsNone(m.complete_math_pdf(2,self.unit,self.token,"other"))
        for invalid in ({"topic":"Other"},{"token":"other"},{"unit":"other"},
                        {"standards":[{"sk":"1.4","sp":"1.4.2"}]},
                        {"standards":[{"sk":"1.4","sp":"1.4.1"},{"sk":"1.4","sp":"1.4.2"}]}):
            with patch.object(m,"_read",return_value={**self.row,**invalid}):
                self.assertIsNone(m.resolve_math(2,self.unit,self.token))

    def test_web_routes_and_original_bytes(self):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        c=app.test_client()
        args={"year":2,"subject":"MATH","unit":self.unit,"lesson":self.token}
        account={"telegram_user_id":1,"authenticated":True,"free_remaining":1}
        with patch("web.unified_rph_web._account",return_value=(account,None)):
            with patch.object(m,"resolve_math",return_value=None):
                self.assertEqual(c.get("/api/web/rph/extra-materials",query_string=args).json["items"],[])
            with patch.object(m,"resolve_math",return_value=self.catalog["records"][0]):
                items=c.get("/api/web/rph/extra-materials",query_string=args).json["items"]
                self.assertEqual(len(items),2)
                for item in items:
                    with patch.object(m,"complete_math_pdf",return_value=(b"%PDF-1.7","test.pdf")):
                        response=c.get(item["url"])
                        self.assertEqual(response.status_code,200)
                        self.assertEqual(response.data,b"%PDF-1.7")
            with patch.object(m,"complete_math_pdf",return_value=None):
                self.assertEqual(c.get("/api/web/rph/math-worksheet-pdf/murid",query_string=args).status_code,404)

if __name__=="__main__":
    unittest.main()
