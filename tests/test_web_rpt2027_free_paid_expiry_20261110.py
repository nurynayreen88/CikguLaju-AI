"""RPT 2027: free and expired accounts retain access without printed school identity."""
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from flask import Flask, jsonify
from web.english_rpt_2027_http import (
    _has_paid_access, create_english_rpt_blueprint,
)

class RPTFreeAndPaidExpiryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.original=b"%PDF-"+b"x"*9017
        (self.root/"RPT_ENGLISH_TAHUN_2_2027_UNTUK_GURU.pdf").write_bytes(self.original)
        self.app=Flask(__name__)
        self.app.register_blueprint(create_english_rpt_blueprint(self.root))
        self.client=self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_entitlements_expired_active_and_lifetime(self):
        self.assertFalse(_has_paid_access({"authenticated":True,"vip_expires_at":"2000-01-01T00:00:00Z"}))
        self.assertFalse(_has_paid_access({"authenticated":True,"vip_until":"2000-01-01"}))
        self.assertFalse(_has_paid_access({"authenticated":True,"free_remaining":10}))
        self.assertTrue(_has_paid_access({"authenticated":True,"vip_expires_at":"2999-01-01T00:00:00Z"}))
        self.assertTrue(_has_paid_access({"authenticated":True,"rakan_pembangun":True}))

    def test_expired_account_has_exact_original_pdf_and_no_school_fetch(self):
        expired={"telegram_user_id":12,"authenticated":True,
                 "vip_expires_at":"2000-01-01T00:00:00Z"}
        with (patch("web.english_rpt_2027_http._account",return_value=(expired,None)),
              patch("web.rpt_school_cover.for_download") as cover):
            catalog=self.client.get("/api/rpt/2027/english")
            self.assertEqual(catalog.status_code,200)
            self.assertTrue(catalog.json["allowed"])
            self.assertFalse(catalog.json["personalization_allowed"])
            result=self.client.get("/api/rpt/2027/english/2.pdf")
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.data,self.original)
            self.assertEqual(result.headers["X-RPT-Personalization-Allowed"],"0")
            cover.assert_not_called()

    def test_paid_english_route_uses_server_personalization(self):
        lifetime={"telegram_user_id":12,"authenticated":True,"rakan_pembangun":True}
        stamped=b"%PDF-"+b"PERSONALIZED"*900
        with (patch("web.english_rpt_2027_http._account",return_value=(lifetime,None)),
              patch("web.rpt_school_cover.for_download",return_value=BytesIO(stamped)) as cover):
            result=self.client.get("/api/rpt/2027/english/2.pdf")
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.data,stamped)
            self.assertEqual(result.headers["X-RPT-Personalization-Allowed"],"1")
            cover.assert_called_once()

    def test_unauthenticated_cannot_fetch_even_free_pdf(self):
        with patch("web.english_rpt_2027_http._account",
                   side_effect=lambda:(None,(jsonify({"error":"Login required"}),401))):
            self.assertEqual(self.client.get("/api/rpt/2027/english/2.pdf").status_code,401)

if __name__=="__main__":
    unittest.main()
