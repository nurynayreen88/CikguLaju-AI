"""Verify special-activity API opt-in does not bypass Telegram privileges."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch
from flask import Flask
from web.telegram_special_activity_api import register_if_enabled


class SpecialActivityIntegration(unittest.TestCase):
    def test_launch_registration_is_opt_in_and_separate_from_rph(self):
        path=Path(__file__).resolve().parents[1]/"tools"/"run_telegram_with_curriculum_api.py"
        code=path.read_text("utf-8")
        ast.parse(code)
        self.assertIn("register_special_rph(telegram_runtime.app)",code)
        self.assertIn("SPECIAL_ACTIVITY_2027_PRIVATE_API_ACTIVE",code)
        self.assertNotIn("rph_standalone.aktiviti_khas.engine import render",code)

    def test_flag_off_keeps_current_telegram_api_unchanged(self):
        app=Flask(__name__)
        count=len(app.url_map._rules)
        with patch.dict("os.environ",{"CIKGULAJU_SPECIAL_RPH_ENABLED":"0",
                                      "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
                                      "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"z"*40}):
            self.assertFalse(register_if_enabled(app))
        self.assertEqual(len(app.url_map._rules),count)

    def test_flag_on_always_requires_bearer(self):
        app=Flask(__name__)
        with patch.dict("os.environ",{"CIKGULAJU_SPECIAL_RPH_ENABLED":"1",
                                      "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
                                      "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"z"*40}):
            self.assertTrue(register_if_enabled(app))
            public=app.test_client().get("/internal/rph/v1/aktiviti-khas/options",
                query_string={"kind":"TRANSISI_TAHUN_1","year":"1"})
            self.assertEqual(public.status_code,401)
            private=app.test_client().get("/internal/rph/v1/aktiviti-khas/options",
                query_string={"kind":"TRANSISI_TAHUN_1","year":"1"},
                headers={"Authorization":"Bearer "+"z"*40})
            self.assertEqual(private.status_code,200)
            self.assertEqual(private.get_json()["status"],"DRAFT_REVIEW")
            self.assertEqual(len(private.get_json()["items"]),20)


if __name__=="__main__":
    unittest.main()
