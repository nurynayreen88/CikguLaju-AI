"""Isolated end-to-end auth contract test with an in-memory account lookup.

No real Telegram token, user account, database or production session is used.
"""
import hashlib
import hmac
import unittest
from datetime import date

from web_v1_entitlements import display_trusted_account
from web_v1_sessions import issue_session_ticket, verify_session_ticket
from web_v1_telegram_login import verify_telegram_login

TOKEN = "test:telegram-token"
SESSION_SECRET = "test-only-session-secret-with-at-least-32-chars"
NOW = 1800000000


def login_payload(user_id):
    data = {"id": str(user_id), "auth_date": str(NOW), "first_name": "Test Teacher"}
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    key = hashlib.sha256(TOKEN.encode()).digest()
    data["hash"] = hmac.new(key, check.encode(), hashlib.sha256).hexdigest()
    return data


class SharedAccountFlowTests(unittest.TestCase):
    def test_verified_login_session_and_lifetime_status(self):
        existing_accounts = {123: {"authenticated": True, "rakan_pembangun": True,
                                   "free_remaining": 4}}
        user_id = verify_telegram_login(login_payload(123), TOKEN, now=NOW)
        self.assertEqual(user_id, 123)
        self.assertIn(user_id, existing_accounts)
        ticket = issue_session_ticket(user_id, SESSION_SECRET, now=NOW)
        resolved_id = verify_session_ticket(ticket, SESSION_SECRET, now=NOW + 10)
        status = display_trusted_account(existing_accounts[resolved_id], today=date(2026, 11, 1))
        self.assertEqual(status["status"], "Rakan Pembangun")
        self.assertNotIn("/10", status["access"])

    def test_verified_but_unknown_account_is_not_created(self):
        existing_accounts = {123: {"authenticated": True, "free_remaining": 2}}
        user_id = verify_telegram_login(login_payload(999), TOKEN, now=NOW)
        self.assertNotIn(user_id, existing_accounts)
        self.assertEqual(len(existing_accounts), 1)

    def test_tampered_login_cannot_create_session(self):
        data = login_payload(123)
        data["id"] = "999"
        self.assertIsNone(verify_telegram_login(data, TOKEN, now=NOW))


if __name__ == "__main__":
    unittest.main()
