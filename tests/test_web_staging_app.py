"""Smoke test the standalone staging WSGI entrypoint."""
import unittest
from web_staging_app import create_app


class WebStagingAppTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_home_renders_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CikguLaju", response.data)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_catalog_is_wired(self):
        response = self.client.get("/api/web/catalog/english/2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["subject"], "ENGLISH")
        self.assertIn("lessons", response.json)

    def test_no_generation_route(self):
        self.assertEqual(self.client.post("/api/staging/rph/generate").status_code, 404)


if __name__ == "__main__":
    unittest.main()
