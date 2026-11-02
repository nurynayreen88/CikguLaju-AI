"""Tests for the standalone local-only preview app."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_web_v1_preview.py"
spec = importlib.util.spec_from_file_location("cikgulaju_web_preview_runner", RUNNER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.client = module.app.test_client()

    def test_preview_is_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CikguLaju AI", response.data)
        self.assertIn(b"disabled", response.data)

    def test_selection_requires_login_and_generation_is_disabled(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="workspace"', response.data)
        self.assertIn(b'id="catalog-status"', response.data)
        self.assertIn(b'id="unit" hidden disabled', response.data)
        self.assertIn(b'id="lesson" hidden disabled', response.data)
        self.assertIn(b'id="generate-docx"', response.data)
        self.assertIn(b'id="generate-pdf"', response.data)
        self.assertIn(b'Muat turun Web akan dibuka', response.data)

    def test_health_declares_no_data_or_generation(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "preview-only")
        self.assertFalse(response.json["database_connected"])
        self.assertFalse(response.json["generation_enabled"])

    def test_no_production_routes(self):
        for route in ("/web/health", "/generate", "/telegram", "/api/rph"):
            self.assertEqual(self.client.get(route).status_code, 404)


if __name__ == "__main__":
    unittest.main()
