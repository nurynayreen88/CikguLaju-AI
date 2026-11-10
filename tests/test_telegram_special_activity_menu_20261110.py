"""Safe, no-network regression tests for Telegram Special Activity RPH parity."""
import types
import unittest
from unittest.mock import patch

from web import telegram_special_activity_menu as mod


class FakeResponse:
    def __init__(self, ok=True):
        self.ok = ok

    def json(self):
        return {"ok": self.ok, "result": {"message_id": 1234}}


class FakeRuntime:
    def __init__(self):
        self.state = {}
        self.messages = []
        self.deliveries = []
        self.debits = []
        self.gates = []
        self.delivery_ok = True
        self.menu_calls = 0
        self.fallback_calls = []

    def send(self, cid, text, kb=None, parse_html=True, reply_keyboard=None):
        self.messages.append((cid, text, kb))
        return FakeResponse()

    def send_document(self, cid, path, caption=""):
        with open(path, "rb") as fp:
            content = fp.read()
        self.deliveries.append((cid, str(path), caption, content))
        return FakeResponse(self.delivery_ok)

    def menu(self, cid, show_persistent=False):
        self.menu_calls += 1
        return FakeResponse()

    def callback(self, cid, data):
        self.fallback_calls.append((cid, data))
        return "original callback"

    def _credit_gate(self, cid, state):
        self.gates.append((cid, state.get("task")))
        self.state.setdefault(cid, {})["_free_generation_pending_v25282"] = True
        return True

    def _consume_free_after_success_v25282(self, cid, reason):
        pending = self.state.setdefault(cid, {}).pop("_free_generation_pending_v25282", False)
        if pending:
            self.debits.append((cid, reason))

    def _telegram_delivery_ok_v25279(self, response):
        return response.ok

    def _profile_class_records(self, cid):
        return [{"name": "1 Bestari", "students": 32}]


class SpecialParityTests(unittest.TestCase):
    def setUp(self):
        self.runtime = FakeRuntime()
        self.assertTrue(mod.install(self.runtime))
        self.cid = 91001

    def test_menu_adds_only_one_visible_entry_per_call_and_preserves_old_callback(self):
        response = self.runtime.menu(self.cid)
        self.assertTrue(response.ok)
        self.assertEqual(self.runtime.menu_calls, 1)
        self.assertEqual(self.runtime.messages, [])
        self.runtime.callback(self.cid, "ak26:home")
        self.assertIn("RPH Aktiviti Khas", self.runtime.messages[-1][1])
        self.assertEqual(self.runtime.callback(self.cid, "quick"), "original callback")
        self.assertEqual(self.runtime.fallback_calls, [(self.cid, "quick")])
        self.assertTrue(mod.install(self.runtime))  # idempotent

    def _choose_transition(self):
        self.runtime.callback(self.cid, "ak26:home")
        self.runtime.callback(self.cid, "ak26:t")
        self.runtime.callback(self.cid, "ak26:tf:0")
        ss = self.runtime.state[self.cid]["_aktiviti_khas_20261110"]
        self.assertEqual(ss["kind"], mod.TRANSISI)
        self.assertEqual(ss["year"], 1)
        self.assertEqual(len(ss["options"]), 10)
        self.assertFalse(self.runtime.gates)
        self.runtime.callback(self.cid, "ak26:a:" + ss["options"][0])
        self.runtime.callback(self.cid, "ak26:c:0")
        self.runtime.callback(self.cid, "ak26:d:x")
        return ss

    def test_transition_word_then_pdf_uses_only_one_free_credit(self):
        ss = self._choose_transition()
        self.assertEqual(ss["class"], "1 Bestari")
        self.assertEqual(ss["students"], "32")
        self.assertEqual(ss["date"], "")
        self.assertEqual(len(self.runtime.debits), 0)
        with patch.object(mod.engine, "render", side_effect=lambda row, year, teacher, fmt, **kwargs:
                          (b"PK" if fmt == "word" else b"%PDF-") + b"t" * 1000):
            self.runtime.callback(self.cid, "ak26:w")
            self.runtime.callback(self.cid, "ak26:f")
            # Repeating the first download is not a new generation.
            self.runtime.callback(self.cid, "ak26:w")
        self.assertEqual(len(self.runtime.gates), 1)
        self.assertEqual(len(self.runtime.debits), 1)
        self.assertEqual(len(self.runtime.deliveries), 3)
        self.assertTrue(all("DRAF" in doc[2] for doc in self.runtime.deliveries))
        self.assertFalse(self.runtime.state[self.cid].get("_free_generation_pending_v25282", False))

    def test_failed_send_never_consumes_credit_and_allows_retry(self):
        self._choose_transition()
        self.runtime.delivery_ok = False
        with patch.object(mod.engine, "render", return_value=b"PK" + b"x" * 1000):
            self.runtime.callback(self.cid, "ak26:w")
            self.assertEqual(len(self.runtime.debits), 0)
            self.assertFalse(self.runtime.state[self.cid].get("_free_generation_pending_v25282", False))
            self.runtime.delivery_ok = True
            self.runtime.callback(self.cid, "ak26:w")
        self.assertEqual(len(self.runtime.debits), 1)
        self.assertEqual(len(self.runtime.gates), 2)

    def test_invalid_document_not_delivered_or_debited(self):
        self._choose_transition()
        with patch.object(mod.engine, "render", return_value=b"CORRUPT"):
            self.runtime.callback(self.cid, "ak26:w")
        self.assertEqual(self.runtime.debits, [])
        self.assertEqual(self.runtime.deliveries, [])
        self.assertFalse(self.runtime.state[self.cid].get("_free_generation_pending_v25282", False))

    def test_post_syllabus_options_and_back_navigation(self):
        self.runtime.callback(self.cid, "ak26:p")
        self.runtime.callback(self.cid, "ak26:py:6")
        self.runtime.callback(self.cid, "ak26:ps:2")  # Matematik
        ss = self.runtime.state[self.cid]["_aktiviti_khas_20261110"]
        self.assertEqual(ss["subject"], "Matematik")
        self.assertEqual(len(ss["options"]), 1)
        self.runtime.callback(self.cid, "ak26:a:" + ss["options"][0])
        self.assertEqual(mod._validated_activity(self.runtime, self.cid)[0]["subject"], "Matematik")
        self.runtime.callback(self.cid, "ak26:back")
        self.assertEqual(self.runtime.debits, [])
        self.assertEqual(self.runtime.deliveries, [])

    def test_old_selection_does_not_bypass_catalogue_digest(self):
        ss = self._choose_transition()
        ss["digest"] = "0" * 64
        self.runtime.callback(self.cid, "ak26:w")
        self.assertEqual(self.runtime.gates, [])
        self.assertEqual(self.runtime.debits, [])
        self.assertEqual(self.runtime.deliveries, [])

    def test_install_fails_closed_without_generation_gate(self):
        broken = FakeRuntime()
        broken._credit_gate = None
        self.assertFalse(mod.install(broken))
        self.assertFalse(hasattr(broken, "CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE"))


if __name__ == "__main__":
    unittest.main()
