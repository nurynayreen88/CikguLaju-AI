"""Regression tests for authenticated, fail-closed Web materials listing."""
import os
import unittest
from unittest.mock import patch
from web.authoritative_curriculum_source import SharedSourceUnavailable


class WebMaterialsRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.run_web_v1_preview import app
        cls.app = app

    def _call(self, query="/api/materials?year=2&subject=ENGLISH&lesson=93", account=True, token="x" * 40, source_error=False):
        from web_v1_sessions import issue_session_ticket
        from web_v1_telegram_auth_routes import COOKIE
        secret = "s" * 40
        config = {"CIKGULAJU_WEB_SESSION_SECRET": secret}
        account_data = {"telegram_user_id": 123} if account else None
        env = {"CIKGULAJU_AUTHORITATIVE_API_URL": "https://telegram.example",
               "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}
        with patch("web_v1_telegram_auth_routes._config", return_value=config), \
             patch("web_v1_telegram_auth_routes._lookup", return_value=account_data), \
             patch.dict(os.environ, env), \
             patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource") as adapter:
            if source_error:
                adapter.return_value.get_approved_materials.side_effect = SharedSourceUnavailable("offline")
            else:
                adapter.return_value.get_approved_materials.return_value = []
            client = self.app.test_client()
            client.set_cookie(COOKIE, issue_session_ticket(123, secret))
            response = client.get(query)
            return response, adapter

    def test_download_does_not_expose_unverified_file(self):
        from web_v1_sessions import issue_session_ticket
        from web_v1_telegram_auth_routes import COOKIE
        secret = "s" * 40
        config = {"CIKGULAJU_WEB_SESSION_SECRET": secret}
        with patch("web_v1_telegram_auth_routes._config", return_value=config), \
             patch("web_v1_telegram_auth_routes._lookup", return_value={"telegram_user_id": 123}):
            client = self.app.test_client()
            client.set_cookie(COOKIE, issue_session_ticket(123, secret))
            response = client.get("/api/materials/download/abc")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json["code"], "MATERIAL_DELIVERY_NOT_VERIFIED")

    def test_verified_empty_list(self):
        response, adapter = self._call()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"items": []})
        key = adapter.return_value.get_approved_materials.call_args.args[0]
        self.assertEqual((key.year, key.subject_code, key.lesson_id), (2, "ENGLISH", "93"))

    def test_no_account_no_remote_access(self):
        response, adapter = self._call(account=False)
        self.assertEqual(response.status_code, 403)
        adapter.assert_not_called()

    def test_invalid_lesson_no_remote_access(self):
        response, adapter = self._call(query="/api/materials?year=2&subject=ENGLISH&lesson=")
        self.assertEqual(response.status_code, 400)
        adapter.assert_not_called()

    def test_unavailable_telegram_does_not_fabricate_materials(self):
        response, _ = self._call(source_error=True)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["code"], "APPROVED_MATERIALS_NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
