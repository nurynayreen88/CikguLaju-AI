"""Offline tests for the Telegram admin payment-history page."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from supabase_admin_payment_page import show_admin_payment_history


class AdminPaymentPageTests(unittest.TestCase):
    def test_rakan_pembangun_approval_is_not_a_receipt(self):
        sent = []
        rows = [{
            "telegram_user_id": 12345678,
            "kind": "rakan_pembangun_approval",
            "amount_rm": None,
            "payment_reference": "approval1",
            "status": "approved",
            "event_at": "2026-10-31T00:00:00Z",
            "is_receipt": False,
        }]
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=rows):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertEqual(len(sent), 1)
        self.assertIn("bukan resit", sent[0][1])
        self.assertIn("jumlah tidak direkod", sent[0][1])
        self.assertIn("admin_user|12345678", str(sent[0][2]))

    def test_rakan_pembangun_request_not_receipt(self):
        sent = []
        rows = [{"telegram_user_id": 12345678, "kind": "rakan_pembangun_request", "amount_rm": 10, "status": "pending", "event_at": "2026", "is_receipt": False}]
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=rows):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertIn("permintaan bayaran, bukan resit", sent[0][1])

    def test_pending_payment_not_mislabeled_as_access_approval(self):
        sent = []
        rows = [{"telegram_user_id": 12345678, "kind": "credit", "amount_rm": 10, "status": "pending", "event_at": "2026", "is_receipt": False}]
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=rows):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertIn("belum disahkan sebagai bayaran", sent[0][1])
        self.assertNotIn("kelulusan akses", sent[0][1])

    def test_supabase_failure_is_not_reported_as_empty_history(self):
        sent = []
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", side_effect=RuntimeError("db down")):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertIn("tidak dapat dibaca", sent[0][1])
        self.assertNotIn("Tiada rekod", sent[0][1])

    def test_html_escaping(self):
        sent = []
        rows = [{"telegram_user_id": 12345678, "kind": "<script>", "amount_rm": 8, "status": "<bad>", "event_at": "2026", "is_receipt": True}]
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=rows):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertIn("&lt;script&gt;", sent[0][1])
        self.assertIn("&lt;bad&gt;", sent[0][1])
        self.assertNotIn("<script>", sent[0][1])

    def test_invalid_amount_does_not_crash_page(self):
        sent = []
        rows = [{"telegram_user_id": 12345678, "kind": "subscription", "amount_rm": "not-a-number", "status": "paid", "event_at": "2026", "is_receipt": True}]
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=rows):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertIn("jumlah tidak sah", sent[0][1])

    def test_invalid_page_is_safe(self):
        sent = []
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=[]):
            show_admin_payment_history(99, "invalid", None, lambda *args: sent.append(args))
        self.assertIn("Halaman 1", sent[0][1])

    def test_untrusted_user_id_not_in_callback(self):
        sent = []
        rows = [{"telegram_user_id": "123|admin_panel", "kind": "credit", "amount_rm": 10, "status": "pending", "event_at": "2026", "is_receipt": False}]
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=rows):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertNotIn("admin_user|", str(sent[0][2]))

    def test_pagination(self):
        rows = [{
            "telegram_user_id": 10000000 + i,
            "kind": "subscription",
            "amount_rm": 8,
            "status": "paid",
            "event_at": str(i),
            "is_receipt": True,
        } for i in range(9)]
        sent = []
        with patch("supabase_admin_payment_page.fetch_admin_payment_history", return_value=rows):
            show_admin_payment_history(99, 0, None, lambda *args: sent.append(args))
        self.assertIn("admin_list|payments|1", str(sent[0][2]))


if __name__ == "__main__":
    unittest.main()
