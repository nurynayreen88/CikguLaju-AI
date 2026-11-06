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
    def test_bm_uses_only_native_hierarchy_never_skill_dropdown(self,source):
        source.return_value.list_subjects.return_value=[
            {"value":"BM","label":"Bahasa Melayu"}]
        source.return_value.list_bm_themes.return_value=[
            {"value":"Tema 1: Kekeluargaan","label":"Tema 1: Kekeluargaan"}]
        source.return_value.list_bm_units.return_value=[
            {"value":"Keluargaku","label":"Unit 1: Keluargaku"}]
        source.return_value.list_bm_topics.return_value=[
            {"value":"Ceria Pagi","label":"Ceria Pagi"}]
        source.return_value.list_bm_pdps.return_value=[
            {"value":"128","label":"PdP 001 — Mendengar","textbook_ref":"Buku Teks m/s 3"}]
        theme=self.client.get("/api/options?kind=bm-themes&year=4&subject=BM")
        self.assertEqual(theme.status_code,200,theme.get_json())
        self.assertEqual(theme.get_json()[0]["value"],"Tema 1: Kekeluargaan")
        unit=self.client.get(
            "/api/options?kind=bm-units&year=4&subject=BM&theme=Tema%201%3A%20Kekeluargaan")
        self.assertEqual(unit.status_code,200,unit.get_json())
        topic=self.client.get(
            "/api/options?kind=bm-topics&year=4&subject=BM"
            "&theme=Tema%201%3A%20Kekeluargaan&unit=Keluargaku")
        self.assertEqual(topic.status_code,200,topic.get_json())
        pdp=self.client.get(
            "/api/options?kind=bm-pdp&year=4&subject=BM"
            "&theme=Tema%201%3A%20Kekeluargaan"
            "&unit=Keluargaku&topic=Ceria%20Pagi")
        self.assertEqual(pdp.status_code,200,pdp.get_json())
        self.assertEqual(pdp.get_json()[0]["value"],"128")
        self.assertEqual(pdp.get_json()[0]["textbook_ref"],"Buku Teks m/s 3")
        source.return_value.list_bm_themes.assert_called_once_with(4)
        source.return_value.list_bm_units.assert_called_once_with(4,"Tema 1: Kekeluargaan")
        source.return_value.list_bm_topics.assert_called_once_with(
            4,"Tema 1: Kekeluargaan","Keluargaku")
        source.return_value.list_bm_pdps.assert_called_once_with(
            4,"Tema 1: Kekeluargaan","Keluargaku","Ceria Pagi")
        for kind in ("units","pdp"):
            old=self.client.get("/api/options?kind="+kind+"&year=4&subject=BM")
            self.assertEqual(old.status_code,400)
            self.assertEqual(old.get_json()["code"],"BM_HIERARCHY_REQUIRED")
        source.return_value.list_units.assert_not_called()

    @patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource")
    def test_no_local_source_on_live_failure(self,source):
        from web.authoritative_curriculum_source import SharedSourceUnavailable
        source.return_value.list_subjects.side_effect=SharedSourceUnavailable("offline")
        r=self.client.get("/api/options?kind=units&year=4&subject=ENGLISH")
        self.assertEqual(r.status_code,503)
        self.assertEqual(r.get_json()["code"],"TELEGRAM_CURRICULUM_API_UNAVAILABLE")

if __name__=="__main__":
    unittest.main()
