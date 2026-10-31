"""Offline tests for staged Supabase payment request writer."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from supabase_payment_request_write import create_payment_request


class SupabasePaymentRequestWriteTests(unittest.TestCase):
    def test_creates_pending_request_and_returns_supabase_id(self):
        calls = []
        def request(method, path, **kwargs):
            calls.append((method, path, kwargs))
            if method == "GET":
                return []
            data = kwargs["json"]
            return [{"id": 301, "telegram_user_id": data["telegram_user_id"],
                     "telegram_message_id": data["telegram_message_id"],
                     "status": "pending"}]
        self.assertEqual(create_payment_request(request, 12345, "10.00", 456), 301)
        self.assertEqual(calls[-1][0:2], ("POST", "pioneer_payment_requests"))
        self.assertEqual(calls[-1][2]["json"]["amount_rm"], "10.00")
        self.assertTrue(calls[-1][2]["json"]["proof_received"])

    def test_accepts_exact_cent_amount_with_trailing_zeros(self):
        def request(method, path, **kwargs):
            if method == "GET":
                return []
            data = kwargs["json"]
            return [{"id": 302, "telegram_user_id": data["telegram_user_id"], "telegram_message_id": data["telegram_message_id"], "status": "pending"}]
        self.assertEqual(create_payment_request(request, 1, "10.000", 2), 302)

    def test_rejects_invalid_inputs_without_writing(self):
        def fail_request(*args, **kwargs):
            self.fail("Unexpected write")
        for uid, amount, mid in [(True, 10, 3), ("1|2", 10, 3),
                                 (1, "NaN", 3), (1, -1, 3),
                                 (1, "10.001", 3), (1, "100000000.00", 3), (1, 10, None),
                                 (0, 10, 3), (1, 10, 0),
                                 (9223372036854775808, 10, 3),
                                 ("9" * 10000, 10, 3),
                                 (1, 10, 9223372036854775808)]:
            with self.subTest(uid=uid, amount=amount, mid=mid):
                with self.assertRaises(ValueError):
                    create_payment_request(fail_request, uid, amount, mid)

    def test_retry_returns_existing_supabase_id(self):
        calls = []
        def request(method, path, **kwargs):
            calls.append(method)
            return [{"id": 41, "telegram_user_id": 1, "telegram_message_id": 2, "amount_rm": "10.00", "status": "pending"}]
        self.assertEqual(create_payment_request(request, 1, 10, 2), 41)
        self.assertEqual(calls, ["GET"])

    def test_different_message_cannot_create_second_pending_request(self):
        calls = []
        def request(method, path, **kwargs):
            calls.append(method)
            if "status=eq.pending" in path:
                return [{"id": 9, "telegram_user_id": 1, "telegram_message_id": 99, "amount_rm": 10, "status": "pending"}]
            return []
        with self.assertRaises(RuntimeError):
            create_payment_request(request, 1, 10, 2)
        self.assertEqual(calls, ["GET", "GET"])

    def test_duplicate_same_message_requires_manual_reconciliation(self):
        def request(method, path, **kwargs):
            self.assertEqual(method, "GET")
            row = {"id": 41, "telegram_user_id": 1, "telegram_message_id": 2, "amount_rm": "10.00", "status": "pending"}
            return [row, dict(row, id=42)]
        with self.assertRaises(RuntimeError):
            create_payment_request(request, 1, 10, 2)

    def test_completed_request_cannot_be_retried(self):
        for status in ("approved", "rejected"):
            with self.subTest(status=status):
                def request(method, path, **kwargs):
                    return [{"id": 41, "telegram_user_id": 1, "telegram_message_id": 2, "amount_rm": 10, "status": status}]
                with self.assertRaises(RuntimeError):
                    create_payment_request(request, 1, 10, 2)

    def test_existing_unknown_status_is_rejected(self):
        def request(method, path, **kwargs):
            return [{"id": 41, "telegram_user_id": 1, "telegram_message_id": 2, "amount_rm": 10, "status": "unexpected"}]
        with self.assertRaises(RuntimeError):
            create_payment_request(request, 1, 10, 2)

    def test_existing_malformed_amount_is_rejected(self):
        def request(method, path, **kwargs):
            self.assertEqual(method, "GET")
            return [{"id": 41, "telegram_user_id": 1, "telegram_message_id": 2, "amount_rm": "broken", "status": "pending"}]
        with self.assertRaises(RuntimeError):
            create_payment_request(request, 1, 10, 2)

    def test_fails_closed_if_insert_response_is_unconfirmed(self):
        with self.assertRaises(RuntimeError):
            create_payment_request(lambda method, *a, **kw: [] if method == "GET" else None, 1, 10, 2)


if __name__ == "__main__":
    unittest.main()
