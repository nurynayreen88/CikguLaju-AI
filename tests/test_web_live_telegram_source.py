"""Live Telegram curriculum provenance for source-backed Web RPH selection."""
import os
import unittest
from unittest.mock import patch
from tools.run_web_v1_preview import app

class SharedRuntimeFlowTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
        self.settings=patch.dict(os.environ, {
            "CIKGULAJU_WEB_CATALOG_MODE":"telegram-api",
            "CIKGULAJU_AUTHORITATIVE_API_URL":"https://telegram-source.example",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"a"*40,
        })
        self.config=patch("web_v1_telegram_auth_routes._config",
                          return_value={"CIKGULAJU_WEB_SESSION_SECRET":"x"*40})
        self.session=patch("web_v1_sessions.verify_session_ticket",return_value=123)
        self.account=patch("web_v1_telegram_auth_routes._lookup",
                           return_value={"telegram_user_id":123,"authenticated":True})
        for p in (self.settings,self.config,self.session,self.account):p.start()

    def tearDown(self):
        for p in (self.account,self.session,self.config,self.settings):p.stop()

    @patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource")
    def test_live_source_subjects_and_exact_english_lesson_numbers(self,source):
        source.return_value.list_subjects.return_value=[
            {"value":"ENGLISH","label":"Bahasa Inggeris"},
            {"value":"BM","label":"Bahasa Melayu"}]
        sub=self.client.get("/api/options?kind=subjects&year=4")
        self.assertEqual(sub.status_code,200,sub.get_json())
        codes=[r["value"] for r in sub.get_json()]
        self.assertIn("ENGLISH",codes)
        self.assertIn("MORAL",codes)
        self.assertIn("PJPK",codes)
        units=self.client.get("/api/options?kind=units&year=4&subject=ENGLISH")
        self.assertEqual(units.status_code,200,units.get_json())
        self.assertTrue(len(units.get_json())>0)
        unit=units.get_json()[0]["value"]
        from urllib.parse import urlencode
        pdp=self.client.get("/api/options?"+urlencode({
            "kind":"pdp","year":4,"subject":"ENGLISH","unit":unit}))
        self.assertEqual(pdp.status_code,200,pdp.get_json())
        self.assertTrue(all(r["value"].startswith("e-4-") for r in pdp.get_json()))
        source.return_value.list_units.assert_not_called()
        source.return_value.list_lessons.assert_not_called()

    @patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource")
    def test_non_standalone_rpt_subject_from_live_telegram_only(self,source):
        source.return_value.list_subjects.return_value=[
            {"value":"BM","label":"Bahasa Melayu"}]
        source.return_value.list_units.return_value=[{"value":"Unit 1","label":"Unit 1"}]
        r=self.client.get("/api/options?kind=units&year=4&subject=BM")
        self.assertEqual(r.status_code,200,r.get_json())
        self.assertEqual(r.get_json()[0]["value"],"Unit 1")
        source.return_value.list_units.assert_called_once_with(4,"BM",None)

    @patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource")
    def test_no_local_source_on_live_failure(self,source):
        from web.authoritative_curriculum_source import SharedSourceUnavailable
        source.return_value.list_subjects.side_effect=SharedSourceUnavailable("offline")
        r=self.client.get("/api/options?kind=units&year=4&subject=ENGLISH")
        self.assertEqual(r.status_code,503)
        self.assertEqual(r.get_json()["code"],"TELEGRAM_CURRICULUM_API_UNAVAILABLE")

if __name__=="__main__":
    unittest.main()
