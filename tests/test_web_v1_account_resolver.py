import unittest
from datetime import date

from web_v1_account_resolver import resolve_account, resolve_feature_access
from web_v1_sessions import issue_session_ticket

SECRET = "test-only-session-secret-with-at-least-32-chars"
NOW = 1800000000


class AccountResolverTests(unittest.TestCase):
    def setUp(self):
        self.ticket = issue_session_ticket(123, SECRET, now=NOW)

    def test_existing_matching_account(self):
        account = {"authenticated": True, "telegram_user_id": 123, "free_remaining": 3}
        self.assertEqual(resolve_account(self.ticket, SECRET, lambda uid: account, now=NOW), account)

    def test_wrong_account_id_rejected(self):
        account = {"authenticated": True, "telegram_user_id": 999, "rakan_pembangun": True}
        self.assertIsNone(resolve_account(self.ticket, SECRET, lambda uid: account, now=NOW))

    def test_missing_account_rejected(self):
        self.assertIsNone(resolve_account(self.ticket, SECRET, lambda uid: None, now=NOW))

    def test_lookup_failure_is_closed(self):
        def failing_lookup(uid):
            raise RuntimeError("DB unavailable")
        self.assertIsNone(resolve_account(self.ticket, SECRET, failing_lookup, now=NOW))

    def test_expired_session_cannot_resolve(self):
        called = []
        self.assertIsNone(resolve_account(self.ticket, SECRET, lambda uid: called.append(uid), now=NOW + 50000))
        self.assertEqual(called, [])

    def test_free_account_cannot_access_rpt(self):
        account = {"authenticated": True, "telegram_user_id": 123, "free_remaining": 10}
        self.assertFalse(resolve_feature_access(self.ticket, SECRET, lambda uid: account,
                                                "rpt", now=NOW, today=date(2026, 11, 1)))

    def test_lifetime_account_can_access_rpt(self):
        account = {"authenticated": True, "telegram_user_id": 123, "rakan_pembangun": True}
        self.assertTrue(resolve_feature_access(self.ticket, SECRET, lambda uid: account,
                                               "rpt", now=NOW, today=date(2026, 11, 1)))


if __name__ == "__main__":
    unittest.main()
