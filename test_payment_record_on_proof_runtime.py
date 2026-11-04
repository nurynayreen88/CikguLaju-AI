"""Offline regression tests: opening a payment QR never creates pending payments."""
import base64
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web import payment_record_on_proof_runtime as proof


class Response:
    ok = True
    def json(self):
        return {"ok": True, "result": {"photo": [{"file_id": "QR_FILE_ID"}]}}


class Runtime:
    def __init__(self):
        self.state = {}
        self.API = "https://example.invalid/bot-token"
        self.DONATION_QR_B64 = base64.b64encode(b"fake-qr-image").decode()
        self._donation_qr_file_id = None
        self.requests = []
        self.sent = []
        self.message = None
        self.request = SimpleNamespace(get_json=lambda silent=True: self.message or {})
        self._new_payment_request = self.new_request
        self._latest_pending_payment = self.latest
        self._payment_request = self.payment
        self.send_subscription_payment = lambda cid: "old subscription"
        self._is_admin = lambda cid: int(cid) == 1
        self.send = lambda cid, text, kb=None: self.sent.append((cid, text, kb)) or True

    def latest(self, cid):
        return next((x for x in self.requests
                     if x["chat_id"] == str(cid) and x["status"] == "pending"), None)

    def new_request(self, cid, mid=None, amount=5):
        old = self.latest(cid)
        if old:
            return old["id"]
        record = {"id": len(self.requests) + 1, "chat_id": str(cid),
                  "status": "pending", "amount": str(amount),
                  "telegram_message_id": mid}
        self.requests.append(record)
        return record["id"]

    def payment(self, rid):
        return next((x for x in self.requests if x["id"] == rid), None)

    def upload(self, *, uid=301, mid=777, mime="application/pdf", sender=None, chat_type="private"):
        self.message = {"message": {
            "chat": {"id": uid, "type": chat_type},
            "from": {"id": uid if sender is None else sender},
            "message_id": mid,
            "document": {"file_id": "TG_RESIT_PDF", "mime_type": mime}
        }}


class ProofFirstTests(unittest.TestCase):
    def setUp(self):
        self.rt = Runtime()
        self.assertTrue(proof.install(self.rt))

    def test_subscription_qr_does_not_create_any_request(self):
        with patch("requests.post", return_value=Response()) as send:
            self.rt.send_subscription_payment(301)
        self.assertEqual(len(self.rt.requests), 0)
        self.assertEqual(self.rt.state[301]["waiting"], "payment_proof")
        self.assertEqual(self.rt.state[301]["payment_amount"], 5.0)
        self.assertIn("/sendPhoto", send.call_args.args[0])
        self.assertIsNone(self.rt._latest_pending_payment(301))

    def test_legacy_default_rm5_does_not_replace_selected_rm10(self):
        self.rt.state[301] = {"waiting": "payment_proof", "payment_amount": 10.0}
        self.rt.upload()
        virtual = self.rt._latest_pending_payment(301)
        self.assertIsNone(virtual["id"])
        self.assertEqual(virtual["amount"], 10.0)
        rid = self.rt._new_payment_request(301, 777, 5.0)
        self.assertEqual(rid, 1)
        self.assertEqual(float(self.rt.requests[0]["amount"]), 10.0)
        self.assertIsNotNone(self.rt._latest_pending_payment(301)["id"])

    def test_receipt_creates_rm5_once_and_preserves_original_message(self):
        self.rt.state[301] = {"waiting": "payment_proof", "payment_amount": 5.0}
        self.rt.upload()
        virtual = self.rt._latest_pending_payment(301)
        self.assertEqual(virtual["amount"], 5.0)
        first = self.rt._new_payment_request(301, 777, 5.0)
        second = self.rt._new_payment_request(301, 777, 5.0)
        self.assertEqual((first, second), (1, 1))
        self.assertEqual(len(self.rt.requests), 1)
        self.assertEqual(self.rt.requests[0]["telegram_message_id"], 777)

    def test_only_photo_or_pdf_file_with_actual_id_creates(self):
        self.rt.state[301] = {"waiting": "payment_proof", "payment_amount": 10.0}
        self.rt.message = {"message": {
            "chat": {"id": 301, "type": "private"},
            "from": {"id": 301},
            "message_id": 777,
            "photo": [{"file_id": "PHOTO_BEST_SIZE"}]
        }}
        self.assertEqual(self.rt._latest_pending_payment(301)["amount"], 10.0)
        self.assertEqual(self.rt._new_payment_request(301, 777, 5), 1)

    def test_non_receipt_or_no_consent_never_creates(self):
        self.rt.state[301] = {"waiting": "payment_proof", "payment_amount": 10.0}
        for message in [
            {"message": {"chat": {"id": 301, "type": "private"},
                         "from": {"id": 301}, "message_id": 777, "text": "Hi"}},
            {"message": {"chat": {"id": 301, "type": "private"},
                         "from": {"id": 301}, "message_id": 777,
                         "document": {"file_id": "X", "mime_type": "text/plain"}}},
            {"message": {"chat": {"id": 301, "type": "group"},
                         "from": {"id": 301}, "message_id": 777,
                         "photo": [{"file_id": "X"}]}},
            {"message": {"chat": {"id": 301, "type": "private"},
                         "from": {"id": 302}, "message_id": 777,
                         "photo": [{"file_id": "X"}]}},
        ]:
            self.rt.message = message
            self.assertIsNone(self.rt._latest_pending_payment(301))
            with self.assertRaises(ValueError):
                self.rt._new_payment_request(301, 777, 5)
        self.assertEqual(len(self.rt.requests), 0)

    def test_stale_or_cross_user_message_is_never_accepted(self):
        self.rt.state[301] = {"waiting": "payment_proof", "payment_amount": 10.0}
        self.rt.upload()
        with self.assertRaises(ValueError):
            self.rt._new_payment_request(301, 778, 5)
        with self.assertRaises(ValueError):
            self.rt._new_payment_request(302, 777, 5)
        self.assertEqual(len(self.rt.requests), 0)

    def test_callback_without_flask_request_context_never_writes(self):
        self.rt.state[301] = {"waiting": "payment_proof", "payment_amount": 10.0}
        def missing_context(silent=True):
            raise RuntimeError("Working outside of request context")
        self.rt.request = SimpleNamespace(get_json=missing_context)
        self.assertIsNone(self.rt._latest_pending_payment(301))
        with self.assertRaises(ValueError):
            self.rt._new_payment_request(301, 777, 5)
        self.assertEqual(self.rt.requests, [])

    def test_no_payment_intent_never_creates_request(self):
        self.rt.upload()
        self.assertIsNone(self.rt._latest_pending_payment(301))
        with self.assertRaises(ValueError):
            self.rt._new_payment_request(301, 777, 5)
        self.assertEqual(len(self.rt.requests), 0)

    def test_existing_pending_kept_and_other_plan_not_shown(self):
        self.rt.requests.append({"id": 42, "chat_id": "301", "status": "pending",
                                 "amount": "10.00", "notes": "awaiting_proof"})
        with patch("requests.post") as send:
            self.rt.send_subscription_payment(301)
        send.assert_not_called()
        self.assertEqual(self.rt.requests[0]["id"], 42)
        self.assertIn("permohonan bayaran lain", self.rt.sent[-1][1])

    def test_already_uploaded_receipt_blocks_new_qr(self):
        self.rt.requests.append({"id": 42, "chat_id": "301", "status": "pending",
                                 "amount": "5.00", "notes": "proof_received_admin_notified"})
        with patch("requests.post") as send:
            self.rt.send_subscription_payment(301)
        send.assert_not_called()
        self.assertIn("sedang disemak admin", self.rt.sent[-1][1])

    def test_idempotent_install_and_unrelated_function_untouched(self):
        old = self.rt.send_subscription_payment
        self.assertTrue(proof.install(self.rt))
        self.assertIs(self.rt.send_subscription_payment, old)
        self.assertEqual(self.rt._is_admin(1), True)
        self.assertEqual(self.rt.requests, [])


if __name__ == "__main__":
    unittest.main()
