"""Offline Telegram Login Widget signature verification tests."""
import hashlib
import hmac
import unittest
from web_v1_telegram_auth import TelegramLoginError, verify_telegram_login

TOKEN = "123456:unit-test-only"
NOW = 1800000000


def signed(**fields):
    values = {"id": "1234567", "auth_date": str(NOW), "first_name": "Teacher", **fields}
    check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hashlib.sha256(TOKEN.encode()).digest()
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return values


class TelegramAuthTests(unittest.TestCase):
    def test_valid_signature(self):
        identity = verify_telegram_login(signed(), TOKEN, now=NOW)
        self.assertEqual(identity["telegram_user_id"], 1234567)

    def test_tampered_identity_rejected(self):
        data = signed()
        data["id"] = "7654321"
        with self.assertRaises(TelegramLoginError):
            verify_telegram_login(data, TOKEN, now=NOW)

    def test_expired_rejected(self):
        with self.assertRaises(TelegramLoginError):
            verify_telegram_login(signed(), TOKEN, now=NOW + 301)

    def test_future_rejected(self):
        with self.assertRaises(TelegramLoginError):
            verify_telegram_login(signed(auth_date=str(NOW + 60)), TOKEN, now=NOW)

    def test_wrong_token_rejected(self):
        with self.assertRaises(TelegramLoginError):
            verify_telegram_login(signed(), "wrong-token", now=NOW)

    def test_malformed_fields_rejected(self):
        for data in ({}, signed(id="not-a-number"), {**signed(), "hash": "bad"}):
            with self.assertRaises(TelegramLoginError):
                verify_telegram_login(data, TOKEN, now=NOW)


if __name__ == "__main__":
    unittest.main()
