"""Offline admin Web proof notification tests: no real bot/DB/API writes."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from web.telegram_web_receipt_admin_notification import (
    REVIEW_PATH, _keyboard, _valid_pending_row, create_web_receipt_admin_notification,
)

ADMIN = "987654321"
SECRET = "secure-test-token-" + "x"*40
ROW = {
    "id": 41, "chat_id": "7001234", "amount": "10.00",
    "status": "pending", "notes": "proof_received_web",
    "proof_telegram_file_id": "file_id-from-the-same-bot",
    "proof_telegram_message_id": 567,
    "proof_received_at": "2026-11-06T00:07:01+00:00",
}


class Response:
    def __init__(self, status=200, data=None):
        self.status_code = status
        self.ok = status == 200
        self.data = data or {"ok": True, "result": {"message_id": 123}}
    def json(self):
        return self.data


class WebReceiptNoticeTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(ROW)
        self.copied = []
        self.sent = []
        self.lookup = []
        self.runtime = SimpleNamespace(
            ADMIN_CHAT_ID=ADMIN,
            CIKGULAJU_PROOF_FIRST_PAYMENT_ACTIVE=True,
            _PAYMENT_RECEIPT_ADMIN_INSTALLED=True,
            _is_admin=lambda uid: str(uid) == ADMIN,
            _payment_request=self.read_row,
            send=self.send_admin,
            API="https://api.telegram.org/bot123456789:token",
        )
        app=Flask(__name__)
        app.register_blueprint(create_web_receipt_admin_notification(self.runtime))
        self.client=app.test_client()
        self.env=patch.dict(os.environ, {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": SECRET})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.post=patch("web.telegram_web_receipt_admin_notification.requests.post",
                        side_effect=self.copy_message)
        self.post.start()
        self.addCleanup(self.post.stop)

    def read_row(self,rid):
        self.lookup.append(rid)
        return dict(self.row)

    def send_admin(self,uid,text,kb):
        self.sent.append({"uid":uid, "text":text, "kb":kb})
        return Response(data={"ok":True,"result":{
            "message_id":404,"chat":{"id":int(uid)},
        }})

    def copy_message(self, url, **kwargs):
        self.copied.append({"url":url, **kwargs})
        return Response()

    def notify(self, *, rid=41, uid=7001234, authorization=None):
        return self.client.post(REVIEW_PATH,
            headers={"Authorization": authorization or "Bearer "+SECRET},
            json={"request_id":rid, "telegram_user_id":uid})

    def test_rm20_receipt_notifies_admin_with_actual_amount(self):
        self.row["amount"] = "20.00"
        self.assertEqual(self.notify().status_code, 200)
        self.assertIn("RM20.00", self.copied[0]["json"]["caption"])

    def test_registration_never_sends_or_reviews(self):
        self.assertEqual(self.copied, [])
        self.assertEqual(self.sent, [])
        self.assertEqual(self.lookup, [])

    def test_verified_pending_receipt_copied_to_admin_with_review_button(self):
        response=self.notify()
        self.assertEqual(response.status_code,200,response.get_json())
        self.assertEqual(response.json,{
            "notified":True, "request_id":41,
            "review":"admin_only", "delivery":"receipt_with_buttons"})
        self.assertEqual(self.lookup,[41])
        self.assertEqual(self.sent,[])
        self.assertEqual(len(self.copied),1)
        req=self.copied[0]
        self.assertTrue(req["url"].endswith("/copyMessage"))
        self.assertEqual(req["json"]["from_chat_id"],"7001234")
        self.assertEqual(req["json"]["chat_id"],ADMIN)
        self.assertEqual(req["json"]["message_id"],567)
        self.assertIn("#41",req["json"]["caption"])
        self.assertIn("RM10.00",req["json"]["caption"])
        buttons=req["json"]["reply_markup"]["inline_keyboard"]
        self.assertEqual(buttons,_keyboard(41)["inline_keyboard"])
        self.assertEqual(buttons[0][0]["callback_data"],"pioneer_review|41")
        self.assertEqual(buttons[1][0]["callback_data"],"admin_pending_all")
        self.assertNotIn("admin_receipt|",str(buttons))
        self.assertNotIn("admin_approve",repr(req))

    def test_fallback_maintains_exact_review_when_receipt_copy_fails(self):
        with patch("web.telegram_web_receipt_admin_notification.requests.post",
                   return_value=Response(400,{"ok":False})):
            response=self.notify()
        self.assertEqual(response.status_code,200,response.get_json())
        self.assertEqual(response.json["delivery"],"review_buttons")
        self.assertEqual(self.sent[0]["uid"],ADMIN)
        self.assertEqual(self.sent[0]["kb"][0][0]["callback_data"],"pioneer_review|41")
        self.assertEqual(self.sent[0]["kb"][1][0]["callback_data"],"admin_pending_all")

    def test_no_false_success_when_both_telegram_methods_fail(self):
        with patch("web.telegram_web_receipt_admin_notification.requests.post",
                   return_value=Response(403,{"ok":False})),\
             patch.object(self.runtime,"send",return_value=Response(403,{"ok":False})):
            r=self.notify()
        self.assertEqual(r.status_code,503)
        self.assertEqual(self.lookup,[41])

    def test_missing_or_mismatched_pending_proof_is_rejected_without_sending(self):
        changes=[
            {"id":42},{"chat_id":"7009999"},{"status":"approved"},
            {"amount":"5.00"},{"notes":"anything_else"},
            {"proof_telegram_file_id":""},
            {"proof_telegram_message_id":0},
            {"proof_received_at":None},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.row=dict(ROW,**change)
                self.assertEqual(self.notify().status_code,409)
        self.assertEqual(self.copied,[])
        self.assertEqual(self.sent,[])
        self.assertEqual(_valid_pending_row(dict(ROW),7001234,41),True)

    def test_wrong_caller_auth_or_unconfigured_admin_denied(self):
        self.assertEqual(self.notify(authorization="Bearer wrong").status_code,401)
        self.assertEqual(self.copied,[])
        self.runtime.ADMIN_CHAT_ID=""
        self.assertEqual(self.notify().status_code,503)
        self.runtime.ADMIN_CHAT_ID=ADMIN
        self.runtime._is_admin=lambda _:False
        self.assertEqual(self.notify().status_code,503)
        self.assertEqual(self.lookup,[])

    def test_untrusted_ids_and_extra_fields_denied(self):
        for obj in (
            {"request_id":True,"telegram_user_id":7001234},
            {"request_id":41,"telegram_user_id":"7001234"},
            {"request_id":41,"telegram_user_id":7001234,"approve":True},
            {"request_id":0,"telegram_user_id":7001234},
            {"request_id":41,"telegram_user_id":-1},
        ):
            with self.subTest(obj=obj):
                r=self.client.post(REVIEW_PATH,
                    json=obj,headers={"Authorization":"Bearer "+SECRET})
                self.assertEqual(r.status_code,400)
        self.assertEqual(self.lookup,[])
        self.assertEqual(self.copied,[])

    def test_lookup_failure_does_not_notify_or_change_records(self):
        with patch.object(self.runtime, "_payment_request",
                          side_effect=RuntimeError("database down")):
            r=self.notify()
        self.assertEqual(r.status_code,503)
        self.assertEqual(self.copied,[])
        self.assertEqual(self.sent,[])


if __name__=="__main__":
    unittest.main()
