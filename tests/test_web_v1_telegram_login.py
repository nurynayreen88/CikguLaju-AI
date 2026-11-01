import hashlib
import hmac
import unittest

from web_v1_telegram_login import verify_telegram_login


def signed_payload(token="test:token", auth_date="1800000000", user_id="12345"):
    payload = {"id": user_id, "first_name": "Teacher", "auth_date": auth_date}
    check = "\n".join(f"{k}={v}" for k, v in sorted(payload.items()))
    secret = hashlib.sha256(token.encode()).digest()
    payload["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return payload


class TelegramLoginVerifierTests(unittest.TestCase):
    def test_valid_signature(self):
        self.assertEqual(verify_telegram_login(signed_payload(), "test:token", now=1800000001), 12345)

    def test_tampered_identity(self):
        payload = signed_payload()
        payload["id"] = "99999"
        self.assertIsNone(verify_telegram_login(payload, "test:token", now=1800000001))

    def test_wrong_bot_token(self):
        self.assertIsNone(verify_telegram_login(signed_payload(), "wrong", now=1800000001))

    def test_expired_login(self):
        self.assertIsNone(verify_telegram_login(signed_payload(), "test:token", now=1800100000))

    def test_future_login(self):
        self.assertIsNone(verify_telegram_login(signed_payload(), "test:token", now=1799999999))

    def test_invalid_user_id(self):
        self.assertIsNone(verify_telegram_login(signed_payload(user_id="not-a-number"), "test:token", now=1800000001))

    def test_newline_injection(self):
        payload = signed_payload()
        payload["first_name"] = "Teacher\nadmin=true"
        self.assertIsNone(verify_telegram_login(payload, "test:token", now=1800000001))


if __name__ == "__main__":
    unittest.main()
