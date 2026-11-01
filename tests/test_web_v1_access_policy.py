import unittest
from datetime import date

from web_v1_access_policy import can_use_feature


class AccessPolicyTests(unittest.TestCase):
    def test_unlinked_account_is_denied(self):
        self.assertFalse(can_use_feature({"authenticated": False, "rakan_pembangun": True}, "rpt"))

    def test_free_user_cannot_use_paid_modules(self):
        account = {"authenticated": True, "free_remaining": 10}
        self.assertFalse(can_use_feature(account, "rpt"))
        self.assertFalse(can_use_feature(account, "timetable_ai"))
        self.assertTrue(can_use_feature(account, "generate"))

    def test_exhausted_free_user_cannot_generate(self):
        self.assertFalse(can_use_feature({"authenticated": True, "free_remaining": 0}, "generate"))

    def test_unknown_free_balance_is_denied(self):
        self.assertFalse(can_use_feature({"authenticated": True}, "generate"))

    def test_lifetime_can_use_paid_modules(self):
        account = {"authenticated": True, "rakan_pembangun": True, "free_remaining": 0}
        self.assertTrue(can_use_feature(account, "rpt"))
        self.assertTrue(can_use_feature(account, "timetable_ai"))

    def test_expired_vip_reverts_to_free_access(self):
        account = {"authenticated": True, "vip_until": "2026-10-31", "free_remaining": 2}
        self.assertFalse(can_use_feature(account, "rpt", today=date(2026, 11, 1)))
        self.assertTrue(can_use_feature(account, "generate", today=date(2026, 11, 1)))

    def test_malformed_entitlement_is_denied(self):
        account = {"authenticated": True, "rakan_pembangun": "yes", "free_remaining": 10}
        self.assertFalse(can_use_feature(account, "generate"))

    def test_unknown_feature_is_denied(self):
        self.assertFalse(can_use_feature({"authenticated": True, "rakan_pembangun": True}, "admin"))


if __name__ == "__main__":
    unittest.main()
