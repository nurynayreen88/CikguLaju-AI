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

    def test_rakan_pembangun_requests_are_not_receipts(self):
        def request(method, path):
            if path.startswith("pioneer_payment_requests?"):
                return [{"telegram_user_id": 42, "amount_rm": 10, "status": "approved", "created_at": "2026-10-31"}]
            return []
        rows = fetch_admin_payment_history(request)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "rakan_pembangun_request")
        self.assertFalse(rows[0]["is_receipt"])

    def test_pending_and_failed_are_not_receipts(self):
        statuses = ["pending", "failed", "rejected", "paid"]
        def request(method, path):
            if path.startswith("payments?"):
                return [{"telegram_user_id": 11, "status": status, "created_at": "2026-10-31"} for status in statuses]
            return []
        rows = fetch_admin_payment_history(request)
        self.assertEqual([row["is_receipt"] for row in rows], [False, False, False, True])

    def test_fail_closed_on_bad_response(self):
        with self.assertRaises(RuntimeError):
            fetch_admin_payment_history(lambda *_: None)

    def test_queries_only_required_columns(self):
        paths = []
        def request(method, path):
            paths.append(path)
            return []
        fetch_admin_payment_history(request)
        self.assertEqual(len(paths), 4)
        self.assertTrue(all("select=*" not in p for p in paths))
        self.assertTrue(all("select=telegram_user_id" in p for p in paths))

    def test_rejects_malformed_rows(self):
        with self.assertRaises(RuntimeError):
            fetch_admin_payment_history(lambda *_: [None])

    def test_missing_payment_status_is_not_approved(self):
        def request(method, path):
            if path.startswith("payments?"):
                return [{"telegram_user_id": 1, "created_at": "2026-10-31"}]
            return []
        row = fetch_admin_payment_history(request)[0]
        self.assertEqual(row["status"], "unknown")
        self.assertFalse(row["is_receipt"])

    def test_malformed_timestamp_does_not_crash_sort(self):
        def request(method, path):
            if path.startswith("payments?"):
                return [{"telegram_user_id": 1, "status": "paid", "created_at": 123}, {"telegram_user_id": 2, "status": "paid", "created_at": "2026-10-31"}]
            return []
        self.assertEqual(len(fetch_admin_payment_history(request)), 2)

    def test_malformed_limit_validation(self):
        for limit in (None, "invalid", float("inf")):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    fetch_admin_payment_history(lambda *_: [], limit=limit)

    def test_limit_validation(self):
        with self.assertRaises(ValueError):
            fetch_admin_payment_history(lambda *_: [], limit=1001)


if __name__ == "__main__":
    unittest.main()
