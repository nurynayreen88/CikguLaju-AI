"""Paid access eligibility is independent from the free-trial debit."""
import unittest
from datetime import date
from web.rph_delivery_quota import has_active_paid_access


class PaidAccessTests(unittest.TestCase):
    def test_lifetime_access(self):
        self.assertTrue(has_active_paid_access({"authenticated": True, "rakan_pembangun": True}))

    def test_active_and_expired_subscription(self):
        self.assertTrue(has_active_paid_access({"authenticated": True, "vip_until": "2027-12-31"}, date(2026, 11, 2)))
        self.assertFalse(has_active_paid_access({"authenticated": True, "vip_until": "2026-11-01"}, date(2026, 11, 2)))

    def test_missing_or_untrusted_access(self):
        for account in ({}, {"authenticated": False, "rakan_pembangun": True},
                        {"authenticated": True, "vip_until": "not-a-date"},
                        {"authenticated": True, "free_remaining": 10}):
            with self.subTest(account=account):
                self.assertFalse(has_active_paid_access(account, date(2026, 11, 2)))


if __name__ == "__main__":
    unittest.main()
