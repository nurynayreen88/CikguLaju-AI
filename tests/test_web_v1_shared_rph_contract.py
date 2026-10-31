"""Isolated tests for the future shared Telegram/web RPH service contract."""
import unittest

from web_v1_shared_rph_contract import (
    RphRequest, UnconfiguredRphService, validate_rph_request
)


class SharedRphContractTests(unittest.TestCase):
    def setUp(self):
        self.request = RphRequest(
            account_id="user-123", lesson_id="EN3-093",
            output_format="pdf", idempotency_key="request-001"
        )

    def test_valid_request(self):
        validate_rph_request(self.request)

    def test_rejects_unsupported_format(self):
        request = RphRequest("user-123", "EN3-093", "exe", "request-001")
        with self.assertRaises(ValueError):
            validate_rph_request(request)

    def test_rejects_missing_identifiers(self):
        request = RphRequest("", "EN3-093", "pdf", "request-001")
        with self.assertRaises(ValueError):
            validate_rph_request(request)

    def test_unconfigured_generator_fails_closed(self):
        validate_rph_request(self.request)
        with self.assertRaisesRegex(RuntimeError, "not connected"):
            UnconfiguredRphService().generate(self.request)


if __name__ == "__main__":
    unittest.main()
