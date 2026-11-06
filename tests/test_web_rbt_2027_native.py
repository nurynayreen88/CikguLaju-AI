"""RBT Web end-to-end route security, license and trial debit tests.

All private Telegram calls and Supabase RPCs mocked; NO live identities,
credits, payment record, database or production service is accessed.
"""
import io
import unittest
from unittest.mock import patch
from flask import Flask, jsonify

from web.unified_rph_web import create_blueprint
from web.native_telegram_rph_client import NativeRPHUnavailable


def rbt_query():
    return {"year":"5","subject":"RBT","unit":"u01","lesson":"001",
            "teacher_class":"5 Ikhlas","teacher_date":"2027-01-04",
            "teacher_start":"08:00","teacher_end":"09:00","teacher_students":"24"}


def valid_pdf():
    return io.BytesIO(b"%PDF-1.7\n"+b"Draft native PDF "*110)


class NativeRBTWebRoutes(unittest.TestCase):
    def setUp(self):
        app=Flask("rbt-web-route-qa")
        app.register_blueprint(create_blueprint())
        self.client=app.test_client()

    def test_paid_native_rbt_download_and_existing_source(self):
        account={"telegram_user_id":123,"authenticated":True}
        with patch("web.unified_rph_web._account",return_value=(account,None)), \
             patch("web.unified_rph_web._has_paid_access",return_value=True), \
             patch("web.native_telegram_rbt_2027_client.rbt_available",return_value=True) as available, \
             patch("web.native_telegram_rbt_2027_client.request_rbt_rph",return_value=valid_pdf()) as native:
            r=self.client.get("/api/web/rph/pdf",query_string=rbt_query())
        self.assertEqual(r.status_code,200,r.data[:200])
        self.assertEqual(r.headers["X-RPH-Generator"],"telegram-native")
        self.assertEqual(r.headers["X-RPH-Access-Mode"],"paid")
        self.assertTrue(r.data.startswith(b"%PDF-"))
        selected=native.call_args.args[0]
        self.assertEqual(selected["source"],"telegram-native-rbt-2027")
        self.assertEqual(selected["teacher"]["class"],"5 Ikhlas")
        self.assertEqual(selected["teacher"]["time"],"08:00-09:00")
        self.assertEqual(selected["teacher"]["date"],"2027-01-04")
        available.assert_called_once_with(5,"u01","001")

    def test_trial_native_render_failure_does_not_charge(self):
        account={"telegram_user_id":123,"authenticated":True,"free_remaining":1}
        with patch("web.unified_rph_web._account",return_value=(account,None)), \
             patch("web.unified_rph_web._has_paid_access",return_value=False), \
             patch("web.native_telegram_rbt_2027_client.rbt_available",return_value=True), \
             patch("web.native_telegram_rbt_2027_client.request_rbt_rph",
                   side_effect=NativeRPHUnavailable("source off")), \
             patch("web.rph_delivery_quota.authorize_rendered_document") as debit:
            r=self.client.get("/api/web/rph/pdf",query_string=rbt_query())
        self.assertEqual(r.status_code,503)
        self.assertEqual(r.get_json()["code"],"TELEGRAM_RPH_GENERATOR_UNAVAILABLE")
        debit.assert_not_called()

    def test_trial_success_debits_only_after_document(self):
        account={"telegram_user_id":123,"authenticated":True,"free_remaining":1}
        with patch("web.unified_rph_web._account",return_value=(account,None)), \
             patch("web.unified_rph_web._has_paid_access",return_value=False), \
             patch("web.native_telegram_rbt_2027_client.rbt_available",return_value=True), \
             patch("web.native_telegram_rbt_2027_client.request_rbt_rph",return_value=valid_pdf()), \
             patch("web_v1_telegram_auth_routes._config",
                   return_value={"account_backend":"supabase",
                                 "supabase_url":"https://fake.invalid",
                                 "supabase_key":"never-sent-test-key"}), \
             patch("web.rph_delivery_quota.authorize_rendered_document",
                   return_value={"allowed":True,"remaining":0}) as debit:
            r=self.client.get("/api/web/rph/pdf",query_string=rbt_query())
        self.assertEqual(r.status_code,200,r.data[:200])
        self.assertEqual(r.headers["X-RPH-Trial-Remaining"],"0")
        self.assertEqual(debit.call_count,1)
        self.assertIn(b"%PDF-",debit.call_args.args[2])

    def test_zero_credit_blocks_before_telegram_render(self):
        account={"telegram_user_id":123,"authenticated":True,"free_remaining":0}
        with patch("web.unified_rph_web._account",return_value=(account,None)), \
             patch("web.unified_rph_web._has_paid_access",return_value=False), \
             patch("web.native_telegram_rbt_2027_client.rbt_available") as check:
            r=self.client.get("/api/web/rph/pdf",query_string=rbt_query())
        self.assertEqual(r.status_code,403)
        self.assertEqual(r.get_json()["code"],"FREE_TRIAL_EXHAUSTED")
        check.assert_not_called()

    def test_invalid_selection_never_falls_back(self):
        account={"telegram_user_id":123,"authenticated":True}
        with patch("web.unified_rph_web._account",return_value=(account,None)), \
             patch("web.unified_rph_web._has_paid_access",return_value=True), \
             patch("web.native_telegram_rbt_2027_client.rbt_available",
                   side_effect=ValueError("RBT Unit mismatch")):
            r=self.client.get("/api/web/rph/pdf",query_string={**rbt_query(),"unit":"u99"})
        self.assertEqual(r.status_code,503)
        self.assertEqual(r.get_json()["code"],"TELEGRAM_RBT_SOURCE_UNAVAILABLE")

    def test_no_guest_rbt_download(self):
        with patch("web.unified_rph_web._account",
                   return_value=(None,(jsonify({"error":"login required"}),401))):
            with self.client.application.app_context():
                r=self.client.get("/api/web/rph/pdf",query_string=rbt_query())
        self.assertEqual(r.status_code,401)


if __name__=="__main__":
    unittest.main()
