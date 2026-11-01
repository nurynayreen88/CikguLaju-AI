"""Verify local Web V1 cannot bypass the shared Telegram backend."""
import unittest
from tools.run_web_v1_preview import app


class SharedRoutesTests(unittest.TestCase):
    def test_readiness_is_truthful(self):
        client = app.test_client()
        response = client.get("/api/shared/status")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["shared_backend_connected"])
        self.assertFalse(response.json["generation_enabled"])

    def test_generation_and_download_fail_closed(self):
        client = app.test_client()
        for method, path in (
            ("get", "/api/materials"),
            ("post", "/api/generate"),
            ("get", "/api/materials/download/any-file"),
        ):
            with self.subTest(path=path):
                self.assertEqual(getattr(client, method)(path).status_code, 503)


if __name__ == "__main__":
    unittest.main()
