import unittest

try:
    from tools.run_web_v1_preview import app
except ImportError:
    app = None


@unittest.skipIf(app is None, "Flask preview dependencies unavailable")
class PreviewSecurityTests(unittest.TestCase):
    def test_health_has_security_headers(self):
        response = app.test_client().get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_account_status_stays_disconnected(self):
        response = app.test_client().get("/api/account/status")
        self.assertIn(response.status_code, (401, 503))
        self.assertFalse(response.get_json()["authenticated"])


if __name__ == "__main__":
    unittest.main()
