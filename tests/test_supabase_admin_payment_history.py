"""Unit tests for Supabase admin history reader (no live DB writes)."""
import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from supabase_admin_payment_history import fetch_admin_payment_history


class PaymentHistoryTests(unittest.TestCase):
    def test_combines_and_distinguishes_approvals(self):
        records = {
            "subscription_payments": [{"telegram_user_id": 11, "payment_reference": "sub1", "amount_rm": 8, "status": "paid", "created_at": "2026-10-31T10:00:00Z"}],
            "payments": [],
            "pioneer_entitlements": [{"telegram_user_id": 22, "payment_reference": "access1", "approved_at": "2026-10-30T10:00:00Z", "revoked_at": None}],
        }
        def request(method, path):
            self.assertEqual(method, "GET")
            return records[path.split("?")[0]]
        rows = fetch_admin_payment_history(request)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["kind"], "subscription")
        self.assertTrue(rows[0]["is_receipt"])
        self.assertFalse(rows[1]["is_receipt"])
        self.assertIsNone(rows[1]["amount_rm"])

    def test_fail_closed_on_bad_response(self):
        with self.assertRaises(RuntimeError):
            fetch_admin_payment_history(lambda *_: None)

    def test_queries_only_required_columns(self):
        paths = []
        def request(method, path):
            paths.append(path)
            return []
        fetch_admin_payment_history(request)
        self.assertEqual(len(paths), 3)
        self.assertTrue(all("select=*" not in p for p in paths))
        self.assertTrue(all("select=telegram_user_id" in p for p in paths))

    def test_rejects_malformed_rows(self):
        with self.assertRaises(RuntimeError):
            fetch_admin_payment_history(lambda *_: [None])

    def test_limit_validation(self):
        with self.assertRaises(ValueError):
            fetch_admin_payment_history(lambda *_: [], limit=1001)


if __name__ == "__main__":
    unittest.main()
