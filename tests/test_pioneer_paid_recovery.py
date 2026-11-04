"""Admin recovery when SQLite pending payments were lost; no live payment calls."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pioneer_paid_recovery_telegram as recovery


class FakeApp:
    def __init__(self):
        self.view_functions = {"webhook": lambda: "original-webhook"}


class FakeRequest:
    def __init__(self):
        self.headers = {"X-Telegram-Bot-Api-Secret-Token": "0123456789abcdefghij"}
        self.update = {}

    def get_json(self, silent=True):
        return self.update


class FakeRuntime:
    def __init__(self):
        self.app = FakeApp()
        self.request = FakeRequest()
        self.state = {}
        self.messages = []
        self.members = {201, 202}
        self.entitlements = {}
        self.grants = []
        self.calls = []
        self.delegated = []

    def send(self, cid, message, keyboard=None):
        self.messages.append((cid, message, keyboard or []))
        return True

    def callback(self, cid, d):
        self.delegated.append((cid, d))
        return "old-callback"

    def card(self, cid, uid):
        self.messages.append((cid, "Existing user card", []))
        return True

    def db(self, method, path, **kwargs):
        self.calls.append((method, path))
        if method == "GET" and path.startswith("cikgulaju_users?"):
            uid = int(path.split("eq.", 1)[1].split("&", 1)[0])
            return [{"telegram_user_id": uid}] if uid in self.members else []
        if method == "GET" and path.startswith("pioneer_entitlements?"):
            if "telegram_user_id=eq." in path:
                uid = int(path.split("eq.", 1)[1].split("&", 1)[0])
                ref = self.entitlements.get(uid)
                return [{"entitlement": "PIONEER_LIFETIME"}] if ref else []
            if "payment_reference=eq." in path:
                # For this fake, payment refs are percent-encoded and contain colon.
                from urllib.parse import unquote
                ref = unquote(path.split("eq.", 1)[1].split("&", 1)[0])
                return [{"telegram_user_id": uid} for uid, other in self.entitlements.items()
                        if ref == other]
            raise AssertionError("Unexpected pioneer lookup")
        if method == "POST" and path == "rpc/approve_pioneer_early_bird":
            p = kwargs["json"]
            uid, ref, admin = (p["p_telegram_user_id"], p["p_payment_reference"],
                               p["p_approved_by"])
            if uid in self.entitlements or ref in self.entitlements.values():
                raise RuntimeError("duplicate payment or entitlement")
            self.entitlements[uid] = ref
            self.grants.append((uid, ref, admin))
            return {"approved": True}
        raise AssertionError("Unexpected database call")

    def ns(self):
        return {
            "app": self.app,
            "request": self.request,
            "jsonify": lambda payload: payload,
            "callback": self.callback,
            "_admin_user_card": self.card,
            "send": self.send,
            "_sb_request": self.db,
            "state": self.state,
            "_is_admin": lambda cid: int(cid) == 1,
        }

    def callbacks(self):
        return [b.get("callback_data") for row in self.messages[-1][2] for b in row]

    def input_ref(self, text="/tngref TNG202611040000123"):
        self.request.update = {"message": {
            "chat": {"id": 1, "type": "private"},
            "from": {"id": 1},
            "text": text,
        }}
        return self.app.view_functions["webhook"]()

    def begin(self, uid):
        self.ns_obj["_admin_user_card"](1, uid)
        self.ns_obj["callback"](1, "pioneer_paid_recover_ask|" + str(uid))

    def prepare(self, uid=201, reference="TNG202611040000123"):
        self.begin(uid)
        self.input_ref("/tngref " + reference)
        choices = self.callbacks()
        return next(x for x in choices if x.startswith("pioneer_paid_recover_confirm|"))


class PioneerPaidRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.p = patch.dict(os.environ, {
            "CIKGULAJU_TELEGRAM_WEBHOOK_SECRET": "0123456789abcdefghij",
        })
        self.p.start()
        self.addCleanup(self.p.stop)
        self.rt = FakeRuntime()
        self.rt.ns_obj = self.rt.ns()
        self.assertTrue(recovery.install(self.rt.ns_obj))

    def test_admin_can_open_recovery_from_inactive_user(self):
        self.rt.ns_obj["_admin_user_card"](1, 201)
        self.assertIn("pioneer_paid_recover_ask|201", self.rt.callbacks())
        self.assertEqual(self.rt.grants, [])
        self.assertTrue(recovery.install(self.rt.ns_obj))

    def test_admin_must_enter_merchant_ref_and_confirm_explicitly(self):
        button = self.rt.prepare()
        self.assertEqual(self.rt.grants, [])
        self.assertIn("201", self.rt.messages[-1][1])
        self.assertIn("Saya Sahkan Transaksi", self.rt.messages[-1][2][0][0]["text"])
        self.rt.ns_obj["callback"](1, button)
        self.assertEqual(len(self.rt.grants), 1)
        uid, ref, admin = self.rt.grants[0]
        self.assertEqual((uid, admin), (201, 1))
        self.assertTrue(ref.startswith("tng-merchant-recovery:"))
        self.assertNotIn("TNG202611040000123", ref)
        self.assertIn("AKTIF", self.rt.messages[-2][1])
        self.assertEqual(self.rt.messages[-1][0], 201)
        self.assertFalse(any("payment_requests" in path for _, path in self.rt.calls))

    def test_button_replay_and_missing_state_block_grant(self):
        button = self.rt.prepare()
        self.rt.ns_obj["callback"](1, button)
        self.rt.ns_obj["callback"](1, button)
        self.assertEqual(len(self.rt.grants), 1)
        self.assertIn("tamat", self.rt.messages[-1][1].lower())

    def test_non_admin_cannot_start_or_confirm(self):
        self.rt.ns_obj["callback"](201, "pioneer_paid_recover_ask|201")
        self.assertIn("Admin sahaja", self.rt.messages[-1][1])
        button = self.rt.prepare()
        self.rt.ns_obj["callback"](201, button)
        self.assertEqual(self.rt.grants, [])

    def test_expired_token_never_grants(self):
        button = self.rt.prepare()
        self.rt.state[1]["pioneer_paid_recovery"]["started"] -= 1000
        self.rt.ns_obj["callback"](1, button)
        self.assertEqual(self.rt.grants, [])

    def test_wrong_uid_bound_to_token_never_grants(self):
        button = self.rt.prepare()
        forged = button.replace("|201|", "|202|")
        self.rt.ns_obj["callback"](1, forged)
        self.assertEqual(self.rt.grants, [])

    def test_no_double_use_of_same_bank_transaction_across_users(self):
        first = self.rt.prepare(201, "TNG-20261104-0000123")
        self.rt.ns_obj["callback"](1, first)
        second = self.rt.prepare(202, "tng 20261104 0000123")
        self.rt.ns_obj["callback"](1, second)
        self.assertEqual(len(self.rt.grants), 1)
        self.assertNotIn(202, self.rt.entitlements)
        self.assertIn("telah digunakan", self.rt.messages[-1][1])

    def test_unregistered_user_cannot_be_approved(self):
        self.rt.ns_obj["callback"](1, "pioneer_paid_recover_ask|999")
        self.assertIn("tiada", self.rt.messages[-1][1])
        self.assertEqual(self.rt.grants, [])

    def test_existing_pioneer_prevents_second_grant(self):
        self.rt.entitlements[201] = "old-ref"
        self.rt.ns_obj["callback"](1, "pioneer_paid_recover_ask|201")
        self.assertIn("sudah", self.rt.messages[-1][1])
        self.assertEqual(self.rt.grants, [])

    def test_malformed_bank_ref_never_progresses(self):
        self.rt.begin(201)
        self.rt.input_ref("/tngref 00000000")
        self.assertIn("tidak sah", self.rt.messages[-1][1])
        self.assertEqual(self.rt.grants, [])

    def test_webhook_requires_secret_and_admin_private_chat(self):
        self.rt.begin(201)
        self.rt.request.headers["X-Telegram-Bot-Api-Secret-Token"] = "wrong"
        self.assertEqual(self.rt.input_ref(), "original-webhook")
        self.assertEqual(self.rt.state[1]["pioneer_paid_recovery"]["stage"], "await_ref")
        self.rt.request.headers["X-Telegram-Bot-Api-Secret-Token"] = "0123456789abcdefghij"
        self.rt.request.update["message"]["chat"]["type"] = "group"
        self.assertEqual(self.rt.app.view_functions["webhook"](), "original-webhook")
        self.assertEqual(self.rt.state[1]["pioneer_paid_recovery"]["stage"], "await_ref")

    def test_legacy_payment_approval_is_delegated_unchanged(self):
        self.assertEqual(self.rt.ns_obj["callback"](1, "admin_approve|1"), "old-callback")
        self.assertEqual(self.rt.delegated, [(1, "admin_approve|1")])

    def test_cancel_consumes_reference_without_approval(self):
        button = self.rt.prepare()
        self.rt.ns_obj["callback"](1, "pioneer_paid_recover_cancel|201")
        self.rt.ns_obj["callback"](1, button)
        self.assertEqual(self.rt.grants, [])

    def test_missing_webhook_secret_disables_all_recovery(self):
        rt = FakeRuntime()
        ns = rt.ns()
        with patch.dict(os.environ, {"CIKGULAJU_TELEGRAM_WEBHOOK_SECRET": ""}):
            self.assertFalse(recovery.install(ns))
        self.assertEqual(ns["callback"](1, "pioneer_paid_recover_ask|201"), "old-callback")
        ns["_admin_user_card"](1, 201)
        self.assertEqual(len(rt.messages), 1)


if __name__ == "__main__":
    unittest.main()
