"""One Telegram main-menu message, with the existing RPH entry points intact."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web import web_link_telegram


class Response:
    def __init__(self, rows):
        self.rows = rows
        self.ok = True

    def json(self):
        return {
            "ok": True,
            "result": {
                "message_id": 27,
                "reply_markup": {"inline_keyboard": self.rows},
            },
        }


class EditResponse:
    ok = True

    def json(self):
        return {"ok": True}


class SingleMenuTests(unittest.TestCase):
    def make_runtime(self, rows, active=True):
        sent = []
        old_menu_calls = []
        def original_menu(cid, show_persistent=False):
            old_menu_calls.append((cid, show_persistent))
            return Response(rows)
        rt = SimpleNamespace(
            API="https://api.telegram.invalid/bot-example",
            menu=original_menu,
            send=lambda *args: sent.append(args),
            CIKGULAJU_DAILY_MANUAL_ONLY_20261110=active,
        )
        self.assertTrue(web_link_telegram.install(rt))
        return rt, sent, old_menu_calls

    def updated_rows(self, rt):
        with patch.object(web_link_telegram.requests, "post",
                          return_value=EditResponse()) as post:
            rt.menu(321, show_persistent=True)
            self.assertEqual(post.call_count, 1)
            self.assertEqual(post.call_args.kwargs["json"]["chat_id"], 321)
            self.assertEqual(post.call_args.kwargs["json"]["message_id"], 27)
            return post.call_args.kwargs["json"]["reply_markup"]["inline_keyboard"]

    def test_today_is_inside_original_menu_without_second_message(self):
        original = [
            [{"text": "📚 Sediakan RPH", "callback_data": "quick"}],
            [{"text": "🧑‍🏫 Profil Saya", "callback_data": "account"}],
            [{"text": "🎁 Referral Saya", "callback_data": "private_referral_home"}],
            [{"text": "📘 RPT 2027", "callback_data": "rpt2027_home"}],
        ]
        rt, sent, called = self.make_runtime(original)
        rows = self.updated_rows(rt)
        callbacks = [b.get("callback_data") for row in rows for b in row]
        self.assertEqual(callbacks.count("todayrph272"), 1)
        self.assertEqual(callbacks.count("quick"), 1)
        self.assertNotIn("ak26:home", callbacks)  # only within Sediakan RPH
        self.assertLess(callbacks.index("quick"), callbacks.index("todayrph272"))
        self.assertEqual(callbacks.index("todayrph272"), callbacks.index("quick") + 1)
        for callback in ("account", "private_referral_home", "rpt2027_home"):
            self.assertIn(callback, callbacks)
        self.assertTrue(any(b.get("url") == web_link_telegram.WEB_URL
                            for row in rows for b in row))
        self.assertEqual(sent, [])
        self.assertEqual(called, [(321, True)])

    def test_existing_main_menu_web_button_gets_clearer_label_without_duplicate(self):
        original = [
            [{"text": "📚 Sediakan RPH", "callback_data": "quick"}],
            [{"text": "🌐 BUKA CIKGULAJU WEB", "url": web_link_telegram.WEB_URL}],
            [{"text": "👤 Profil Saya", "callback_data": "account"}],
        ]
        rt, sent, called = self.make_runtime(original, active=False)
        rows = self.updated_rows(rt)
        links = [b for row in rows for b in row
                 if b.get("url") == web_link_telegram.WEB_URL]
        self.assertEqual(links, [web_link_telegram.BUTTON])
        self.assertEqual(sent, [])
        self.assertEqual(called, [(321, True)])
        self.assertEqual(sum(1 for row in rows for b in row
                             if b.get("callback_data") == "quick"), 1)

    def test_no_duplicate_if_buttons_already_exist(self):
        original = [
            [{"text": "📚 Sediakan RPH", "callback_data": "quick"}],
            [dict(web_link_telegram.TODAY_BUTTON)],
            [dict(web_link_telegram.BUTTON)],
        ]
        rt, sent, called = self.make_runtime(original)
        with patch.object(web_link_telegram.requests, "post") as post:
            rt.menu(321)
            post.assert_not_called()
        self.assertEqual(sent, [])
        self.assertEqual(called, [(321, False)])

    def test_manual_and_member_referral_survive_later_markup_edit(self):
        original = [
            [{"text": "📚 Sediakan RPH", "callback_data": "quick"}],
            [{"text": "🧑‍🏫 Profil Saya", "callback_data": "account"}],
        ]
        rt, sent, _ = self.make_runtime(original)
        rt.CIKGULAJU_MANUAL_PENGGUNA_INSTALLED = True
        rt._private_referral_member = lambda cid: {"enabled": True}
        rows = self.updated_rows(rt)
        callbacks = [b.get("callback_data") for row in rows for b in row]
        self.assertEqual(callbacks.count("manual_pengguna_pdf"), 1)
        self.assertEqual(callbacks.count("private_referral_home"), 1)
        self.assertEqual(callbacks.count("todayrph272"), 1)
        self.assertEqual(sent, [])

    def test_no_private_referral_for_unapproved_user(self):
        original = [[{"text": "Profil Saya", "callback_data": "account"}]]
        rt, sent, _ = self.make_runtime(original)
        rt._private_referral_member = lambda cid: {"enabled": False}
        rows = self.updated_rows(rt)
        callbacks = [b.get("callback_data") for row in rows for b in row]
        self.assertNotIn("private_referral_home", callbacks)
        self.assertEqual(sent, [])

    def test_daily_button_hidden_if_feature_did_not_install(self):
        original = [
            [{"text": "📚 Sediakan RPH", "callback_data": "quick"}],
            [{"text": "Profil Saya", "callback_data": "account"}],
        ]
        rt, sent, _ = self.make_runtime(original, active=False)
        rows = self.updated_rows(rt)
        self.assertFalse(any(b.get("callback_data") == "todayrph272"
                             for row in rows for b in row))
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
