"""Offline HTTP integration of experimental Web RPH download and quota.

All backend reads, renderer calls and quota debits are mocked. No live
Supabase account, Telegram token or production database is touched.
"""
import os
import unittest
from unittest.mock import patch
from tools.run_web_v1_preview import app
from web_v1_telegram_auth_routes import COOKIE

ENV = {"CIKGULAJU_ENV": "staging",
       "CIKGULAJU_WEB_RPH_STAGING_ENABLED": "1",
       "CIKGULAJU_WEB_RPH_DELIVERY_EXPERIMENT": "1",
       "SUPABASE_URL": "https://example.supabase.co",
       "SUPABASE_SECRET_KEY": "test-key",
       "CIKGULAJU_WEB_APPROVED_DB": "/tmp/not-used.db",
       "CIKGULAJU_WEB_APPROVED_TABLE": "approved",
       "CIKGULAJU_WEB_APPROVED_ID_COLUMN": "id",
       "CIKGULAJU_WEB_APPROVED_TITLE_COLUMN": "title",
       "CIKGULAJU_WEB_APPROVED_CONTENT_COLUMN": "content",
       "CIKGULAJU_WEB_APPROVED_STATUS_COLUMN": "status",
       "CIKGULAJU_WEB_APPROVED_STATUS_VALUE": "READY",
       "CIKGULAJU_WEB_APPROVED_REFERENCE_COLUMN": "reference"}
ACCOUNT = {"authenticated": True, "telegram_user_id": 123,
           "free_remaining": 2, "rakan_pembangun": False}


class WebDeliveryHttpTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.set_cookie(COOKIE, "test-session")

    def patches(self):
        return (
            patch.dict(os.environ, ENV),
            patch("web_v1_telegram_auth_routes._config",
                  return_value={"CIKGULAJU_WEB_SESSION_SECRET": "test"}),
            patch("web_v1_sessions.verify_session_ticket", return_value=123),
            patch("web_v1_telegram_auth_routes._lookup", return_value=ACCOUNT),
        )

    def test_approved_route_downloads_only_after_authorization(self):
        from web.rph_document_renderer import ApprovedRPH
        patches = self.patches()
        with patches[0], patches[1], patches[2], patches[3], \
             patch("web.approved_rph_reader.load_approved_rph",
                   return_value=ApprovedRPH(1, "Test", "Lesson", "ready")), \
             patch("web.rph_download_pipeline.prepare_approved_download",
                   return_value={"allowed": True, "document": b"%PDF-1.4 test",
                                 "mime": "application/pdf", "remaining": 1}) as pipeline:
            response = self.client.post("/api/generate",
                                        json={"lesson_id": 1, "format": "pdf"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        self.assertEqual(response.data, b"%PDF-1.4 test")
        self.assertEqual(pipeline.call_args.args[3], 123)

    def test_denied_quota_returns_no_document(self):
        from web.rph_document_renderer import ApprovedRPH
        patches = self.patches()
        with patches[0], patches[1], patches[2], patches[3], \
             patch("web.approved_rph_reader.load_approved_rph",
                   return_value=ApprovedRPH(1, "Test", "Lesson", "ready")), \
             patch("web.rph_download_pipeline.prepare_approved_download",
                   return_value={"allowed": False, "document": None,
                                 "mime": None, "remaining": 0}):
            response = self.client.post("/api/generate",
                                        json={"lesson_id": 1, "format": "pdf"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.mimetype, "application/json")

    def test_english_release_gate_then_delivery(self):
        patches = self.patches()
        with patches[0], patches[1], patches[2], patches[3], \
             patch("web.english_release_gate.load_release_ready_english",
                   return_value="Approved lesson content") as release, \
             patch("web.rph_download_pipeline.prepare_approved_download",
                   return_value={"allowed": True, "document": b"%PDF-1.4 test",
                                 "mime": "application/pdf", "remaining": 1}) as pipeline:
            response = self.client.post("/api/web/english/rph",
                                        json={"year": 2, "lesson_no": 12,
                                              "format": "pdf"})
        self.assertEqual(response.status_code, 200)
        release.assert_called_once_with(2, 12)
        self.assertEqual(pipeline.call_args.args[3], 123)

    def test_experiment_off_even_if_staging_enabled(self):
        patches = self.patches()
        with patches[0], patches[1], patches[2], patches[3], \
             patch.dict(os.environ, {"CIKGULAJU_WEB_RPH_DELIVERY_EXPERIMENT": "0"}):
            response = self.client.post("/api/generate",
                                        json={"lesson_id": 1, "format": "pdf"})
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
