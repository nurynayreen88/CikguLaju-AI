"""Offline validation tests; no production payment or user access writes."""
import unittest
from staging_payment_reference import normalize_transaction_reference, transaction_key

class TransactionReferenceValidationTests(unittest.TestCase):
    def test_normalizes_case_and_edge_spaces(self):
        self.assertEqual(normalize_transaction_reference(" tx-12345 "), "TX-12345")
    def test_rejects_short_reference(self):
        with self.assertRaises(ValueError):
            normalize_transaction_reference("123")
    def test_rejects_internal_grant_reference(self):
        with self.assertRaises(ValueError):
            normalize_transaction_reference("pioneer-payment:123:abc123")
    def test_rejects_embedded_spaces(self):
        with self.assertRaises(ValueError):
            normalize_transaction_reference("TX 12345")
    def test_distinguishes_merchants(self):
        self.assertNotEqual(transaction_key("TNG","merchant-A","tx-12345"),
                            transaction_key("TNG","merchant-B","tx-12345"))

if __name__ == "__main__":
    unittest.main()
