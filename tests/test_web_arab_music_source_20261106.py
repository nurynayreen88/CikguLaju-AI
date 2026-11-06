"""Draft Arabic/Music Web: no fake sources, no unapproved PDF/audio, no quota bypass."""
import io
import unittest
from unittest.mock import patch

from flask import Flask

from web.unified_rph_web import create_blueprint
from web.native_telegram_other_draft_client import (
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

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=("word",))
    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":55},None))
    def test_arab_source_availability_shows_draft_word_only(self,*_):
        result=self.client.get("/api/web/rph/availability",query_string=self.query)
        self.assertEqual(result.status_code,200,result.get_json())
        self.assertEqual(result.get_json()["status"],"DRAF UNTUK SEMAKAN GURU")
        self.assertEqual(result.get_json()["formats"],["word"])
        self.assertEqual(result.get_json()["download_allowed"],True)

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=("word",))
    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":55},None))
    def test_arab_pdf_denied_before_native_renderer(self,*_):
        with patch("web.native_telegram_other_draft_client.request_draft_rph") as render:
            result=self.client.get("/api/web/rph/pdf",query_string=self.query)
        self.assertEqual(result.status_code,503,result.get_json())
        self.assertEqual(result.get_json()["code"],"DRAFT_RPH_FORMAT_NOT_VERIFIED")
        render.assert_not_called()

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=("word",))
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

    @patch("web.native_telegram_other_draft_client.draft_available",return_value=("word","pdf"))
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
                     "DRAF tersedia melalui sumber Telegram",
                     "Format belum disahkan"):
            self.assertIn(text,page)


if __name__=="__main__":
    unittest.main()
