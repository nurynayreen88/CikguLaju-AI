"""Exact paid entitlement expiry tests, without external backend access."""
from datetime import datetime, timedelta, timezone
import unittest
from web.rph_delivery_quota import has_active_paid_access, authorize_rendered_document


class ExactExpiryTests(unittest.TestCase):
    def setUp(self):
        self.account = {"authenticated": True, "telegram_user_id": 42,
                        "rakan_pembangun": False, "free_remaining": 0,
                        "vip_until": datetime.now(timezone.utc).date().isoformat()}

    def test_expired_earlier_today_is_not_paid(self):
        self.account["vip_expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
        self.assertFalse(has_active_paid_access(self.account))
        result = authorize_rendered_document(self.account, 42, b"document", "url", "key")
        self.assertFalse(result["allowed"])

    def test_active_until_future_minute(self):
        self.account["vip_expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        self.assertTrue(has_active_paid_access(self.account))
        result = authorize_rendered_document(self.account, 42, b"document", "url", "key")
        self.assertTrue(result["allowed"])

    def test_timezone_missing_is_rejected(self):
        self.account["vip_expires_at"] = "2026-11-02T23:59:00"
        with self.assertRaises(ValueError):
            authorize_rendered_document(self.account, 42, b"document", "url", "key")

    def test_bad_exact_timestamp_is_rejected(self):
        self.account["vip_expires_at"] = "tomorrow"
        with self.assertRaises(ValueError):
            authorize_rendered_document(self.account, 42, b"document", "url", "key")


if __name__ == "__main__":
    unittest.main()
