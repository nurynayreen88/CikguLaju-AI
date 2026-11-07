"""Security and data integrity tests for staging payment store."""
import unittest
from unittest.mock import patch
from web.google_payment_store import (
    MAX_RECEIPT, validate_receipt, submit_receipt, review_payment,
    PaymentConflict, PaymentUnavailable, web_payment_access,
)

ACCOUNT = "b1d855d1-a68d-4e93-909b-b71ee8ae9e78"
REQUEST_ID = "8888ee83-6ff8-430d-bf86-800cd403e5ec"
CONFIG = {"supabase_url":"https://staging.supabase.co",
          "staging_service_key":"server-side-service-role-placeholder"}
PLANS = {"rakan_pembangun":{"enabled":True,"amount_sen":1000}}
PDF = b"%PDF-" + b"z"*1024


class PaymentStoreSafety(unittest.TestCase):
    def test_receipt_magic_and_size(self):
        extension, sha = validate_receipt(PDF, "application/pdf")
        self.assertEqual(extension, ".pdf")
        self.assertEqual(len(sha), 64)
        for data, mime in [(b"z"*800, "application/pdf"),
                           (b"%PDF-short", "application/pdf"),
                           (b"x"*(MAX_RECEIPT+1), "application/pdf"),
                           (PDF, "text/plain")]:
            with self.assertRaises(ValueError):
                validate_receipt(data,mime)

    def test_duplicate_pending_is_rejected_before_upload(self):
        with (
            patch("web.google_payment_store._rows", return_value=[{"id":REQUEST_ID}]),
            patch("web.google_payment_store._request") as upload,
        ):
            with self.assertRaises(PaymentConflict):
                submit_receipt(CONFIG, ACCOUNT, "rakan_pembangun", PLANS,
                               PDF, "application/pdf")
            upload.assert_not_called()

    def test_upload_uses_account_namespace_and_verified_price(self):
        with (
            patch("web.google_payment_store._rows", return_value=[]),
            patch("web.google_payment_store._request") as upload,
            patch("web.google_payment_store._rpc", return_value=REQUEST_ID) as rpc,
        ):
            result=submit_receipt(CONFIG,ACCOUNT,"rakan_pembangun",PLANS,
                                  PDF,"application/pdf")
        self.assertEqual(result, REQUEST_ID)
        self.assertEqual(upload.call_count,1)
        endpoint=upload.call_args.args[1]
        self.assertIn("/storage/v1/object/web-receipts-staging/"+ACCOUNT+"/",endpoint)
        self.assertEqual(rpc.call_args.args[1],"submit_web_payment_request")
        payload=rpc.call_args.args[2]
        self.assertEqual(payload["p_account_id"],ACCOUNT)
        self.assertEqual(payload["p_amount_sen"],1000)

    def test_uncertain_commit_requires_check_status_before_retry(self):
        with (
            patch("web.google_payment_store._rows", return_value=[]),
            patch("web.google_payment_store._request"),
            patch("web.google_payment_store._rpc",
                  side_effect=PaymentUnavailable("timeout")),
        ):
            with self.assertRaisesRegex(PaymentUnavailable,"Semak status"):
                submit_receipt(CONFIG,ACCOUNT,"rakan_pembangun",PLANS,
                               PDF,"application/pdf")

    def test_review_requires_admin_and_preserves_idempotent_reply(self):
        with self.assertRaises(PermissionError):
            review_payment(CONFIG,REQUEST_ID,"approve",None)
        with patch("web.google_payment_store._rpc", return_value={
            "id":REQUEST_ID,"status":"approved","already_reviewed":True}) as rpc:
            outcome=review_payment(CONFIG,REQUEST_ID,"approve",123456)
        self.assertTrue(outcome["already_reviewed"])
        self.assertEqual(rpc.call_args.args[2]["p_admin_actor"],"telegram:123456")

    def test_non_expiring_rakan_entitlement_is_active_only_as_payment(self):
        with patch("web.google_payment_store._rows",return_value=[{
            "plan_code":"rakan_pembangun","valid_from":"2026-11-07T01:00:00Z",
            "valid_until":None
        }]):
            access=web_payment_access(CONFIG,ACCOUNT)
        self.assertTrue(access["payment_access_active"])
        self.assertFalse(access["rph_google_integration_ready"])


if __name__ == "__main__":
    unittest.main()
