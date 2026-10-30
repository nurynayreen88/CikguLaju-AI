"""Tests for the isolated funnel event recorder. Run: python -m unittest tests/test_user_funnel_analytics.py"""
import os
import tempfile
import unittest
from unittest.mock import patch

import user_funnel_analytics as funnel


class FunnelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "funnel.sqlite3")
        self.settings = patch.multiple(funnel, DB_PATH=self.db, SECRET="unit-test-secret")
        self.settings.start()

    def tearDown(self):
        self.settings.stop()
        self.tmp.cleanup()

    def test_idempotency(self):
        self.assertTrue(funnel.record_event("bot_start", "telegram-123"))
        self.assertFalse(funnel.record_event("bot_start", "telegram-123"))
        self.assertEqual(funnel.summary()["bot_start"], 1)

    def test_separate_events(self):
        funnel.record_event("bot_start", "123")
        funnel.record_event("registration_complete", "123")
        self.assertEqual(funnel.summary()["registration_complete"], 1)
        self.assertEqual(funnel.summary()["bot_start"], 1)

    def test_campaign_filter(self):
        funnel.record_event("promo_click", "visitor-a", "fb")
        funnel.record_event("promo_click", "visitor-b", "status")
        self.assertEqual(funnel.summary("fb")["promo_click"], 1)
        self.assertEqual(funnel.summary()["promo_click"], 2)

    def test_missing_secret_rejected(self):
        with patch.object(funnel, "SECRET", ""):
            with self.assertRaises(RuntimeError):
                funnel.record_event("bot_start", "123")

    def test_invalid_event_rejected(self):
        with self.assertRaises(ValueError):
            funnel.record_event("arbitrary_event", "123")


if __name__ == "__main__":
    unittest.main()
