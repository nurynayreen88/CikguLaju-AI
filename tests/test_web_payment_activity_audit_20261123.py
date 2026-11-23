"""Payment activity is linked to authenticated account and does not block payment."""
import unittest
from unittest.mock import patch
from flask import Flask
from web.web_payment_routes import bp, _audit_payment

CONF={"supabase_url":"https://unit.supabase.co","supabase_key":"test-service-key"}

class ActivityTests(unittest.TestCase):
    def test_payment_catalog_audits_authenticated_id(self):
        app=Flask(__name__);app.register_blueprint(bp)
        catalog={"mode":"manual_receipt_review","telegram_bot_id":"123456789",
            "progress_percentage":"0.0%","rakan_open":True,
            "plans":[{"code":"rakan_pembangun","amount":"20.00"}]}
        with patch("web.web_payment_routes._auth",return_value=(CONF,712,None)), \
             patch("web.web_payment_routes._source",return_value=catalog), \
             patch("web.web_payment_routes.validated_plans",
                   return_value={"rakan_pembangun":{"code":"rakan_pembangun","amount":"20.00"}}), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=False), \
             patch("web.web_payment_routes._audit_payment") as audit:
            response=app.test_client().get("/api/web/payment/catalog")
        self.assertEqual(response.status_code,200)
        audit.assert_called_once_with(CONF,712,"payment_opened")

    def test_audit_failure_never_blocks_checkout(self):
        with patch("web.web_payment_routes.build_opener",side_effect=OSError("offline")):
            self.assertIsNone(_audit_payment(CONF,712,"payment_opened"))

    def test_invalid_identity_or_event_not_written(self):
        with patch("web.web_payment_routes.build_opener") as opener:
            _audit_payment(CONF,0,"payment_opened")
            _audit_payment(CONF,712,"untrusted_event")
        opener.assert_not_called()

if __name__=="__main__":
    unittest.main()
