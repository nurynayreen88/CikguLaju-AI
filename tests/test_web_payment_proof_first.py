"""Web payment security and proof-first queue tests with no external charges."""
from io import BytesIO
import json
import os
from pathlib import Path
from unittest.mock import patch
import unittest

from flask import Flask
from web.web_payment_routes import (
    bp, PaymentConflict, ProfileUnavailable, _validate_receipt,
    _telegram_document, _existing, _payment_rest, validated_plans,
)

CATALOG={"mode":"manual_receipt_review","telegram_bot_id":"123456789","plans":[
    {"code":"rakan_pembangun","amount":"10.00","label":"Rakan Pembangun"},
    {"code":"langganan_30_hari","amount":"5.00","label":"Langganan 30 Hari"},
]}
CONF={"supabase_url":"https://unit.supabase.co",
      "supabase_key":"server-secret-key-for-test-only"}
RECEIPT=b"%PDF-"+b"x"*2100


class PaymentWebTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(bp)
        self.client=app.test_client()
        self.url="https://cikgulaju-web.onrender.com"
        self.user_auth=patch("web.web_payment_routes._auth",
                  return_value=(CONF,712,None))
        self.user_auth.start();self.addCleanup(self.user_auth.stop)
        bot=patch.dict(os.environ,{"CIKGULAJU_WEB_BOT_TOKEN":
            "123456789:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"})
        bot.start();self.addCleanup(bot.stop)

    def request_receipt(self,plan="rakan_pembangun",origin=None):
        return self.client.post("/api/web/payment/receipt",base_url=self.url,
               headers={"Origin":origin or self.url},
               data={"plan":plan,"receipt":(BytesIO(RECEIPT),"receipt.pdf",
                                     "application/pdf")})

    def test_qr_does_not_create_pending(self):
        with patch("web.web_payment_routes._existing",return_value=[]) as read, \
             patch("web.web_payment_routes._source",return_value=(b"\xff\xd8\xff"+b"x"*900,"image/jpeg")) as qr, \
             patch("web.web_payment_routes._payment_rest") as write:
            r=self.client.get("/api/web/payment/qr",base_url=self.url)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.mimetype,"image/jpeg")
        write.assert_not_called()
        read.assert_called_once()
        qr.assert_called_once_with("/internal/payment/v1/qr",expect="image")

    def test_existing_pending_blocks_qr_and_receipt(self):
        row={"id":91,"chat_id":"712","status":"pending","amount":"10.00"}
        with patch("web.web_payment_routes._existing",return_value=[row]), \
             patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._telegram_document") as send:
            q=self.client.get("/api/web/payment/qr",base_url=self.url)
            r=self.request_receipt()
        self.assertEqual(q.status_code,409)
        self.assertEqual(r.status_code,409)
        send.assert_not_called()

    def test_rejects_csrf_and_bad_receipts_before_calling_payment_backend(self):
        with patch("web.web_payment_routes._source") as src, \
             patch("web.web_payment_routes._telegram_document") as send:
            r=self.request_receipt(origin="https://evil.example")
            self.assertEqual(r.status_code,400)
            self.assertEqual(_validate_receipt(b"%PDF-"+b"x"*700,"application/pdf"),".pdf")
            with self.assertRaises(ValueError):
                _validate_receipt(b"not a PDF"+b"x"*900,"application/pdf")
            with self.assertRaises(ValueError):
                _validate_receipt(RECEIPT,"image/jpeg")
            self.assertEqual(self.client.post("/api/web/payment/receipt",
                base_url=self.url,headers={"Origin":self.url},
                data={"plan":"rakan_pembangun"}).status_code,400)
            send.assert_not_called()
            src.assert_not_called()

    def test_receipt_saved_only_after_bot_confirms_file(self):
        proof={"file_id":"telegram-proof-id","unique_id":"unique",
               "message_id":31,"mime":"application/pdf"}
        with patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web_v1_telegram_auth_routes._lookup",
                   return_value={"telegram_user_id":712}), \
             patch("web.web_payment_routes._telegram_document",return_value=proof) as bot, \
             patch("web.web_payment_routes._payment_rest",
                   return_value=[{"chat_id":"712","status":"pending","id":21}]) as write:
            r=self.request_receipt()
        self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(r.json["status"],"pending")
        bot.assert_called_once()
        self.assertEqual(bot.call_args.args[1],712)
        self.assertEqual(write.call_args.args[1],"POST")
        row=write.call_args.kwargs["body"]
        self.assertEqual(row["proof_telegram_file_id"],"telegram-proof-id")
        self.assertEqual(row["amount"],"10.00")
        self.assertEqual(row["notes"],"proof_received_web")
        self.assertEqual(row["chat_id"],"712")

    def test_receipt_bot_failure_never_creates_pending(self):
        with patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web_v1_telegram_auth_routes._lookup",
                   return_value={"telegram_user_id":712}), \
             patch("web.web_payment_routes._telegram_document",
                   side_effect=ProfileUnavailable("Telegram unavailable")), \
             patch("web.web_payment_routes._payment_rest") as write:
            r=self.request_receipt()
        self.assertEqual(r.status_code,503)
        write.assert_not_called()

    def test_cannot_choose_another_user_or_fake_price(self):
        with patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web_v1_telegram_auth_routes._lookup",
                   return_value={"telegram_user_id":712}), \
             patch("web.web_payment_routes._telegram_document") as send:
            self.assertEqual(self.request_receipt(plan="hacked").status_code,400)
            send.assert_not_called()
        with self.assertRaises(ProfileUnavailable):
            validated_plans({"mode":"manual_receipt_review","telegram_bot_id":"000000000","plans":[
                {"code":"rakan_pembangun","amount":"1.00"},
                {"code":"langganan_30_hari","amount":"5.00"}]})

    def test_different_bot_token_rejected_before_payment(self):
        with patch.dict(os.environ,{"CIKGULAJU_WEB_BOT_TOKEN":
                "999999999:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"}):
            with self.assertRaises(ProfileUnavailable):
                validated_plans(CATALOG)

    def test_unauthenticated_and_wrong_account_cannot_pay(self):
        with patch("web.web_payment_routes._auth",
                   return_value=(None,None,({"error":"no login"},401))):
            self.assertEqual(self.client.get("/api/web/payment/catalog").status_code,401)
            self.assertEqual(self.client.get("/api/web/payment/qr").status_code,401)
            self.assertEqual(self.request_receipt().status_code,401)

    def test_interface_keeps_refresh_and_payment_as_separate_view(self):
        root=Path(__file__).resolve().parents[1]
        html=(root/"web_v1_static_preview/index.html").read_text("utf8")
        js=(root/"web_v1_static_preview/web-payment.js").read_text("utf8")
        self.assertIn("🔄 Refresh Profil &amp; Jadual",html)
        self.assertNotIn("Segar Semula",html)
        self.assertIn('id="view-payment"',html)
        self.assertIn('data-web-view="payment"',html)
        self.assertIn('id="payment-submit"',html)
        self.assertIn('id="payment-refresh"',html)
        self.assertIn("/api/web/payment/receipt",js)
        self.assertNotIn("status=\"approved\"",js)


if __name__=="__main__":
    unittest.main()
