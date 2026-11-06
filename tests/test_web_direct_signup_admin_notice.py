"""Trusted Telegram admin notification for direct Web signup."""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from flask import Flask
from web.telegram_web_direct_signup_admin_notice import create_web_direct_signup_admin_notice


class DirectWebNoticeTests(unittest.TestCase):
    def setup_app(self, *, registered=True, claimed=True):
        runtime = Mock()
        runtime.ADMIN_CHAT_ID = "123456789"
        runtime._is_admin.side_effect = lambda x: str(x) == "123456789"
        runtime.send.return_value.ok = True
        runtime.send.return_value.json.return_value = {"ok": True}
        now = datetime.now(timezone.utc).isoformat()
        def sb(method, path, **kwargs):
            if method == "GET" and path.startswith("web_direct_signups?"):
                return [{"telegram_user_id": 234567890, "created_at": now, "notified_at": None}] if registered else []
            if method == "GET" and path.startswith("cikgulaju_users?"):
                return [{"telegram_user_id": 234567890, "created_at": now,
                         "trial_remaining": 10, "first_name": "Cikgu", "last_name": "Baharu",
                         "username": "cikgu_web"}]
            if method == "PATCH" and path.startswith("web_direct_signups?"):
                return [{"telegram_user_id": 234567890}] if claimed else []
            if method == "GET" and path.startswith("referral_signups?"):
                return []
            raise AssertionError((method,path))
        runtime._sb_request.side_effect = sb
        app = Flask(__name__)
        app.register_blueprint(create_web_direct_signup_admin_notice(runtime))
        return app.test_client(), runtime

    def post(self, client, auth=True):
        headers = {"Authorization": "Bearer " + "a"*40} if auth else {}
        return client.post("/internal/web-signup/v1/admin-notify", json={
            "telegram_user_id": 234567890}, headers=headers)

    @patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": "a"*40})
    def test_new_verified_account_notifies_admin(self):
        client, runtime = self.setup_app()
        result = self.post(client)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json["notified"])
        runtime.send.assert_called_once()
        self.assertIn("Web", runtime.send.call_args.args[1])

    @patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": "a"*40})
    def test_missing_auth_never_sends(self):
        client, runtime = self.setup_app()
        self.assertEqual(self.post(client, auth=False).status_code, 401)
        runtime.send.assert_not_called()

    @patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": "a"*40})
    def test_existing_or_unmarked_account_never_sends(self):
        client, runtime = self.setup_app(registered=False)
        self.assertEqual(self.post(client).status_code, 409)
        runtime.send.assert_not_called()

    @patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": "a"*40})
    def test_duplicate_claim_never_sends(self):
        client, runtime = self.setup_app(claimed=False)
        self.assertEqual(self.post(client).status_code, 200)
        self.assertFalse(self.post(client).json["notified"])
        runtime.send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
