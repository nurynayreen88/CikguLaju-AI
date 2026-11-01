"""Telegram Login Widget signature tests; no live bot credentials."""
import hashlib
import hmac
import unittest

from web_v1_telegram_login import verify_telegram_login


BOT_TOKEN = "123456:test-only-not-a-real-bot-token"


def signed_payload(**fields):
    fields = {k: str(v) for k, v in fields.items()}
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    fields["hash"] = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    return fields


class TelegramLoginSignatureTests(unittest.TestCase):
    def test_signed_existing_user(self):
        payload = signed_payload(id=12345, auth_date=1000, first_name="Teacher")
        self.assertEqual(verify_telegram_login(payload, BOT_TOKEN, now=1001), 12345)

    def test_real_widget_numeric_id_and_auth_date(self):
        payload = signed_payload(id=12345, auth_date=1000, first_name="Teacher")
        payload["id"] = 12345
        payload["auth_date"] = 1000
        self.assertEqual(verify_telegram_login(payload, BOT_TOKEN, now=1001), 12345)

    def test_boolean_numeric_fields_rejected(self):
        payload = signed_payload(id=12345, auth_date=1000)
        payload["id"] = True
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=1001))

    def test_changed_user_id_rejected(self):
        payload = signed_payload(id=12345, auth_date=1000)
        payload["id"] = "99999"
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=1001))

    def test_stale_and_future_payloads_rejected(self):
        payload = signed_payload(id=12345, auth_date=1000)
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=90000))
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=999))

    def test_noncanonical_numeric_id_rejected_even_when_signed(self):
        payload = signed_payload(id="00012345", auth_date=1000)
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=1001))

    def test_noncanonical_timestamp_rejected_even_when_signed(self):
        payload = signed_payload(id=12345, auth_date="01000")
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=1001))

    def test_untrusted_payload_type_rejected(self):
        payload = signed_payload(id=12345, auth_date=1000)
        payload["photo_url"] = ["unexpected", "list"]
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=1001))

    def test_oversized_field_rejected(self):
        payload = signed_payload(id=12345, auth_date=1000, first_name="X" * 4097)
        self.assertIsNone(verify_telegram_login(payload, BOT_TOKEN, now=1001))


if __name__ == "__main__":
    unittest.main()
