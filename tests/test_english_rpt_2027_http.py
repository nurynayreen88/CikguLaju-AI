"""Flask test-client regression for paid English RPT PDF endpoints."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from flask import Flask

from web.english_rpt_2027_http import create_english_rpt_blueprint


class EnglishRPTWebTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Flask(__name__)
        self.app.register_blueprint(create_english_rpt_blueprint(Path(self.temp.name)))
        self.client = self.app.test_client()
        self.client.set_cookie("cikgulaju_web_v1_session", "signed")
        self.account = {"authenticated": True, "telegram_user_id": 123,
                        "rakan_pembangun": False, "vip_until": None,
                        "free_remaining": 10}

        patchers = [
            patch("web_v1_telegram_auth_routes._config", return_value={"CIKGULAJU_WEB_SESSION_SECRET": "s" * 32}),
            patch("web_v1_telegram_auth_routes._lookup", side_effect=lambda *_: self.account),
            patch("web_v1_sessions.verify_session_ticket", return_value=123),
        ]
        for p in patchers:
            p.start()
            self.addCleanup(p.stop)

    def test_unpaid_blocked_even_with_ten_free_rph(self):
        (Path(self.temp.name) / "RPT_ENGLISH_TAHUN_2_2027_UNTUK_GURU.pdf").write_bytes(b"%PDF-test")
        r = self.client.get("/api/rpt/2027/english/2.pdf")
        self.assertEqual(r.status_code, 403)
        self.assertNotIn(b"%PDF-test", r.data)

    def test_lifetime_download_same_pdf(self):
        self.account["rakan_pembangun"] = True
        pdf = Path(self.temp.name) / "RPT_ENGLISH_TAHUN_6_2027_UNTUK_GURU.pdf"
        pdf.write_bytes(b"%PDF-1.7\\nexample")
        r = self.client.get("/api/rpt/2027/english/6.pdf")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, pdf.read_bytes())
        self.assertEqual(r.mimetype, "application/pdf")
        self.assertIn("no-store", r.headers["Cache-Control"])
        self.assertIn("attachment", r.headers["Content-Disposition"])

    def test_invalid_year_and_missing_file(self):
        self.account["rakan_pembangun"] = True
        self.assertEqual(self.client.get("/api/rpt/2027/english/1.pdf").status_code, 404)
        self.assertEqual(self.client.get("/api/rpt/2027/english/5.pdf").status_code, 503)

    def test_inventory_marks_unpaid(self):
        r = self.client.get("/api/rpt/2027/english")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json["allowed"])
        self.assertEqual(r.json["years"], [2, 3, 4, 5, 6])

    def test_unauthenticated_fails_closed(self):
        with patch("web_v1_sessions.verify_session_ticket", return_value=None):
            self.assertEqual(self.client.get("/api/rpt/2027/english/2.pdf").status_code, 401)

    def test_backend_error_fails_closed(self):
        with patch("web_v1_telegram_auth_routes._lookup", side_effect=RuntimeError("offline")):
            self.assertEqual(self.client.get("/api/rpt/2027/english/2.pdf").status_code, 503)

    def test_expired_vip_not_eligible(self):
        self.account["vip_expires_at"] = "2025-01-01T00:00:00+00:00"
        self.assertEqual(self.client.get("/api/rpt/2027/english/2.pdf").status_code, 403)


if __name__ == "__main__":
    unittest.main()
