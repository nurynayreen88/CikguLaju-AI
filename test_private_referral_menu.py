"""Offline, no Telegram or Supabase calls; validate invite-only menu buttons."""
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from web.private_referral_menu_runtime import install


class Response:
    ok = True

    def __init__(self, content):
        self._content = content

    def json(self):
        return self._content


class Runtime:
    API = "https://telegram.invalid/botTEST"

    def __init__(self, allowed=True):
        self.allowed = allowed
        self.sent = []
        self.keyboard = [
            [{"text": "📚 Bahan", "callback_data": "quick"}],
            [{"text": "👤 Profil", "callback_data": "account"}],
            [{"text": "🏆 Rakan Pembangun", "callback_data": "pioneer_join"}],
        ]

    def _private_referral_member(self, cid):
        return {"enabled": self.allowed, "referrer_user_id": cid}

    def menu(self, cid, show_persistent=False):
        self.sent.append((cid, "main", show_persistent))
        return Response({
            "ok": True,
            "result": {
                "message_id": 123,
                "reply_markup": {"inline_keyboard": self.keyboard},
            },
        })

    def send(self, cid, text, buttons=None):
        self.sent.append((cid, text, buttons))
        return Response({"ok": True})


class TestPrivateReferralMenu(unittest.TestCase):
    def test_unapproved_user_does_not_see_referral(self):
        runtime = Runtime(allowed=False)
        self.assertTrue(install(runtime))
        with patch("web.private_referral_menu_runtime.requests.post") as post:
            runtime.menu(101, show_persistent=True)
        self.assertEqual(len(runtime.sent), 1)
        post.assert_not_called()

    def test_approved_user_gets_share_entry_in_existing_menu(self):
        runtime = Runtime(allowed=True)
        self.assertTrue(install(runtime))
        with patch("web.private_referral_menu_runtime.requests.post") as post:
            post.return_value = Response({"ok": True})
            result = runtime.menu(101, show_persistent=True)
        self.assertTrue(result.json()["ok"])
        post.assert_called_once()
        kwargs = post.call_args.kwargs
        updated = kwargs["json"]["reply_markup"]["inline_keyboard"]
        ids = [button["callback_data"] for row in updated for button in row]
        self.assertEqual(ids, [
            "quick", "account", "private_referral_home", "pioneer_join",
        ])
        self.assertEqual(kwargs["json"]["message_id"], 123)
        self.assertEqual(len(runtime.sent), 1)
        self.assertEqual(len(runtime.keyboard), 3)  # original remains unchanged

    def test_revoked_user_loses_button_next_menu(self):
        runtime = Runtime(allowed=True)
        install(runtime)
        with patch("web.private_referral_menu_runtime.requests.post") as post:
            post.return_value = Response({"ok": True})
            runtime.menu(101)
            runtime.allowed = False
            runtime.menu(101)
        self.assertEqual(post.call_count, 1)

    def test_telegram_markup_edit_failure_preserves_original_menu(self):
        runtime = Runtime(allowed=True)
        install(runtime)
        with patch("web.private_referral_menu_runtime.requests.post") as post:
            post.return_value = Response({"ok": False})
            runtime.menu(101)
        self.assertEqual(runtime.sent[0][1], "main")
        self.assertEqual(runtime.sent[1][2][0][0]["callback_data"],
                         "private_referral_home")
        self.assertEqual(len(runtime.keyboard), 3)


if __name__ == "__main__":
    unittest.main()
