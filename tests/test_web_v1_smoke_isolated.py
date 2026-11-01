"""Web V1 isolated smoke checks: no real database or credentials required."""
import unittest
from unittest.mock import patch
from tools.run_web_v1_preview import app


class WebV1SmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_preview_never_claims_generation_enabled(self):
        with patch.dict("os.environ", {"CIKGULAJU_WEB_PREVIEW_DB": ""}):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["database_connected"])
        self.assertFalse(response.json["generation_enabled"])

    def test_no_account_without_authentication(self):
        response = self.client.get("/api/account/status")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json["authenticated"])

    def test_no_generation_or_download(self):
        self.assertEqual(self.client.post("/api/generate").status_code, 503)
        self.assertEqual(self.client.get("/api/materials").status_code, 503)
        self.assertEqual(self.client.get("/api/materials/download/example").status_code, 503)

    def test_options_fail_closed_without_database(self):
        with patch.dict("os.environ", {"CIKGULAJU_WEB_PREVIEW_DB": ""}):
            response = self.client.get("/api/options?year=1&kind=units&subject=ENGLISH")
        self.assertEqual(response.status_code, 503)

    def test_invalid_options_rejected(self):
        self.assertEqual(self.client.get("/api/options?year=0&kind=subjects").status_code, 400)
        self.assertEqual(self.client.get("/api/options?year=1&kind=unknown").status_code, 400)


if __name__ == "__main__":
    unittest.main()
