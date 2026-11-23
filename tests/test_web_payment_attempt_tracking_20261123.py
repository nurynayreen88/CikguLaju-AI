"""Authenticated payment audit events: no user-supplied IDs, fail-open logging."""
import unittest
from unittest.mock import patch
from flask import Flask
from web.web_payment_routes import bp, _track_payment_event

CONF={"supabase_url":"https://example.supabase.co","supabase_key":"server-secret-key"}
CATALOG={"mode":"manual_receipt_review","telegram_bot_id":"123456789",
"progress_percentage":"1.2%","rakan_open":True,
"plans":[{"code":"rakan_pembangun","amount":"20.00"}]}

class PaymentAuditTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(bp)
        self.client=app.test_client()

    def test_page_opened_is_attributed_to_authenticated_account(self):
        with patch("web.web_payment_routes._auth",return_value=(CONF,712,None)), \
             patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=False), \
             patch("web.web_payment_routes._track_payment_event") as audit:
            response=self.client.get("/api/web/payment/catalog?telegram_user_id=999")
        self.assertEqual(response.status_code,200)
        audit.assert_called_once_with(CONF,712,"payment_page_opened")

    def test_receipt_failed_is_attributed_even_on_validation_error(self):
        with patch("web.web_payment_routes._auth",return_value=(CONF,712,None)), \
             patch("web.web_payment_routes._track_payment_event") as audit:
            response=self.client.post("/api/web/payment/receipt",
                base_url="https://cikgulaju-web.onrender.com",
                headers={"Origin":"https://evil.invalid"})
        self.assertEqual(response.status_code,400)
        self.assertEqual(audit.call_args_list[0].args,(CONF,712,"receipt_started"))
        self.assertEqual(audit.call_args_list[1].args,(CONF,712,"receipt_failed"))
        self.assertEqual(audit.call_args_list[1].kwargs,{"error_code":"validation_failed"})

    def test_audit_failure_never_blocks_payment(self):
        with patch("web.web_payment_routes._auth",return_value=(CONF,712,None)), \
             patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=False), \
             patch("web.web_payment_routes._track_payment_event",side_effect=lambda *a,**k:None):
            response=self.client.get("/api/web/payment/catalog")
        self.assertEqual(response.status_code,200)

    def test_rejects_invalid_audit_identity(self):
        with patch("web.web_payment_routes.build_opener") as transport:
            _track_payment_event(CONF,0,"qr_opened")
            _track_payment_event(CONF,712,"unknown_event")
        transport.assert_not_called()

if __name__=="__main__":
    unittest.main()
