"""Admin pending payment card shows a receipt immediately: offline regressions."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web.payment_receipt_admin_runtime import install, malaysia_time


class Response:
    def __init__(self, *, ok=True, copied=False, cid=1):
        self.ok = ok
        self.copied = copied
        self.cid = cid

    def json(self):
        if not self.ok:
            return {"ok": False}
        result = {"message_id": 808}
        if not self.copied:
            result["chat"] = {"id": self.cid}
        return {"ok": True, "result": result}


class Runtime:
    API = "https://telegram.invalid/bot-TEST"

    def __init__(self, *, receipt=True, mime="telegram/photo"):
        self.sent = []
        self.delegated = []
        self.reads = []
        self.user_reads = []
        self.records = {
            1: {"id": 1, "chat_id": "301", "amount": "10.00",
                "status": "pending",
                "notes": "proof_received_web" if receipt else "awaiting_proof",
                "submitted_at": "2026-11-04T09:48:34+00:00",
                "proof_received_at": "2026-11-04T09:55:00+00:00" if receipt else None,
                "proof_telegram_file_id": "tg-file-private" if receipt else None,
                "proof_mime_type": mime,
                "proof_telegram_message_id": 777 if receipt else None,
                }
        }
        self._payment_request = self.payment_request
        self._is_admin = lambda cid: str(cid) == "1"
        self._admin_pending_card = lambda cid, rid: self.delegated.append(("card", rid))
        self.callback = lambda cid, d: self.delegated.append(("callback", d))
        self._sb_request = self.user_query

    def payment_request(self, rid):
        self.reads.append(int(rid))
        return self.records.get(int(rid))

    def user_query(self, method, query, **kw):
        self.user_reads.append((method, query))
        return [{"first_name": "Cikgu", "last_name": "Ali <Nama>",
                 "username": "cikgualitest"}]

    def send(self, cid, text, buttons=None):
        self.sent.append((cid, text, buttons or []))
        return Response(cid=int(cid))

    def buttons(self):
        return [b.get("callback_data") for row in self.sent[-1][2] for b in row]


class TestReceiptAdmin(unittest.TestCase):
    def test_utc_to_malaysia(self):
        self.assertEqual(malaysia_time("2026-11-04T09:55:00Z"),
                         "04/11/2026 17:55:00 MYT")
        self.assertEqual(malaysia_time(None), "Belum direkodkan")

    def test_name_tap_opens_single_photo_with_details_and_actions(self):
        rt = Runtime()
        install(rt)
        with patch("requests.post", return_value=Response()) as post:
            rt._admin_pending_card(1, 1)
        self.assertEqual(rt.reads, [1])
        self.assertEqual(rt.delegated, [])
        self.assertEqual(rt.sent, [])
        post.assert_called_once()
        self.assertTrue(post.call_args.args[0].endswith("/sendPhoto"))
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["chat_id"], "1")
        self.assertEqual(body["photo"], "tg-file-private")
        self.assertEqual(body["parse_mode"], "HTML")
        self.assertIn("Cikgu Ali &lt;Nama&gt;", body["caption"])
        self.assertIn("Payment ID: <b>#1</b>", body["caption"])
        self.assertIn("RM10.00", body["caption"])
        self.assertIn("17:48:34 MYT", body["caption"])
        self.assertIn("17:55:00 MYT", body["caption"])
        self.assertIn("\n", body["caption"])
        self.assertNotIn("\\n", body["caption"])
        buttons = [b["callback_data"]
                   for row in body["reply_markup"]["inline_keyboard"]
                   for b in row]
        self.assertIn("admin_approve|1|301", buttons)
        self.assertIn("admin_reject|1", buttons)
        self.assertIn("admin_pending_all", buttons)
        self.assertNotIn("admin_receipt|1", buttons)
        self.assertNotIn("pioneer_review|1", buttons)
        self.assertTrue(rt.user_reads)

    def test_pdf_sends_document_with_same_caption_and_approval(self):
        rt = Runtime(mime="application/pdf")
        install(rt)
        with patch("requests.post", return_value=Response()) as post:
            rt._admin_pending_card(1, 1)
        post.assert_called_once()
        self.assertTrue(post.call_args.args[0].endswith("/sendDocument"))
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["document"], "tg-file-private")
        self.assertIn("admin_approve|1|301", str(payload["reply_markup"]))
        self.assertIn("PENGESAHAN RAKAN PEMBANGUN", payload["caption"])

    def test_web_uploaded_jpg_document_keeps_senddocument(self):
        rt = Runtime(mime="image/jpeg")
        install(rt)
        with patch("requests.post", return_value=Response()) as post:
            rt._admin_pending_card(1, 1)
        self.assertTrue(post.call_args.args[0].endswith("/sendDocument"))

    def test_expired_file_id_tries_original_copy_with_review_actions(self):
        rt = Runtime()
        install(rt)
        with patch("requests.post",
                   side_effect=[Response(ok=False), Response(copied=True)]) as post:
            rt._admin_pending_card(1, 1)
        self.assertEqual(post.call_count, 2)
        self.assertTrue(post.call_args.args[0].endswith("/copyMessage"))
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["from_chat_id"], "301")
        self.assertEqual(payload["message_id"], 777)
        self.assertIn("admin_approve|1|301", str(payload["reply_markup"]))

    def test_only_message_id_can_copy_without_file_id(self):
        rt = Runtime()
        rt.records[1]["proof_telegram_file_id"] = None
        install(rt)
        with patch("requests.post", return_value=Response(copied=True)) as post:
            rt._admin_pending_card(1, 1)
        post.assert_called_once()
        self.assertTrue(post.call_args.args[0].endswith("/copyMessage"))

    def test_no_proof_shows_details_but_no_approve_button(self):
        rt = Runtime(receipt=False)
        install(rt)
        with patch("requests.post") as post:
            rt._admin_pending_card(1, 1)
        post.assert_not_called()
        self.assertEqual(len(rt.sent), 1)
        self.assertEqual(rt.delegated, [])
        self.assertIn("17:48:34 MYT", rt.sent[-1][1])
        self.assertIn("Fail resit tidak tersimpan", rt.sent[-1][1])
        self.assertNotIn("admin_approve|1|301", rt.buttons())
        self.assertIn("admin_reject|1", rt.buttons())
        self.assertNotIn("admin_receipt|1", rt.buttons())

    def test_media_delivery_failure_shows_retry_not_approval(self):
        rt = Runtime()
        install(rt)
        with patch("requests.post", return_value=Response(ok=False)) as post:
            rt._admin_pending_card(1, 1)
        self.assertEqual(post.call_count, 2)
        self.assertEqual(len(rt.sent), 1)
        self.assertIn("tidak dapat dipaparkan", rt.sent[-1][1])
        self.assertNotIn("admin_approve|1|301", rt.buttons())
        self.assertIn("admin_pending|1", rt.buttons())

    def test_non_admin_cannot_read_or_send_receipt(self):
        rt = Runtime()
        install(rt)
        with patch("requests.post") as post:
            rt._admin_pending_card(301, 1)
        post.assert_not_called()
        self.assertEqual(rt.reads, [])
        self.assertEqual(rt.user_reads, [])
        self.assertIn("Admin sahaja", rt.sent[-1][1])
        self.assertNotIn("admin_approve|1|301", rt.buttons())

    def test_stale_or_invalid_row_never_shows_approval(self):
        rt = Runtime()
        rt.records[1]["id"] = 17
        install(rt)
        with patch("requests.post") as post:
            rt._admin_pending_card(1, 1)
        post.assert_not_called()
        self.assertNotIn("admin_approve|1|301", rt.buttons())
        self.assertIn("tidak sepadan", rt.sent[-1][1])

    def test_non_pending_or_other_plan_still_uses_original_card(self):
        for status, amount in (("approved", "10.00"), ("pending", "8.00")):
            with self.subTest(status=status, amount=amount):
                rt = Runtime()
                rt.records[1]["status"] = status
                rt.records[1]["amount"] = amount
                install(rt)
                with patch("requests.post") as post:
                    rt._admin_pending_card(1, 1)
                post.assert_not_called()
                self.assertEqual(rt.delegated, [("card", 1)])

    def test_legacy_papar_resit_callback_still_works_for_old_messages(self):
        rt = Runtime()
        install(rt)
        with patch("requests.post", return_value=Response()) as post:
            rt.callback(1, "admin_receipt|1")
        post.assert_called_once()
        self.assertTrue(post.call_args.args[0].endswith("/sendPhoto"))

    def test_unknown_callbacks_and_id_validation_preserved(self):
        rt = Runtime()
        install(rt)
        rt.callback(1, "admin_approve|1|301")
        self.assertEqual(rt.delegated, [("callback", "admin_approve|1|301")])
        for d in ("admin_receipt|x", "admin_receipt|-2", "admin_receipt|1|301"):
            rt.callback(1, d)
            self.assertIn("tidak sah", rt.sent[-1][1])
        self.assertTrue(install(rt))

    def test_receipt_card_never_changes_payment_or_entitlement(self):
        rt = Runtime()
        original = dict(rt.records[1])
        install(rt)
        with patch("requests.post", return_value=Response()):
            rt._admin_pending_card(1, 1)
        self.assertEqual(rt.records[1], original)


if __name__ == "__main__":
    unittest.main()
