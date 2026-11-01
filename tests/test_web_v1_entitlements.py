import unittest
from datetime import date
from web_v1_entitlements import display_access, display_trusted_account


class AccountStatusTests(unittest.TestCase):
    def test_unknown_balance_not_invented(self):
        self.assertEqual(display_access(today=date(2026, 11, 1)),
                         {"status": "Percuma", "access": "Baki janaan belum tersedia"})

    def test_unlinked_account(self):
        self.assertEqual(display_trusted_account({"authenticated": False}),
                         {"status": "Belum disambungkan", "access": "Sambungkan akaun Telegram"})

    def test_trusted_snapshot_vip(self):
        result = display_trusted_account({"authenticated": True, "vip_until": "2027-12-31",
                                          "free_remaining": 5}, today=date(2026, 11, 1))
        self.assertEqual(result, {"status": "VIP", "access": "Tanpa had sehingga 31/12/2027"})

    def test_trusted_snapshot_free(self):
        result = display_trusted_account({"authenticated": True, "free_remaining": 8},
                                         today=date(2026, 11, 1))
        self.assertEqual(result["access"], "8/10 janaan percuma berbaki")

    def test_free_credits(self):
        self.assertEqual(display_access(free_remaining=7, today=date(2026, 11, 1)),
                         {"status": "Percuma", "access": "7/10 janaan percuma berbaki"})

    def test_lifetime_precedes_vip(self):
        self.assertEqual(display_access(rakan_pembangun=True, vip_until=date(2027, 1, 1),
                                        free_remaining=4, today=date(2026, 11, 1)),
                         {"status": "Rakan Pembangun", "access": "Tanpa had seumur hidup"})

    def test_active_vip_hides_trial(self):
        result = display_access(vip_until=date(2027, 1, 1), free_remaining=3,
                                today=date(2026, 11, 1))
        self.assertEqual(result["status"], "VIP")
        self.assertNotIn("/10", result["access"])

    def test_expired_vip_reverts_to_free(self):
        result = display_access(vip_until=date(2026, 10, 31), free_remaining=3,
                                today=date(2026, 11, 1))
        self.assertEqual(result["status"], "Percuma")

    def test_expiry_day_is_inclusive(self):
        result = display_access(vip_until=date(2026, 11, 1), today=date(2026, 11, 1))
        self.assertEqual(result["status"], "VIP")


if __name__ == "__main__":
    unittest.main()
