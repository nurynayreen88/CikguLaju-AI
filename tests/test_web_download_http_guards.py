"""HTTP guard tests: staging download routes must fail closed by default."""
import os
import unittest
from unittest.mock import patch

from tools.run_web_v1_preview import app


class DownloadRouteGuards(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_anonymous_downloads_denied(self):
        with patch.dict(os.environ, {}, clear=True):
            for path in ("/api/generate", "/api/web/english/rph"):
                with self.subTest(path=path):
                    response = self.client.post(path, json={"format": "pdf"})
                    self.assertIn(response.status_code, (401, 503))
                    self.assertNotEqual(response.mimetype, "application/pdf")

    def test_capabilities_still_report_disabled(self):
        response = self.client.get("/api/web/english/rph/capabilities")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["download_enabled"])


if __name__ == "__main__":
    unittest.main()
