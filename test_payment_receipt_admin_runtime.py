"""Receipt display tests; no real Telegram or Supabase network activity."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web.payment_receipt_admin_runtime import install, malaysia_time


class Response:
    def __init__(self, ok=True):
        self.ok = ok
    def json(self):
        return {"ok": self.ok}


class Runtime:
    API = "https://telegram.invalid/bot-TEST"
    def __init__(self, receipt=False, mime="telegram/photo"):
        self.sent = []
        self.delegated = []
        self.records = {1: {"id": 1, "chat_id":"301","amount":"10.00",
                            "status":"pending", "notes":"awaiting_proof",
                            "submitted_at":"2026-11-04T09:48:34+00:00",
                            "proof_received_at":"2026-11-04T09:55:00+00:00" if receipt else None,
                            "proof_telegram_file_id":"tg-file-private" if receipt else None,
                            "proof_mime_type":mime,
                            "proof_telegram_message_id":777 if receipt else None}}
        self._payment_request=lambda rid:self.records.get(int(rid))
        self._is_admin=lambda cid:str(cid)=="1"
        self._admin_pending_card=lambda cid,rid:self.delegated.append(("card",rid))
        self.callback=lambda cid,d:self.delegated.append(("callback",d))
    def send(self, cid, text, buttons=None):
        self.sent.append((cid,text,buttons or []))
        return True
    def buttons(self):
        return [b.get("callback_data") for row in self.sent[-1][2] for b in row]


class TestReceiptAdmin(unittest.TestCase):
    def test_utc_to_malaysia(self):
        self.assertEqual(malaysia_time("2026-11-04T09:55:00Z"),
                         "04/11/2026 17:55:00 MYT")
        self.assertEqual(malaysia_time(None), "Belum direkodkan")
        self.assertEqual(malaysia_time("nonsense"),"Masa tidak tersedia")

    def test_pending_no_receipt_has_no_preview_and_shows_request_time(self):
        rt=Runtime()
        self.assertTrue(install(rt))
        rt._admin_pending_card(1,1)
        self.assertIn("04/11/2026 17:48:34 MYT",rt.sent[-1][1])
        self.assertIn("Resit dihantar: Belum direkodkan",rt.sent[-1][1])
        self.assertNotIn("admin_receipt|1",rt.buttons())
        self.assertEqual(rt.delegated,[("card",1)])
        rt.callback(1,"admin_receipt|1")
        self.assertIn("Fail resit belum direkodkan",rt.sent[-1][1])

    def test_non_admin_cannot_view_private_receipt(self):
        rt=Runtime(receipt=True)
        install(rt)
        rt._admin_pending_card(301,1)
        self.assertIn("Admin sahaja",rt.sent[-1][1])
        with patch("requests.post") as p:
            rt.callback(301,"admin_receipt|1")
        p.assert_not_called()
        self.assertIn("Admin sahaja",rt.sent[-1][1])

    def test_photo_file_id_sent_to_admin_only(self):
        rt=Runtime(receipt=True)
        install(rt)
        rt._admin_pending_card(1,1)
        self.assertIn("admin_receipt|1",rt.buttons())
        with patch("requests.post",return_value=Response()) as post:
            rt.callback(1,"admin_receipt|1")
        post.assert_called_once()
        endpoint=post.call_args.args[0]
        payload=post.call_args.kwargs["json"]
        self.assertTrue(endpoint.endswith("/sendPhoto"))
        self.assertEqual(payload["photo"],"tg-file-private")
        self.assertEqual(payload["chat_id"],"1")
        self.assertIn("17:55:00 MYT",payload["caption"])

    def test_pdf_file_id_uses_send_document(self):
        rt=Runtime(receipt=True,mime="application/pdf")
        install(rt)
        with patch("requests.post",return_value=Response()) as post:
            rt.callback(1,"admin_receipt|1")
        self.assertTrue(post.call_args.args[0].endswith("/sendDocument"))
        self.assertEqual(post.call_args.kwargs["json"]["document"],"tg-file-private")

    def test_expired_file_id_falls_back_to_original_telegram_message(self):
        rt=Runtime(receipt=True)
        install(rt)
        with patch("requests.post",side_effect=[Response(False),Response()]) as post:
            rt.callback(1,"admin_receipt|1")
        self.assertEqual(post.call_count,2)
        payload=post.call_args.kwargs["json"]
        self.assertTrue(post.call_args.args[0].endswith("/copyMessage"))
        self.assertEqual(payload["from_chat_id"],"301")
        self.assertEqual(payload["message_id"],777)

    def test_unknown_actions_are_preserved(self):
        rt=Runtime(receipt=True)
        install(rt)
        rt.callback(1,"admin_approve|1|301")
        self.assertEqual(rt.delegated[-1],("callback","admin_approve|1|301"))
        self.assertTrue(install(rt))

    def test_invalid_id_and_missing_record_fail_closed(self):
        rt=Runtime(receipt=True)
        install(rt)
        for d in ["admin_receipt|x","admin_receipt|-2","admin_receipt|1|301"]:
            rt.callback(1,d)
            self.assertIn("tidak sah",rt.sent[-1][1])
        rt.callback(1,"admin_receipt|99")
        self.assertIn("tidak ditemui",rt.sent[-1][1])

    def test_receipt_preview_never_modifies_payment(self):
        rt=Runtime(receipt=True)
        before=dict(rt.records[1])
        install(rt)
        with patch("requests.post",return_value=Response()):
            rt._admin_pending_card(1,1)
            rt.callback(1,"admin_receipt|1")
        self.assertEqual(rt.records[1],before)


if __name__ == "__main__":
    unittest.main()
