"""Authenticated payment intent audit; no payment approval or wallet assertion."""
import json
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError
from flask import Flask
from web.web_payment_routes import bp, _audit_payment_event

CONF={"supabase_url":"https://unit.supabase.co","supabase_key":"test-private-key-12345678901234567890"}
class Reply:
    status=201
    def __enter__(self):return self
    def __exit__(self,*args):return None
class Transport:
    def __init__(self):self.requests=[]
    def open(self,req,timeout):
        self.requests.append(req)
        return Reply()
class AuditTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(bp)
        self.client=app.test_client()
        a=patch("web.web_payment_routes._auth",return_value=(CONF,712,None))
        a.start();self.addCleanup(a.stop)

    def test_audit_sends_immutable_user_id_only_to_private_server_endpoint(self):
        t=Transport()
        _audit_payment_event(CONF,712,"receipt_failed",
                             error_code="telegram_unavailable",opener=t)
        self.assertEqual(len(t.requests),1)
        req=t.requests[0]
        self.assertTrue(req.full_url.endswith("/rest/v1/web_payment_attempt_events"))
        body=json.loads(req.data)
        self.assertEqual(body["telegram_user_id"],712)
        self.assertEqual(body["event_type"],"receipt_failed")
        self.assertEqual(body["error_code"],"telegram_unavailable")
        self.assertNotIn("receipt",body.keys())

    def test_qr_open_records_id_without_affecting_payment_status(self):
        catalog={"mode":"manual_receipt_review","telegram_bot_id":"123456789",
                 "progress_percentage":"1.2%","rakan_open":True,
                 "plans":[{"code":"rakan_pembangun","amount":"20.00","label":"Rakan Pembangun"}]}
        with patch.dict("os.environ",{"CIKGULAJU_WEB_BOT_TOKEN":"123456789:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"}), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=False), \
             patch("web.web_payment_routes._source",side_effect=[catalog,(b"\\x89PNG\\r\\n\\x1a\\n"+"x".encode()*900,"image/png")]), \
             patch("web.web_payment_routes._try_audit") as audit:
            r=self.client.get("/api/web/payment/qr")
        self.assertEqual(r.status_code,200)
        audit.assert_called_once_with(CONF,712,"qr_opened")

    def test_invalid_audit_user_is_rejected(self):
        with self.assertRaises(ValueError):
            _audit_payment_event(CONF,0,"qr_opened",opener=Transport())
        with self.assertRaises(ValueError):
            _audit_payment_event(CONF,712,"approved",opener=Transport())

if __name__=="__main__":unittest.main()
