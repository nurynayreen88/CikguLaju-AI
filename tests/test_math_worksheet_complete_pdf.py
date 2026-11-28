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

    def test_both_verified_live_pdp_share_one_original_pair(self):
        records=[r for r in self.catalog["records"] if r["title"]=="Nilai Tempat dan Nilai Digit"]
        self.assertEqual(self.catalog["unique_worksheet_count"],6)
        self.assertEqual(self.catalog["mapped_pdp_count"],8)
        self.assertEqual({r["runtime_lesson"] for r in records},{"MT2-PDP-006","MT2-PDP-007"})
        self.assertEqual(len({r["student"]["sha256"] for r in records}),1)
        self.assertEqual(len({r["teacher_key"]["sha256"] for r in records}),1)
        for record in records:
            row={**self.row,"unit":record["runtime_unit"],"token":record["runtime_lesson"]}
            with patch.object(m,"_read",return_value=row):
                self.assertEqual(m.resolve_math(2,row["unit"],row["token"]),record)
                self.assertIsNone(m.resolve_math(2,row["unit"],"MT2-PDP-008"))

    def test_three_new_exact_pairs_and_filenames(self):
        expected = {
            "MT2-PDP-008": ("CERAKIN_NOMBOR", "1.4.2"),
            "MT2-PDP-009": ("BANDING_NOMBOR", "1.1.2(iii)"),
            "MT2-PDP-010": ("SUSUN_NOMBOR", "1.1.2(iv)"),
        }
        records = [r for r in self.catalog["records"] if r["runtime_lesson"] in expected]
        self.assertEqual({r["runtime_lesson"] for r in records}, set(expected))
        for rec in records:
            token,unit = rec["runtime_lesson"],rec["runtime_unit"]
            slug,sp = expected[token]
            row = {**self.row,"unit":unit,"token":token,"topic":rec["title"],
                   "standards":[{"sk":rec["sk"],"sp":sp.replace("("," (")}]}
            with patch.object(m,"_read",return_value=row):
                self.assertEqual(m.resolve_math(2,unit,token),rec)
                with patch.object(m,"_pdf",return_value=b"%PDF-1.7") as pdf:
                    for kind,key in (("murid","student"),("skema","teacher_key")):
                        raw,name=m.complete_math_pdf(2,unit,token,kind)
                        self.assertEqual(name,"CIKGULAJU_LATIHAN_MATH_T2_"+slug+"_"+kind.upper()+".pdf")
                        asset=rec[key]
                        pdf.assert_called_with(asset["drive_file_id"],asset["sha256"],asset["size_bytes"])
                self.assertIsNone(m.resolve_math(2,unit,"MT2-PDP-012"))
            for invalid in ({"topic":"Other"},{"standards":[{"sk":rec["sk"],"sp":"1.1.2"}]},
                            {"standards":[{"sk":rec["sk"],"sp":"1.1.2(ii)"}]}):
                with patch.object(m,"_read",return_value={**row,**invalid}):
                    self.assertIsNone(m.resolve_math(2,unit,token))

    def test_new_shared_and_composite_pdp_keep_exact_standards(self):
        expected = {
            "MT2-PDP-004": ("Nilai Nombor","1.1","1.1.2(i)"),
            "MT2-PDP-005": ("Nilai Nombor","1.1","1.1.2(ii)"),
            "MT2-PDP-011": ("Bilang Nombor","1.3","1.3.1;1.3.2"),
        }
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        client=app.test_client()
        account={"telegram_user_id":1,"authenticated":True,"free_remaining":1}
        records=[r for r in self.catalog["records"] if r["runtime_lesson"] in expected]
        self.assertEqual(len(records),3)
        for rec in records:
            token,unit=rec["runtime_lesson"],rec["runtime_unit"]
            title,sk,sp=expected[token]
            row={**self.row,"unit":unit,"token":token,"topic":title,
                 "standards":[{"sk":sk,"sp":sp}]}
            with patch.object(m,"_read",return_value=row):
                self.assertEqual(m.resolve_math(2,unit,token),rec)
                with patch("web.unified_rph_web._account",return_value=(account,None)):
                    items=client.get("/api/web/rph/extra-materials",
                        query_string={"year":2,"subject":"MATH","unit":unit,"lesson":token}).json["items"]
                    self.assertEqual(len(items),2)
                    self.assertEqual(items[0]["title"],"Lembaran Latihan Murid"+
                        (" — latihan bersama PdP 004–005" if token!="MT2-PDP-011" else ""))
                with patch.object(m,"_pdf",return_value=b"%PDF-1.7") as pdf:
                    for kind,key in (("murid","student"),("skema","teacher_key")):
                        raw,name=m.complete_math_pdf(2,unit,token,kind)
                        self.assertEqual(name,"CIKGULAJU_LATIHAN_MATH_T2_"+title.upper().replace(" ","_")+"_"+kind.upper()+".pdf")
                        asset=rec[key]
                        pdf.assert_called_with(asset["drive_file_id"],asset["sha256"],asset["size_bytes"])
            wrong_sp={"MT2-PDP-004":"1.1.2(ii)","MT2-PDP-005":"1.1.2(i)","MT2-PDP-011":"1.3.1"}[token]
            with patch.object(m,"_read",return_value={**row,"standards":[{"sk":sk,"sp":wrong_sp}]}):
                self.assertIsNone(m.resolve_math(2,unit,token))

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
