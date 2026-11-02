"""Web RPH downloads must fail closed until the shared Telegram debit is atomic.

This test does not connect to production accounts or mutate trial balances.
"""
import os
import unittest
from unittest.mock import patch

from tools.run_web_v1_preview import app


class SharedQuotaGuardTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_capabilities_never_advertise_unmetered_downloads(self):
        with patch.dict(os.environ, {'CIKGULAJU_ENV': 'staging', 'CIKGULAJU_WEB_RPH_STAGING_ENABLED': '1'}):
            result = self.client.get('/api/web/english/rph/capabilities')
        self.assertEqual(result.status_code, 200)
        data = result.get_json()
        self.assertIs(data['download_enabled'], False)
        self.assertIs(data['shared_quota_debit_verified'], False)
        self.assertIs(data['telegram_generation_parity_verified'], False)

    def test_anonymous_request_never_generates_document(self):
        with patch.dict(os.environ, {'CIKGULAJU_ENV': 'staging', 'CIKGULAJU_WEB_RPH_STAGING_ENABLED': '1'}):
            response = self.client.post('/api/web/english/rph', json={'year': 2, 'lesson_no': 1, 'format': 'pdf'})
        self.assertIn(response.status_code, (401, 503))
        self.assertEqual(response.mimetype, 'application/json')


if __name__ == '__main__':
    unittest.main()
