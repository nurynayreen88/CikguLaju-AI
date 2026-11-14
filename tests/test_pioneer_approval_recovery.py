"""Regression tests: old Rakan Pembangun approval buttons never grant blindly."""
import re
import unittest
from unittest.mock import patch

import pioneer_telegram


ADMIN = 9001
PAYER = 201


class Bot:
    def __init__(self, *, payer=PAYER, amount=10.0, notes="proof_received_admin_notified"):
        self.requests = {
            1: {"id": 1, "chat_id": payer, "amount": amount,
                "status": "pending", "notes": notes}}
        self.messages = []
        self.marked = []
        self.delegated = []
        self.db_rows = []

    def send(self, cid, message, keyboard=None):
        self.messages.append((cid, message, keyboard or []))
        return {"ok": True}

    def payment(self, rid):
        return self.requests.get(rid)

    def mark(self, rid, status, admin, note):
        self.marked.append((rid, status, admin, note))
        self.requests[rid]["status"] = status

    def old_callback(self, cid, data):
        self.delegated.append(("callback", cid, data))
        return "old"

    def old_card(self, cid, rid):
        self.delegated.append(("card", cid, rid))
        return self.send(cid, "Existing subscription card")

    def old_user(self, cid, uid):
        self.delegated.append(("user", cid, uid))
        return self.send(cid, "Existing user card")

    def namespace(self):
        return {
            "callback": self.old_callback,
            "menu": lambda cid, show_persistent=False: "old menu",
            "_access_info": lambda cid: {"active": False},
            "_admin_pending_card": self.old_card,
            "_admin_user_card": self.old_user,
            "_is_admin": lambda cid: int(cid) == ADMIN,
            "_payment_request": self.payment,
            "_mark_payment_request": self.mark,
            "_latest_pending_payment": lambda cid: None,
            "_sb_request": lambda method, path, **kw: (
                self.db_rows if path.startswith(
                    "pioneer_entitlements?telegram_user_id=eq.") else []),
            "state": {},
            "send": self.send,
        }


class TestStalePioneerApproval(unittest.TestCase):
    def setUp(self):
        self.bot = Bot()
        self.grant = patch("pioneer_telegram.grant_pioneer")
        self.grant_mock = self.grant.start()
        self.has = patch("pioneer_telegram.has_pioneer", return_value=False)
        self.has.start()
        self.referral = patch("referral_points_telegram.install", return_value=False)
        self.referral.start()
        self.addCleanup(self.grant.stop)
        self.addCleanup(self.has.stop)
        self.addCleanup(self.referral.stop)
        self.ns = self.bot.namespace()
        self.assertTrue(pioneer_telegram.install(self.ns))

    def buttons(self):
        return [b.get("callback_data") for row in self.bot.messages[-1][2] for b in row]

    def test_rm20_qr_and_receipt_button_do_not_create_pending_without_upload(self):
        import base64
        from types import SimpleNamespace
        self.ns["API"] = "https://example.invalid/bot"
        self.ns["DONATION_QR_B64"] = base64.b64encode(b"qr-photo").decode()
        self.ns["_donation_qr_file_id"] = "EXISTING_QR_FILE"
        self.ns["_new_payment_request"] = lambda *args, **kwargs: self.fail(
            "No database insert allowed before receipt upload")
        self.ns["_set_payment_note"] = lambda *args, **kwargs: self.fail(
            "No premature payment note allowed")
        self.ns["_latest_pending_payment"] = lambda cid: None
        telegram = SimpleNamespace(ok=True)
        with patch("pioneer_telegram.pioneer_availability", return_value=(0, 500)):
            with patch("requests.post", return_value=telegram) as sent:
                self.ns["callback"](PAYER, "pioneer_pay")
        self.assertEqual(sent.call_count, 1)
        self.assertEqual(self.ns["state"][PAYER]["waiting"], "payment_proof")
        self.assertEqual(self.ns["state"][PAYER]["payment_amount"], 20.0)
        self.ns["state"][PAYER].clear()
        with patch("pioneer_telegram.pioneer_availability", return_value=(0, 500)):
            self.ns["callback"](PAYER, "pioneer_receipt")
        self.assertEqual(self.ns["state"][PAYER]["payment_amount"], 20.0)
        self.assertEqual(self.ns["state"][PAYER]["waiting"], "payment_proof")
        self.assertEqual(self.bot.marked, [])

    def test_full_batch_blocks_new_join_receipt_and_qr(self):
        self.ns["_latest_pending_payment"]=lambda cid: None
        with patch("pioneer_telegram.pioneer_availability", return_value=(500, 0)):
            self.ns["callback"](PAYER, "pioneer_join")
            self.assertIn("sudah penuh",self.bot.messages[-1][1])
            self.assertNotIn("pioneer_pay",self.buttons())
            self.ns["callback"](PAYER, "pioneer_receipt")
            self.assertIn("penuh",self.bot.messages[-1][1])
            self.ns["callback"](PAYER, "pioneer_pay")
            self.assertIn("penuh",self.bot.messages[-1][1])
        self.assertNotIn("payment_proof",str(self.ns["state"]))

    def test_two_part_legacy_button_reopens_current_card_but_never_approves(self):
        self.ns["callback"](ADMIN, "admin_approve|1")
        msg = self.bot.messages[-1][1]
        self.assertIn("ID pelanggan Telegram: <code>201</code>", msg)
        self.assertIn("ID permohonan: <code>1</code>", msg)
        self.assertIn("admin_user|201", self.buttons())
        self.assertIn("admin_approve|1|201", self.buttons())
        self.assertIn("pioneer_review|1", self.buttons())
        self.assertEqual(self.bot.marked, [])
        self.grant_mock.assert_not_called()

    def test_reopen_then_manually_verified_fresh_button_grants_same_user_only(self):
        self.ns["callback"](ADMIN, "admin_approve|1")
        self.ns["callback"](ADMIN, "admin_approve|1|201")
        self.assertEqual(self.bot.marked[0][:3], (1, "approved", ADMIN))
        self.grant_mock.assert_called_once()
        args, kwargs = self.grant_mock.call_args
        self.assertEqual(args[1], PAYER)
        self.assertEqual(args[3], ADMIN)
        self.assertTrue(kwargs["verified"])
        self.assertRegex(args[2], r"^pioneer-payment:201:[a-f0-9]{32}$")
        self.assertEqual(self.bot.requests[1]["status"], "approved")

    def test_revoked_member_is_reactivated_only_after_explicit_admin_confirmation(self):
        previous = [{"entitlement": "PIONEER_LIFETIME",
                     "payment_reference": "old-payment-verified",
                     "revoked_at": "2026-11-05T22:39:22Z"}]
        self.bot.db_rows = previous
        # The bridge was installed with a closure using ns, so it sees the
        # replacement durable lookup without re-installing wrappers.
        with patch("pioneer_telegram.reactivate_revoked_pioneer",
                   return_value={"approved": True, "reactivated": True}) as restore:
            self.ns["callback"](ADMIN, "admin_approve|1")
            self.assertEqual(self.bot.marked, [])
            restore.assert_not_called()
            self.ns["callback"](ADMIN, "admin_approve|1|201")
            restore.assert_called_once()
            args, kw = restore.call_args
            self.assertEqual((args[1], args[3], args[4]), (PAYER, ADMIN, 1))
            self.assertTrue(kw["verified"])
            self.assertEqual(self.bot.marked[0][:3], (1, "approved", ADMIN))
            self.grant_mock.assert_not_called()

    def test_revoked_member_rpc_failure_preserves_pending_and_history(self):
        self.bot.db_rows = [
            {"entitlement":"PIONEER_LIFETIME",
             "revoked_at":"2026-11-05T22:39:22Z"}]
        with patch("pioneer_telegram.reactivate_revoked_pioneer",
                   side_effect=RuntimeError("Matching pending verified proof required")) as restore:
            self.ns["callback"](ADMIN, "admin_approve|1|201")
        restore.assert_called_once()
        self.assertEqual(self.bot.requests[1]["status"], "pending")
        self.assertEqual(self.bot.marked, [])
        self.grant_mock.assert_not_called()
        self.assertIn("belum diaktifkan", self.bot.messages[-1][1])

    def test_revoked_member_unconfirmed_result_never_marks_payment_approved(self):
        self.bot.db_rows = [
            {"entitlement":"PIONEER_LIFETIME",
             "revoked_at":"2026-11-05T22:39:22Z"}]
        with patch("pioneer_telegram.reactivate_revoked_pioneer",
                   return_value={"approved": False}) as restore:
            self.ns["callback"](ADMIN, "admin_approve|1|201")
        restore.assert_called_once()
        self.assertEqual(self.bot.marked, [])
        self.assertEqual(self.bot.requests[1]["status"], "pending")

    def test_no_reactivation_if_proof_is_missing_or_owner_differs(self):
        self.bot.db_rows = [
            {"entitlement":"PIONEER_LIFETIME",
             "revoked_at":"2026-11-05T22:39:22Z"}]
        with patch("pioneer_telegram.reactivate_revoked_pioneer") as restore:
            self.bot.requests[1]["notes"]="awaiting_proof"
            self.ns["callback"](ADMIN, "admin_approve|1|201")
            self.bot.requests[1]["notes"]="proof_received_web"
            self.bot.requests[1]["chat_id"]=202
            self.ns["callback"](ADMIN, "admin_approve|1|201")
        restore.assert_not_called()
        self.assertEqual(self.bot.marked, [])

    def test_mismatched_owner_blocks_approval_and_shows_both_ids(self):
        self.bot.requests[1]["chat_id"] = 202
        self.ns["callback"](ADMIN, "admin_approve|1|201")
        msg = self.bot.messages[-1][1]
        self.assertIn("ID PELANGGAN TIDAK SEPADAN", msg)
        self.assertIn("<code>201</code>", msg)
        self.assertIn("<code>202</code>", msg)
        self.assertIn("pioneer_review|1", self.buttons())
        self.assertEqual(self.bot.marked, [])
        self.grant_mock.assert_not_called()
        self.ns["callback"](ADMIN, "pioneer_review|1")
        self.assertIn("ID pelanggan Telegram: <code>202</code>", self.bot.messages[-1][1])
        self.assertIn("admin_approve|1|202", self.buttons())
        self.grant_mock.assert_not_called()

    def test_durable_rakan_uses_shared_review_for_both_decisions(self):
        from unittest.mock import Mock

        self.ns["_review_rakan_payment"] = Mock(side_effect=[
            {"status": "approved"}, {"status": "rejected"}])
        self.ns["callback"](ADMIN, "admin_approve|1|201")
        self.ns["callback"](ADMIN, "admin_reject|1")
        calls = self.ns["_review_rakan_payment"].call_args_list
        self.assertEqual([call.args[2] for call in calls], ["approved", "rejected"])
        self.assertTrue(all(call.args[:2] == (self.bot.requests[1], ADMIN) for call in calls))
        self.assertEqual(self.bot.marked, [])

    def test_missing_proof_blocks_even_forged_fresh_button(self):
        self.bot.requests[1]["notes"] = "awaiting_proof"
        self.ns["callback"](ADMIN, "admin_approve|1")
        self.assertNotIn("admin_approve|1|201", self.buttons())
        self.assertIn("Resit belum direkodkan", self.bot.messages[-1][1])
        self.ns["callback"](ADMIN, "admin_approve|1|201")
        self.assertIn("Resit belum direkodkan", self.bot.messages[-1][1])
        self.assertEqual(self.bot.marked, [])
        self.grant_mock.assert_not_called()

    def test_review_button_is_admin_only_and_never_grants(self):
        self.ns["callback"](456, "pioneer_review|1")
        self.assertIn("Admin sahaja", self.bot.messages[-1][1])
        self.ns["callback"](456, "admin_approve|1")
        self.assertIn("Admin sahaja", self.bot.messages[-1][1])
        self.grant_mock.assert_not_called()

    def test_lost_local_request_does_not_recreate_payment(self):
        self.ns["callback"](ADMIN, "pioneer_review|99")
        self.assertIn("tidak ditemui", self.bot.messages[-1][1])
        self.assertIn("Jangan", self.bot.messages[-1][1])
        self.assertIn("admin_panel", self.buttons())
        self.ns["callback"](ADMIN, "admin_approve|99")
        self.assertIn("tidak ditemui", self.bot.messages[-1][1])
        self.grant_mock.assert_not_called()

    def test_malformed_id_does_not_delegate_to_unsafe_legacy_handler(self):
        for data in ("admin_approve|x", "admin_approve|1|x", "admin_approve|0",
                     "admin_approve|1|201|extra", "pioneer_review|z"):
            self.ns["callback"](ADMIN, data)
            self.assertIn("tidak sah", self.bot.messages[-1][1])
        self.assertEqual(self.bot.marked, [])
        self.assertEqual(self.bot.delegated, [])

    def test_non_pioneer_payment_delegates_unchanged(self):
        self.bot.requests[1]["amount"] = 8.0
        self.assertEqual(self.ns["callback"](ADMIN, "admin_approve|1"), "old")
        self.assertIn(("callback", ADMIN, "admin_approve|1"), self.bot.delegated)
        self.grant_mock.assert_not_called()

    def test_approved_or_duplicate_request_cannot_regrant(self):
        self.bot.requests[1]["status"] = "approved"
        self.ns["callback"](ADMIN, "admin_approve|1|201")
        self.assertIn(("card", ADMIN, 1), self.bot.delegated)
        self.assertEqual(self.bot.marked, [])
        self.grant_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
