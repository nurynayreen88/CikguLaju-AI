"""Production Web subject menu lists new subjects only when Telegram is live."""
import os
import unittest
from unittest.mock import patch

from tools.run_web_v1_preview import app
from web.native_telegram_rph_client import NativeRPHUnavailable


class DraftMenuTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
        self.patches=[
            patch.dict(os.environ,{
                "CIKGULAJU_WEB_CATALOG_MODE":"telegram-api",
                "CIKGULAJU_AUTHORITATIVE_API_URL":"https://source.example",
                "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"z"*40,
            }),
            patch("web_v1_telegram_auth_routes._config",
                  return_value={"CIKGULAJU_WEB_SESSION_SECRET":"x"*40}),
            patch("web_v1_sessions.verify_session_ticket",return_value=123),
            patch("web_v1_telegram_auth_routes._lookup",
                  return_value={"telegram_user_id":123,"authenticated":True}),
            patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource"),
            patch("web.native_telegram_other_draft_client.list_draft_units"),
            patch("web.native_telegram_other_draft_client.list_draft_lessons"),
            patch("web.native_telegram_sejarah_2027_client.list_sejarah_units"),
        ]
        self.config,self.auth,self.session,self.user,self.native,self.units,self.lessons,self.history=[p.start() for p in self.patches]
        self.native.return_value.list_subjects.return_value=[
            {"value":"BM","label":"Bahasa Melayu"}]
        self.units.return_value=[{"value":"u01","label":"Unit 1: Buku","status":"DRAF"}]
        self.lessons.return_value=[
            {"value":"001","label":"PdP 001 — Bacaan (DRAF)","status":"DRAF",
             "formats":["word"]}]
        self.history.side_effect=NativeRPHUnavailable("unavailable")

    def tearDown(self):
        for p in reversed(self.patches): p.stop()

    def test_draft_subjects_y2_y6_source_aware(self):
        for year in (2,6):
            self.units.reset_mock()
            res=self.client.get(f"/api/options?kind=subjects&year={year}")
            self.assertEqual(res.status_code,200,res.get_json())
            by={x["value"]:x["label"] for x in res.get_json()}
            self.assertEqual(by.get("ARAB"),"Bahasa Arab (DRAF)")
            self.assertEqual(by.get("MUZIK"),"Pendidikan Muzik (DRAF)")
            self.assertNotIn("SEJARAH",by)
            self.assertEqual(self.units.call_count,2)
        res=self.client.get("/api/options?kind=subjects&year=1")
        self.assertEqual(res.status_code,200,res.get_json())
        by={x["value"] for x in res.get_json()}
        self.assertNotIn("ARAB",by)
        self.assertNotIn("MUZIK",by)

    def test_no_false_draft_advertisement_when_telegram_unavailable(self):
        self.units.side_effect=NativeRPHUnavailable("offline")
        res=self.client.get("/api/options?kind=subjects&year=3")
        self.assertEqual(res.status_code,200,res.get_json())
        codes={x["value"] for x in res.get_json()}
        self.assertNotIn("ARAB",codes)
        self.assertNotIn("MUZIK",codes)

    def test_native_units_and_pdp_do_not_fallback_to_rpt(self):
        unit=self.client.get("/api/options?kind=units&year=2&subject=ARAB")
        self.assertEqual(unit.status_code,200,unit.get_json())
        self.assertEqual(unit.get_json()[0]["value"],"u01")
        lesson=self.client.get(
            "/api/options?kind=pdp&year=2&subject=ARAB&unit=u01")
        self.assertEqual(lesson.status_code,200,lesson.get_json())
        self.assertEqual(lesson.get_json()[0]["formats"],["word"])
        self.lessons.assert_called_once_with(2,"ARAB","u01")
        self.lessons.side_effect=NativeRPHUnavailable("unavailable")
        unavailable=self.client.get(
            "/api/options?kind=pdp&year=2&subject=ARAB&unit=u01")
        self.assertEqual(unavailable.status_code,503,unavailable.get_json())
        self.assertEqual(unavailable.get_json()["code"],
                         "TELEGRAM_OTHER_DRAFT_SOURCE_UNAVAILABLE")


if __name__=="__main__":
    unittest.main()
