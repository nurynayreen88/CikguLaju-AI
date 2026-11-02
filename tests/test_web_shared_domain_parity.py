"""Conservative Telegram/Web shared-domain status tests."""
import unittest
from web.shared_domain_parity import parity_report, SHARED_DOMAINS


class SharedDomainParityTests(unittest.TestCase):
    def test_catalog_alone_does_not_mean_full_parity(self):
        report = parity_report({"lesson_catalog": True})
        self.assertFalse(report["fully_shared"])
        self.assertTrue(report["domains"]["lesson_catalog"])
        self.assertIn("audio_tracks", report["unverified"])
        self.assertIn("trial_ledger", report["unverified"])

    def test_only_all_verified_domains_qualify(self):
        report = parity_report({domain: True for domain in SHARED_DOMAINS})
        self.assertTrue(report["fully_shared"])
        self.assertEqual(report["unverified"], [])

    def test_unknown_and_nonboolean_flags_rejected(self):
        with self.assertRaises(ValueError):
            parity_report({"some_other_source": True})
        with self.assertRaises(ValueError):
            parity_report({"lesson_catalog": "yes"})


if __name__ == "__main__":
    unittest.main()
