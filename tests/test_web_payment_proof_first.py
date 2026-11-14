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
    _telegram_document, _existing, _payment_rest, validated_plans, validated_rakan_status,
)

CATALOG={"mode":"manual_receipt_review","telegram_bot_id":"123456789",
    "progress_percentage":"1.2%","rakan_open":True,"plans":[
    {"code":"rakan_pembangun","amount":"20.00","label":"Rakan Pembangun"},
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

    def test_admin_payment_queue_is_private_and_does_not_expose_file_id(self):
        route = "/api/web/admin/payments"
        row = {"id": 31, "chat_id": "201", "amount": "20.00", "status": "pending",
               "proof_telegram_file_id": "private-reference",
               "proof_received_at": "2026-11-14T01:00:00+00:00"}
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "901"}), \
             patch("web.web_payment_routes._admin_payment_rows", return_value=[row]) as source, \
             patch("web.web_payment_routes._payer_names", return_value={"201": "Cikgu Ujian"}):
            self.assertEqual(self.client.get(route).status_code, 403)
            source.assert_not_called()
            with patch("web.web_payment_routes._auth", return_value=(CONF, 901, None)):
                self.assertEqual(self.client.get(route + "?status=bad").status_code, 400)
                response = self.client.get(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["items"][0]["name"], "Cikgu Ujian")
        self.assertTrue(response.json["items"][0]["can_review"])
        self.assertNotIn("private-reference", response.get_data(as_text=True))
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_admin_receipt_and_review_bind_authorized_admin_and_version(self):
        route = "/api/web/admin/payments/31"
        stamp = "2026-11-14T01:00:00+00:00"
        body = {"payer": "201", "receipt_at": stamp, "decision": "approved"}
        row = {"proof_telegram_file_id": "private-reference", "proof_received_at": stamp}
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "901"}), \
             patch("web.web_payment_routes._auth", return_value=(CONF, 901, None)), \
             patch("web.web_payment_routes._admin_payment_rows", return_value=[row]), \
             patch("web.web_payment_routes._telegram_receipt_bytes",
                   return_value=(RECEIPT, "application/pdf", ".pdf")), \
             patch("web.web_payment_routes._review_rakan",
                   return_value={"status": "approved"}) as review:
            receipt = self.client.get(route + "/receipt")
            self.assertEqual(receipt.data, RECEIPT)
            self.assertIn("sandbox", receipt.headers["Content-Security-Policy"])
            self.assertEqual(self.client.post(route + "/review", json=body).status_code, 403)
            review.assert_not_called()
            response = self.client.post(route + "/review", base_url=self.url,
                                        json=body, headers={"Origin": self.url})
            review.assert_called_once_with(CONF, 31, 201, 901, stamp, "approved")
            self.assertEqual(response.json, {"status": "approved"})
            review.return_value = {"error": "reviewed"}
            response = self.client.post(route + "/review", base_url=self.url,
                                        json=body, headers={"Origin": self.url})
            self.assertEqual(response.status_code, 409)

    def test_qr_does_not_create_pending(self):
        def source(path,**kwargs):
            return CATALOG if path.endswith("/catalog") else (b"\xff\xd8\xff"+b"x"*900,"image/jpeg")
        with patch("web.web_payment_routes._existing",return_value=[]) as read, \
             patch("web.web_payment_routes._source",side_effect=source) as qr, \
             patch("web.web_payment_routes._is_member",return_value=False), \
             patch("web.web_payment_routes._payment_rest") as write:
            r=self.client.get("/api/web/payment/qr",base_url=self.url)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.mimetype,"image/jpeg")
        write.assert_not_called()
        read.assert_called_once()
        self.assertEqual(qr.call_count,2)
        qr.assert_any_call("/internal/payment/v1/catalog")
        qr.assert_any_call("/internal/payment/v1/qr",expect="image")

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
                   return_value=[{"chat_id":"712","status":"pending","id":21}]) as write, \
             patch("web.web_payment_routes._notify_telegram_admin_review",
                   return_value=True) as notice:
            r=self.request_receipt()
        notice.assert_called_once_with(712,21)
        self.assertEqual(r.json["admin_notification"],"sent")
        self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(r.json["status"],"pending")
        bot.assert_called_once()
        self.assertEqual(bot.call_args.args[1],712)
        self.assertEqual(write.call_args.args[1],"POST")
        row=write.call_args.kwargs["body"]
        self.assertEqual(row["proof_telegram_file_id"],"telegram-proof-id")
        self.assertEqual(row["amount"],"20.00")
        self.assertEqual(row["notes"],"proof_received_web")
        self.assertEqual(row["chat_id"],"712")

    def test_pending_is_not_lost_if_telegram_admin_notice_fails(self):
        # A successfully saved payment must NEVER return 503 and induce a
        # second payment just because the admin notification transport fails.
        proof={"file_id":"telegram-proof-id","unique_id":"u",
               "message_id":31,"mime":"application/pdf"}
        with patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web_v1_telegram_auth_routes._lookup",
                   return_value={"telegram_user_id":712}), \
             patch("web.web_payment_routes._telegram_document",return_value=proof), \
             patch("web.web_payment_routes._payment_rest",
                   return_value=[{"chat_id":"712","status":"pending","id":21}]) as store, \
             patch("web.web_payment_routes._notify_telegram_admin_review",
                   side_effect=ProfileUnavailable("Telegram unreachable")) as notice:
            r=self.request_receipt()
        self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(r.json["admin_notification"],"unconfirmed")
        self.assertIn("Jangan bayar",r.json["message"])
        self.assertEqual(r.json["id"],21)
        store.assert_called_once()
        notice.assert_called_once_with(712,21)

    def test_telegram_admin_private_notice_uses_fixed_verified_payment_id(self):
        from web.web_payment_routes import _notify_telegram_admin_review
        from unittest.mock import Mock
        class Reply:
            status=200
            headers={"Content-Type":"application/json; charset=utf-8"}
            def __enter__(self):return self
            def __exit__(self,*args):return None
            def read(self,n):return json.dumps({
                "notified":True,"request_id":47,"review":"admin_only"
            }).encode()
        class Transport:
            def __init__(self):self.req=None
            def open(self,req,timeout):self.req=req;return Reply()
        transport=Transport()
        with patch.dict(os.environ,{
            "CIKGULAJU_AUTHORITATIVE_API_URL":"https://cikgulaju-ai.onrender.com",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*48,
        }):
            self.assertTrue(_notify_telegram_admin_review(712,47,opener=transport))
        body=json.loads(transport.req.data)
        self.assertEqual(body,{"request_id":47,"telegram_user_id":712})
        self.assertEqual(transport.req.get_method(),"POST")
        self.assertTrue(transport.req.full_url.endswith(
            "/internal/payment/v1/admin-review-notify"))
        self.assertEqual(transport.req.get_header("Authorization"),"Bearer "+"x"*48)
        self.assertNotIn("approve",str(body))
        self.assertNotIn("file_id",str(body))
        with self.assertRaises(ProfileUnavailable):
            _notify_telegram_admin_review(True,47,opener=transport)

    def test_no_notification_for_qr_or_invalid_proof(self):
        def source(path, **kwargs):
            return CATALOG if path.endswith("/catalog") else (
                b"\\xff\\xd8\\xff" + b"x"*900, "image/jpeg")
        with patch("web.web_payment_routes._notify_telegram_admin_review") as notice, \
             patch("web.web_payment_routes._source",side_effect=source), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=False):
            r=self.client.get("/api/web/payment/qr",base_url=self.url)
            self.assertEqual(r.status_code,200)
            self.assertEqual(self.request_receipt(plan="wrong-plan").status_code,400)
        notice.assert_not_called()

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

    def test_catalog_shows_verified_percentage_and_only_rakan(self):
        with patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=False):
            r=self.client.get("/api/web/payment/catalog",base_url=self.url)
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(r.json["progress_percentage"],"1.2%")
        self.assertEqual(r.json["plans"][0]["amount"],"20.00")
        self.assertEqual([x["code"] for x in r.json["plans"]],["rakan_pembangun"])
        self.assertTrue(r.json["rakan_open"])
        self.assertNotIn("500",str(r.json))
        self.assertNotIn("langganan_30_hari",str(r.json))

    def test_legacy_rm5_submission_rejected_without_sending_resit(self):
        with patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._telegram_document") as upload:
            r=self.request_receipt(plan="langganan_30_hari")
        self.assertEqual(r.status_code,400)
        upload.assert_not_called()

    def test_full_rakan_quota_blocks_qr_receipt_and_displays_progress(self):
        full=dict(CATALOG,progress_percentage="100.0%",rakan_open=False)
        with patch("web.web_payment_routes._source",return_value=full), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=False), \
             patch("web.web_payment_routes._telegram_document") as send:
            cat=self.client.get("/api/web/payment/catalog",base_url=self.url)
            q=self.client.get("/api/web/payment/qr",base_url=self.url)
            r=self.request_receipt()
        self.assertEqual(cat.status_code,200)
        self.assertEqual(cat.json["progress_percentage"],"100.0%")
        self.assertFalse(cat.json["rakan_open"])
        self.assertEqual(q.status_code,409)
        self.assertEqual(r.status_code,409)
        send.assert_not_called()

    def test_already_member_cannot_pay_twice(self):
        with patch("web.web_payment_routes._source",return_value=CATALOG), \
             patch("web.web_payment_routes._existing",return_value=[]), \
             patch("web.web_payment_routes._is_member",return_value=True), \
             patch("web.web_payment_routes._telegram_document") as send:
            cat=self.client.get("/api/web/payment/catalog",base_url=self.url)
            qr=self.client.get("/api/web/payment/qr",base_url=self.url)
            submit=self.request_receipt()
        self.assertTrue(cat.json["already_member"])
        self.assertFalse(cat.json["qr_available"])
        self.assertEqual(qr.status_code,409)
        self.assertEqual(submit.status_code,409)
        send.assert_not_called()

    def test_progress_invalid_fails_closed(self):
        self.assertEqual(validated_rakan_status(CATALOG),("1.2%",True))
        for data in [
            dict(CATALOG,progress_percentage="500%"),
            dict(CATALOG,progress_percentage="1.23%"),
            dict(CATALOG,progress_percentage="unknown"),
            dict(CATALOG,progress_percentage="100.0%",rakan_open=True),
            dict(CATALOG,rakan_open="true"),
        ]:
            with self.subTest(data=data),self.assertRaises(ProfileUnavailable):
                validated_rakan_status(data)

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
        self.assertIn('id="payment-direct-link"',html)
        self.assertIn('id="payment-tng-link"',html)
        self.assertIn('href="https://payment.tngdigital.com.my/sc/bDLocm2K1n"',html)
        self.assertIn('rel="noopener noreferrer external"',html)
        self.assertIn('id="payment-direct-link" class="payment-direct-link" hidden',html)
        self.assertIn('id="rakan-progress-percent"',html)
        self.assertIn('role="progressbar"',html)
        self.assertIn('type="hidden" value="rakan_pembangun"',html)
        self.assertNotIn('Langganan 30 Hari',html)
        self.assertNotIn('Memuatkan pakej',html)
        self.assertIn('setVerifiedProgress(data)',js)
        self.assertIn('payDirectLink.hidden=!canPay;',js)
        self.assertIn('payDirectLink.hidden=true;',js)
        self.assertRegex(html, r'/assets/web-payment\.js\?v=[a-z0-9-]+')
        self.assertIn("hantar resit",html.lower())


if __name__=="__main__":
    unittest.main()
