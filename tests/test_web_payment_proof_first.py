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

    def test_admin_payment_inbox_displays_email_not_synthetic_account_id(self):
        uid = "8000000000000000000"
        row = {"id": 8, "chat_id": uid, "amount": "20.00", "status": "pending",
               "proof_telegram_file_id": "private-proof",
               "proof_received_at": "2026-11-22T15:45:06.89408+00:00"}
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "901"}), \
             patch("web.web_payment_routes._admin_payment_rows", return_value=[row]), \
             patch("web.admin_usage_web._fetch",
                   return_value=[{"telegram_user_id": uid, "first_name": None,
                                  "last_name": None, "username": None}]), \
             patch("web.web_payment_routes._email_payer_names",
                   return_value={uid: "teacher@example.com"}) as email_source:
            unauthenticated = self.client.get("/api/web/admin/payments")
            self.assertEqual(unauthenticated.status_code, 403)
            email_source.assert_not_called()
            with patch("web.web_payment_routes._auth",
                       return_value=(CONF, 901, None)):
                response = self.client.get("/api/web/admin/payments")
        self.assertEqual(response.status_code, 200, response.json)
        item = response.json["items"][0]
        self.assertEqual(item["name"], "teacher@example.com")
        self.assertEqual(item["user_id"], uid)  # hidden immutable DB key
        self.assertEqual(item["id"], "8")
        self.assertNotIn("private-proof", response.get_data(as_text=True))
        email_source.assert_called_once()

    def test_server_only_email_lookup_maps_to_matching_auth_id(self):
        from web.web_payment_routes import _email_payer_names
        uid = "8000000000000000000"
        auth_id = "12345678-1234-4234-9234-123456789012"

        class Reply:
            status = 200
            def __init__(self, payload): self.payload = payload
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self, length): return json.dumps(self.payload).encode()

        class Transport:
            def __init__(self): self.requests = []
            def open(self, req, timeout):
                self.requests.append(req)
                if "/rest/v1/web_email_identities?" in req.full_url:
                    return Reply([{"telegram_user_id": uid, "auth_user_id": auth_id}])
                if req.full_url.endswith("/auth/v1/admin/users/" + auth_id):
                    return Reply({"id": auth_id, "email": "teacher@example.com"})
                raise AssertionError("Unexpected auth endpoint")

        transport = Transport()
        with patch("web.admin_usage_web._api_config",
                   return_value=("https://unit.supabase.co",
                                 {"apikey": "server-secret-test-only"})):
            names = _email_payer_names(CONF, [uid], opener=transport)
        self.assertEqual(names, {uid: "teacher@example.com"})
        self.assertEqual(len(transport.requests), 2)
        for req in transport.requests:
            self.assertEqual(req.get_header("Apikey"), "server-secret-test-only")
            self.assertNotIn("teacher@example.com", req.full_url)
        self.assertEqual(_email_payer_names(CONF, [], opener=transport), {})

    def test_email_display_unavailable_does_not_block_payment_review(self):
        from web.web_payment_routes import _payer_names
        uid = "8000000000000000000"
        with patch("web.admin_usage_web._fetch", return_value=[
             {"telegram_user_id": uid, "first_name": None, "last_name": None,
              "username": None}]), \
             patch("web.web_payment_routes._email_payer_names",
                   side_effect=ProfileUnavailable("Auth unavailable")):
            names = _payer_names(CONF, [{"chat_id": uid}])
        self.assertEqual(names[uid], "Akaun e-mel")

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

    def test_email_only_19_digit_admin_approval_and_rejection_are_valid(self):
        """Synthetic Web account IDs must reach the owner-checking DB RPC."""
        uid = 8000000000000000000
        stamp = "2026-11-22T15:45:06.89408+00:00"
        route = "/api/web/admin/payments/8/review"
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "901"}), \
             patch("web.web_payment_routes._auth", return_value=(CONF, 901, None)), \
             patch("web.web_payment_routes._review_rakan") as review:
            for decision in ("approved", "rejected"):
                review.return_value = {"status": decision}
                response = self.client.post(
                    route, base_url=self.url, headers={"Origin": self.url},
                    json={"payer": str(uid), "receipt_at": stamp, "decision": decision},
                )
                self.assertEqual(response.status_code, 200, response.json)
                self.assertEqual(response.json["status"], decision)
                review.assert_called_with(CONF, 8, uid, 901, stamp, decision)

    def test_admin_review_rejects_out_of_range_and_untrusted_payer_values(self):
        stamp = "2026-11-22T15:45:06.89408+00:00"
        route = "/api/web/admin/payments/8/review"
        invalid = [
            str(2**63), str(2**63 + 1), "9999999999999999999",
            "08000000000000000000", "0", "-1", "nan", "7.5", 8000000000000000000,
        ]
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "901"}), \
             patch("web.web_payment_routes._auth", return_value=(CONF, 901, None)), \
             patch("web.web_payment_routes._review_rakan") as review:
            for payer in invalid:
                with self.subTest(payer=payer):
                    response = self.client.post(
                        route, base_url=self.url, headers={"Origin": self.url},
                        json={"payer": payer, "receipt_at": stamp, "decision": "approved"},
                    )
                    self.assertEqual(response.status_code, 400, response.json)
            review.assert_not_called()

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

    def test_receipt_is_private_before_pending_and_optional_admin_notice(self):
        import hashlib
        with patch("web.web_payment_routes._existing", return_value=[]), \
             patch("web.web_payment_routes._is_member", return_value=False), \
             patch("web.web_payment_routes._private_receipt_storage",
                   return_value=True) as storage, \
             patch("web.web_payment_routes._payment_rest",
                   side_effect=lambda conf, method, **kw:
                   [{**kw["body"], "id": 21}]) as write, \
             patch("web.web_payment_routes._optional_web_receipt_notice",
                   return_value=True) as notice, \
             patch("web.web_payment_routes._audit_payment"):
            response = self.request_receipt()
        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json["status"], "pending")
        self.assertEqual(response.json["source"], "web")
        self.assertEqual(response.json["admin_notification"], "sent")
        body = write.call_args.kwargs["body"]
        self.assertEqual(body["notes"], "proof_received_web_private")
        self.assertEqual(body["chat_id"], "712")
        self.assertEqual(body["proof_web_sha256"], hashlib.sha256(RECEIPT).hexdigest())
        self.assertRegex(body["proof_web_path"],
                         r"^receipts/712/[0-9a-f]{32}\.pdf$")
        self.assertNotIn("proof_telegram_file_id", body)
        storage.assert_called_once_with(CONF, "POST", body["proof_web_path"],
                                        data=RECEIPT, mime="application/pdf")
        notice.assert_called_once_with(712, 21)

    def test_pending_is_not_lost_when_optional_telegram_notice_fails(self):
        # Web receipt is the durable primary channel; a Telegram outage cannot
        # ask the customer to pay again or undo the recorded Pending row.
        with patch("web.web_payment_routes._existing", return_value=[]), \
             patch("web.web_payment_routes._is_member", return_value=False), \
             patch("web.web_payment_routes._private_receipt_storage",
                   return_value=True), \
             patch("web.web_payment_routes._payment_rest",
                   side_effect=lambda conf, method, **kw:
                   [{**kw["body"], "id": 21}]) as store, \
             patch("web.web_payment_routes._optional_web_receipt_notice",
                   return_value=False) as notice, \
             patch("web.web_payment_routes._audit_payment"):
            response = self.request_receipt()
        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json["admin_notification"], "web_only")
        self.assertEqual(response.json["id"], 21)
        self.assertIn("Jangan bayar", response.json["message"])
        store.assert_called_once()
        notice.assert_called_once_with(712, 21)

    def test_legacy_telegram_receipts_use_confirmed_admin_first(self):
        from web.web_payment_routes import _receipt_destinations
        uid = 8000000000000000003

        class Reply:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self, n):
                return json.dumps({"ok": True, "result": {
                    "chat": {"id": 901}, "message_id": 44,
                    "document": {"file_id": "saved-proof",
                                 "file_unique_id": "unique",
                                 "mime_type": "application/pdf"}}}).encode()

        class Transport:
            def __init__(self): self.req = None; self.timeout = None
            def open(self, req, timeout):
                self.req, self.timeout = req, timeout
                return Reply()

        transport = Transport()
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "901"}):
            self.assertEqual(_receipt_destinations(uid), [901])
            self.assertEqual(_receipt_destinations(712), [901, 712])
            proof = _telegram_document(CONF, uid, RECEIPT, ".pdf",
                                       opener=transport)
        self.assertEqual(proof["file_id"], "saved-proof")
        self.assertEqual(proof["admin_chat_id"], 901)
        self.assertEqual(proof["message_id"], 44)
        self.assertIn(b'name="chat_id"\r\n\r\n901\r\n', transport.req.data)
        self.assertNotIn(str(uid).encode() + b"\r\n", transport.req.data)
        self.assertEqual(transport.timeout, 12)
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": ""}):
            with self.assertRaises(ProfileUnavailable):
                _receipt_destinations(uid)

    def test_legacy_telegram_customer_receipt_uses_admin_first(self):
        class Reply:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self, n):
                return json.dumps({"ok": True, "result": {
                    "chat": {"id": 901}, "message_id": 55,
                    "document": {"file_id": "telegram-proof"}}}).encode()

        class Transport:
            def __init__(self): self.req = None
            def open(self, req, timeout): self.req = req; return Reply()

        transport = Transport()
        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "901"}):
            proof = _telegram_document(CONF, 712, RECEIPT, ".pdf",
                                       opener=transport)
        self.assertEqual(proof["admin_chat_id"], 901)
        self.assertIn(b'name="chat_id"\r\n\r\n901\r\n', transport.req.data)

    def test_email_only_full_submit_creates_web_pending_and_notifies_admin(self):
        uid = 8000000000000000003
        with patch("web.web_payment_routes._auth",
                   return_value=(CONF, uid, None)), \
             patch("web.web_payment_routes._existing", return_value=[]), \
             patch("web.web_payment_routes._is_member", return_value=False), \
             patch("web.web_payment_routes._private_receipt_storage",
                   return_value=True) as upload, \
             patch("web.web_payment_routes._payment_rest",
                   side_effect=lambda conf, method, **kw:
                   [{**kw["body"], "id": 91}]) as store, \
             patch("web.web_payment_routes._optional_web_receipt_notice",
                   return_value=True) as notice, \
             patch("web.web_payment_routes._audit_payment"):
            response = self.request_receipt()
        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json["id"], 91)
        self.assertEqual(response.json["admin_notification"], "sent")
        body = store.call_args.kwargs["body"]
        self.assertEqual(body["chat_id"], str(uid))
        self.assertEqual(body["notes"], "proof_received_web_private")
        self.assertNotIn("proof_telegram_file_id", body)
        upload.assert_called_once_with(CONF, "POST", body["proof_web_path"],
                                       data=RECEIPT, mime="application/pdf")
        notice.assert_called_once_with(uid, 91)

    def test_email_only_optional_notice_failure_keeps_web_pending(self):
        uid = 8000000000000000003
        with patch("web.web_payment_routes._auth",
                   return_value=(CONF, uid, None)), \
             patch("web.web_payment_routes._existing", return_value=[]), \
             patch("web.web_payment_routes._is_member", return_value=False), \
             patch("web.web_payment_routes._private_receipt_storage",
                   return_value=True), \
             patch("web.web_payment_routes._payment_rest",
                   side_effect=lambda conf, method, **kw:
                   [{**kw["body"], "id": 92}]) as store, \
             patch("web.web_payment_routes._optional_web_receipt_notice",
                   return_value=False), \
             patch("web.web_payment_routes._audit_payment"):
            response = self.request_receipt()
        self.assertEqual(response.status_code, 201, response.json)
        self.assertEqual(response.json["status"], "pending")
        self.assertEqual(response.json["admin_notification"], "web_only")
        self.assertIn("Jangan bayar", response.json["message"])
        store.assert_called_once()

    def test_email_only_admin_followup_is_bound_to_original_receipt(self):
        from web.web_payment_routes import _notify_email_admin_review
        uid=8000000000000000003
        proof={"admin_chat_id":901,"message_id":44}

        class Reply:
            status=200
            def __enter__(self): return self
            def __exit__(self,*args): return None
            def read(self,n):
                return json.dumps({"ok":True,"result":{
                    "chat":{"id":901},"message_id":45}}).encode()

        class Transport:
            def __init__(self): self.req=None
            def open(self,req,timeout): self.req=req;return Reply()

        transport=Transport()
        with patch.dict(os.environ,{"CIKGULAJU_WEB_ADMIN_IDS":"901"}):
            self.assertTrue(_notify_email_admin_review(uid,91,proof,opener=transport))
            payload=json.loads(transport.req.data)
            self.assertEqual(payload["chat_id"],"901")
            self.assertEqual(payload["reply_to_message_id"],44)
            self.assertIn("Pending #91",payload["text"])
            self.assertIn(str(uid),payload["text"])
            self.assertNotIn("approved",payload["text"])
            with self.assertRaises(ProfileUnavailable):
                _notify_email_admin_review(uid,91,{"admin_chat_id":902,"message_id":44},
                                           opener=transport)


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

    def test_full_rakan_quota_blocks_new_qr_but_accepts_old_payment_proof(self):
        # Closing new enrolment may not discard a customer receipt for a
        # transaction already made. Only the admin can approve an entitlement.
        full = dict(CATALOG, progress_percentage="100.0%", rakan_open=False)
        with patch("web.web_payment_routes._source", return_value=full), \
             patch("web.web_payment_routes._existing", return_value=[]), \
             patch("web.web_payment_routes._is_member", return_value=False), \
             patch("web.web_payment_routes._private_receipt_storage",
                   return_value=True), \
             patch("web.web_payment_routes._payment_rest",
                   side_effect=lambda conf, method, **kw:
                   [{**kw["body"], "id": 93}]) as store, \
             patch("web.web_payment_routes._optional_web_receipt_notice",
                   return_value=False), \
             patch("web.web_payment_routes._audit_payment"):
            cat = self.client.get("/api/web/payment/catalog", base_url=self.url)
            qr = self.client.get("/api/web/payment/qr", base_url=self.url)
            receipt = self.request_receipt()
        self.assertEqual(cat.status_code, 200, cat.json)
        self.assertEqual(cat.json["progress_percentage"], "100.0%")
        self.assertFalse(cat.json["rakan_open"])
        self.assertEqual(qr.status_code, 409)
        self.assertEqual(receipt.status_code, 201, receipt.json)
        self.assertEqual(receipt.json["status"], "pending")
        store.assert_called_once()

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
