"""Regression checks for the trusted Web -> Telegram new referral notice."""
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
from flask import Flask
from web.telegram_web_referral_admin_notice import create_web_referral_signup_notice


class SignupNoticeTests(unittest.TestCase):
    def make_client(self):
        runtime = Mock()
        runtime.ADMIN_CHAT_ID = "123456789"
        runtime._is_admin.side_effect = lambda x: str(x) == "123456789"
        runtime.send.return_value = Mock(ok=True)
        runtime.send.return_value.json.return_value = {"ok": True}
        uid = 234567890
        stamp = datetime.now(timezone.utc).isoformat()
        def sb(method, path, **kwargs):
            if method == "GET" and path.startswith("cikgulaju_users?"):
                return [{"telegram_user_id":uid, "first_name":"Cikgu", "last_name":"Baru",
                         "username":"cikgubaru", "created_at":stamp, "trial_remaining":10}]
            if method == "GET" and path.startswith("referral_signups?"):
                return [{"referrer_user_id":345678901, "captured_at":stamp}]
            if method == "POST" and path == "web_referral_signup_notices":
                return [{"referred_user_id":uid}]
            raise AssertionError((method,path))
        runtime._sb_request.side_effect = sb
        app = Flask(__name__)
        app.register_blueprint(create_web_referral_signup_notice(runtime))
        return app.test_client(), runtime, uid

    def test_unauthorized_request_fails_closed(self):
        client, runtime, uid = self.make_client()
        response = client.post("/internal/referral/v1/new-web-signup-notify",
                               json={"telegram_user_id":uid})
        self.assertEqual(response.status_code,401)
        runtime.send.assert_not_called()

    def test_authenticated_recent_referral_sends_one_admin_notice(self):
        from unittest.mock import patch
        client, runtime, uid = self.make_client()
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*40}):
            response = client.post("/internal/referral/v1/new-web-signup-notify",
                                   headers={"Authorization":"Bearer "+"x"*40},
                                   json={"telegram_user_id":uid})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json["notified"])
        runtime.send.assert_called_once()
        self.assertEqual(str(runtime.send.call_args.args[0]),"123456789")


if __name__=="__main__":
    unittest.main()
