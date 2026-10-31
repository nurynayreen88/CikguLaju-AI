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
            if method == "GET":\n                return []\n            data = kwargs["json"]
            return [{"id": 301, "telegram_user_id": data["telegram_user_id"],
                     "telegram_message_id": data["telegram_message_id"],
                     "status": "pending"}]
        self.assertEqual(create_payment_request(request, 12345, "10.00", 456), 301)
        self.assertEqual(calls[0][0:2], ("POST", "pioneer_payment_requests"))
        self.assertEqual(calls[0][2]["json"]["amount_rm"], "10.00")
        self.assertTrue(calls[0][2]["json"]["proof_received"])

    def test_rejects_invalid_inputs_without_writing(self):
        def fail_request(*args, **kwargs):
            self.fail("Unexpected write")
        for uid, amount, mid in [(True, 10, 3), ("1|2", 10, 3),
                                 (1, "NaN", 3), (1, -1, 3),
                                 (1, "10.001", 3), (1, 10, None)]:
            with self.subTest(uid=uid, amount=amount, mid=mid):
                with self.assertRaises(ValueError):
                    create_payment_request(fail_request, uid, amount, mid)

    def test_retry_returns_existing_supabase_id(self):\n        calls = []\n        def request(method, path, **kwargs):\n            calls.append(method)\n            return [{"id": 41, "telegram_user_id": 1, "telegram_message_id": 2, "amount_rm": "10.00", "status": "pending"}]\n        self.assertEqual(create_payment_request(request, 1, 10, 2), 41)\n        self.assertEqual(calls, ["GET"])\n\n    def test_fails_closed_if_insert_response_is_unconfirmed(self):
        with self.assertRaises(RuntimeError):
            create_payment_request(lambda method, *a, **kw: [] if method == "GET" else None, 1, 10, 2)


if __name__ == "__main__":
    unittest.main()
