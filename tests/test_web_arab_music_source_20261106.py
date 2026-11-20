"""Draft Arabic/Music Web: no fake sources, no unapproved PDF/audio, no quota bypass."""
import io
import unittest
from unittest.mock import patch

from flask import Flask

from web.unified_rph_web import create_blueprint
from web.native_telegram_other_draft_client import (
    NativeRPHUnavailable,
    _check, list_draft_units, list_draft_lessons, draft_available,
)


class DraftWebQA(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        self.client=app.test_client()
        self.query={"year":"2","subject":"ARAB","unit":"u01","lesson":"001"}

    def test_source_identity_strict(self):
        self.assertTrue(_check(2,"ARAB","u01","001"))
        self.assertTrue(_check(4,"MUZIK","u12","035"))
        for y,subject,u,lesson in (
            (1,"ARAB","u01","001"),
            (4,"ARAB","u01","999"),
            (2,"MUZIK","u01","036"),
            (2,"ARAB","../xx","001"),
            (2,"MUZIK","u00","001"),
        ):
            with self.subTest(year=y,subject=subject),self.assertRaises(ValueError):
                _check(y,subject,u,lesson)

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=(("word",), "DRAF"))
    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":55},None))
    def test_arab_source_availability_shows_draft_word_only(self,*_):
        result=self.client.get("/api/web/rph/availability",query_string=self.query)
        self.assertEqual(result.status_code,200,result.get_json())
        self.assertEqual(result.get_json()["status"],"DRAF UNTUK SEMAKAN GURU")
        self.assertEqual(result.get_json()["formats"],["word"])
        self.assertEqual(result.get_json()["download_allowed"],True)

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=(("word",), "DRAF"))
    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":55},None))
    def test_arab_pdf_denied_before_native_renderer(self,*_):
        with patch("web.native_telegram_other_draft_client.request_draft_rph") as render:
            result=self.client.get("/api/web/rph/pdf",query_string=self.query)
        self.assertEqual(result.status_code,503,result.get_json())
        self.assertEqual(result.get_json()["code"],"DRAFT_RPH_FORMAT_NOT_VERIFIED")
        render.assert_not_called()

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=(("word",), "DRAF"))
    @patch("web.unified_rph_web._has_paid_access",return_value=False)
    @patch("web.unified_rph_web._account",return_value=(
        {"telegram_user_id":55,"free_remaining":0},None))
    def test_arab_preview_draft_no_trial_quota_bypass(self,*_):
        read=self.client.get("/api/web/rph/availability",query_string=self.query)
        self.assertEqual(read.status_code,200,read.get_json())
        self.assertEqual(read.get_json()["access_status"],"exhausted")
        self.assertFalse(read.get_json()["download_allowed"])
        with patch("web.native_telegram_other_draft_client.request_draft_rph") as render:
            word=self.client.get("/api/web/rph/word",query_string=self.query)
        self.assertEqual(word.status_code,403,word.get_json())
        self.assertEqual(word.get_json()["code"],"FREE_TRIAL_EXHAUSTED")
        render.assert_not_called()

    @patch("web.unified_rph_web._has_paid_access", return_value=False)
    @patch("web.unified_rph_web._account")
    @patch("web.native_telegram_other_draft_client._read")
    def test_arab_year3_recordings_use_reviewed_pdp_and_trial_access(self, read, account, _):
        account.return_value = ({"telegram_user_id": 55, "free_remaining": 1}, None)
        read.return_value = {"available": True, "generator": "telegram-native",
                             "status": "READY", "formats": ["word"]}
        path = "/api/web/rph/extra-materials"
        base = {**self.query, "year": 3}
        for unit, lesson, video_ids in (
            ("u01", "010", ("3cfsR_2ADTU",)),
            ("u02", "028", ("v5e3wECmYDo",)),
            ("u03", "043", ("QKsDg28oO14",)),
            ("u04", "052", ("GLi9tLRQMw0", "bfU1oW4-VsQ")),
            ("u04", "054", ("GLi9tLRQMw0",)),
        ):
            query = {**base, "unit": unit, "lesson": lesson}
            response = self.client.get(path, query_string=query)
            self.assertEqual(response.status_code, 200, response.json)
            items = response.json["items"]
            self.assertEqual(response.json["status"], "PAUTAN_RAKAMAN")
            if unit == "u04":
                audio = items.pop(0)
                self.assertEqual((audio["type"], audio["action"]), ("audio", "Muat Turun Audio"))
                self.assertEqual(audio["url"], "https://drive.usercontent.google.com/download?"
                                 "id=1MNsCyjEiy7tK1eu0O4H4xJioEQf0b2Qq&export=download&confirm=t")
            for video, video_id in zip(items, video_ids, strict=True):
                self.assertEqual((video["type"], video["action"]), ("video", "Mainkan Rakaman"))
                self.assertEqual(video["url"], "https://www.youtube.com/watch?v=" + video_id)
            read.assert_called_with("availability", query, opener=None)

        read.reset_mock()
        for overrides in ({"year": 2}, {"unit": "u03"}, {"lesson": "053"}, {"lesson": "059"}):
            self.assertEqual(self.client.get(path, query_string={**query, **overrides}).json["items"], [])
        read.assert_not_called()
        read.side_effect = NativeRPHUnavailable("source offline")
        self.assertEqual(self.client.get(path, query_string=query).status_code, 503)
        read.reset_mock()
        account.return_value = ({"telegram_user_id": 55, "free_remaining": 0}, None)
        blocked = self.client.get(path, query_string=query)
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.json["code"], "FREE_TRIAL_EXHAUSTED")
        read.assert_not_called()

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=(("word","pdf"), "DRAF"))
    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":55},None))
    def test_music_native_word_download(self,*_):
        query={"year":"2","subject":"MUZIK","unit":"u01","lesson":"001"}
        fake=io.BytesIO(b"PK\x03\x04"+b"source"*250)
        with patch("web.native_telegram_other_draft_client.request_draft_rph",
                   return_value=fake) as native:
            result=self.client.get("/api/web/rph/word",query_string=query)
        self.assertEqual(result.status_code,200,result.get_json() if result.is_json else result.data[:60])
        self.assertEqual(result.headers["X-RPH-Generator"],"telegram-native")
        native.assert_called_once()
        self.assertEqual(native.call_args.args[0]["source"],"telegram-provisional-subjects-2027")
        self.assertEqual(native.call_args.args[0]["lesson"],"001")

    def test_browser_labels_and_format_gates(self):
        from pathlib import Path
        page=(Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"index.html").read_text("utf8")
        for text in ("ARAB:", "MUZIK:", "SEJARAH:",
                     "verifiedRphFormats.includes(\"pdf\")",
                     "verifiedRphFormats.includes(\"word\")",
                     "RPH tersedia. Kandungan masih dalam semakan.",
                     "(Dalam semakan)", "(belum disahkan)",
                     "Tiada format RPH disahkan untuk PdP ini."):
            self.assertIn(text,page)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":55}, None))
    @patch("web.native_telegram_other_draft_client._read")
    def test_only_reviewed_arabic_choices_can_be_ready(self, read, *_):
        for year, unit, pdps in (
            (2, "u01", range(1, 13)),
            (2, "u02", range(13, 29)),
            (2, "u03", range(29, 45)),
            (2, "u04", range(45, 61)),
            (3, "u01", range(1, 13)),
            (3, "u02", range(13, 29)),
            (3, "u03", range(29, 45)),
            (3, "u04", range(45, 61)),
        ):
            ready = [
                {"value": f"{pdp:03d}", "label": f"PdP {pdp:03d} — اللغة العربية",
                 "status": "READY", "formats": ["word"]}
                for pdp in pdps
            ]
            read.return_value = {"source": "telegram-provisional-subjects-2027-v1",
                                 "status": "DRAF", "items": ready}
            self.assertEqual(list_draft_lessons(year, "ARAB", unit), ready)
            with self.assertRaises(NativeRPHUnavailable):
                list_draft_lessons(4, "ARAB", unit)

            read.return_value = {"available": True, "generator": "telegram-native",
                                 "status": "READY", "formats": ["word"]}
            for item in ready:
                result = self.client.get("/api/web/rph/availability", query_string={
                    **self.query, "year": year, "unit": unit, "lesson": item["value"],
                })
                self.assertEqual(result.get_json()["status"], "READY")
                self.assertEqual(result.get_json()["formats"], ["word"])
        for unit, lesson in (("u01", "013"), ("u01", "018"), ("u02", "029"), ("u03", "045"), ("u04", "044"), ("u04", "061")):
            result = self.client.get("/api/web/rph/availability",
                                     query_string={**self.query, "unit": unit, "lesson": lesson})
            self.assertEqual(result.status_code, 503)
        for unit, lesson in (("u01", "013"), ("u02", "001"), ("u02", "029"), ("u03", "045"), ("u04", "044"), ("u04", "061")):
            result = self.client.get("/api/web/rph/availability", query_string={
                **self.query, "year": 3, "unit": unit, "lesson": lesson,
            })
            self.assertEqual(result.status_code, 503)


if __name__=="__main__":
    unittest.main()
