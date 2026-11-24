import unittest
from io import BytesIO
from unittest.mock import patch
from flask import Flask
from web.unified_rph_web import create_blueprint,source_records
from web.akuatik_v2_web_client import kssr_id,KP2027

class AquaticsV2WebTest(unittest.TestCase):
    def test_exact_allowlist(self):
        self.assertEqual(KP2027,{("A",51):"KP2027-A-051",("B",50):"KP2027-B-050"})
        for y,n in ((3,22),(3,23),(4,26)):
            self.assertEqual(kssr_id(y,"PJPK","PJ",f"p-{y}-PJ-{n:03d}"),f"{n:03d}")
        self.assertIsNone(kssr_id(4,"PJPK","PJ","p-4-PJ-025"))
        self.assertIsNone(kssr_id(3,"PJPK","PK","p-3-PJ-022"))
        self.assertIsNone(kssr_id(2,"PJPK","PJ","p-2-PJ-022"))
    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":123},None))
    def test_same_paid_gate_and_exact_source(self,*_):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        client=app.test_client()
        row=next(x for x in source_records(3,"PJPK","PJ") if x["lesson"]==22)
        args={"year":3,"subject":"PJPK","component":"PJ","unit":row["unit"],"lesson":row["token"],"rph_variant":"V2_DARAT"}
        with patch("web.akuatik_v2_web_client.request_document",return_value=BytesIO(b"%PDF-1.4\n"+b"0"*1200)) as native:
            result=client.get("/api/web/rph/pdf",query_string=args)
            self.assertEqual(result.status_code,200,result.get_json() if result.is_json else "")
            self.assertIn("AKUATIK_V2",result.headers["Content-Disposition"])
            self.assertEqual(native.call_args.args[:3],(3,"022","pdf"))
            denied=client.get("/api/web/rph/pdf",query_string={**args,"lesson":"p-3-PJ-021"})
            self.assertEqual(denied.status_code,400)
            self.assertEqual(native.call_count,1)

if __name__=="__main__":unittest.main()
