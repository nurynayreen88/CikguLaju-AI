"""RPH readiness is checked before showing native Word/PDF buttons."""
from pathlib import Path
import unittest
from unittest.mock import patch

from flask import Flask
from web.unified_rph_web import create_blueprint, source_records

ROOT = Path(__file__).resolve().parents[1]


class ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        cls.client = app.test_client()
        cls.row = source_records(4, "ENGLISH")[0]
        cls.query = {"year": 4, "subject": "ENGLISH",
                     "unit": cls.row["unit"], "lesson": cls.row["token"]}

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":123}, None))
    def test_readiness_has_no_rph_content_or_private_data(self, *_):
        response = self.client.get("/api/web/rph/availability", query_string=self.query)
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json(), {"available": True, "generator": "telegram-native",
                                              "download_allowed": True,
                                              "access_status": "paid"})
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertNotIn(b"telegram_layout", response.data)
        self.assertNotIn(b"teacher", response.data)
        self.assertNotIn(b"activity", response.data)

    @patch("web.unified_rph_web._has_paid_access", return_value=False)
    @patch("web.unified_rph_web._account", return_value=(
        {"authenticated":True,"telegram_user_id":123,"free_remaining":0},None))
    def test_readiness_distinguishes_source_from_exhausted_trial(self, *_):
        response = self.client.get("/api/web/rph/availability", query_string=self.query)
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json(), {
            "available": True, "generator": "telegram-native",
            "download_allowed": False, "access_status": "exhausted"})
        # Native Word/PDF remain gated; a read-only check spends zero credits.
        with patch("web.native_telegram_rph_client.request_native_rph") as renderer:
            word = self.client.get("/api/web/rph/word", query_string=self.query)
        self.assertEqual(word.status_code, 403)
        self.assertEqual(word.get_json()["code"], "FREE_TRIAL_EXHAUSTED")
        renderer.assert_not_called()

    @patch("web.unified_rph_web._has_paid_access", return_value=False)
    @patch("web.unified_rph_web._account", return_value=(
        {"authenticated":True,"telegram_user_id":123,"free_remaining":5},None))
    def test_readiness_allows_existing_trial_but_never_consumes_it(self, *_):
        response = self.client.get("/api/web/rph/availability", query_string=self.query)
        self.assertEqual(response.status_code,200,response.get_json())
        self.assertEqual(response.get_json(),{"available":True,"generator":"telegram-native",
                                              "download_allowed":True,"access_status":"trial"})

    @patch("web.unified_rph_web._account", return_value=(None, ({"error":"login"},401)))
    def test_readiness_rejects_anonymous(self, *_):
        response = self.client.get("/api/web/rph/availability", query_string=self.query)
        self.assertEqual(response.status_code, 401)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":123}, None))
    def test_readiness_does_not_invent_missing_subject(self, *_):
        q=dict(self.query)
        q["subject"]="BM"
        response=self.client.get("/api/web/rph/availability", query_string=q)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "TELEGRAM_NATIVE_BM_RPH_NOT_READY")

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":123}, None))
    @patch("web.english_y5_standalone_runtime.approved_for_telegram", return_value=False)
    def test_year5_availability_distinguishes_audited_draft_from_held_lessons(self, *_):
        row, held = source_records(5, "ENGLISH")[:2]
        query = {"year":5, "subject":"ENGLISH", "unit":row["unit"], "lesson":row["token"]}
        response = self.client.get("/api/web/rph/availability", query_string=query)
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["status"], "DRAF UNTUK SEMAKAN GURU")
        self.assertEqual(response.get_json()["formats"], ["word", "pdf"])
        with patch("web.english_y5_standalone_runtime.verified_draft_for_web", return_value=False):
            response = self.client.get("/api/web/rph/availability",
                                       query_string={**query, "unit": held["unit"], "lesson": held["token"]})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "TELEGRAM_RPH_PARITY_NOT_READY")

    @patch("web.unified_rph_web._account", return_value=(
        {"authenticated": True, "telegram_user_id": 123, "free_remaining": 10}, None))
    def test_all_year5_lessons_offer_word_and_pdf_to_a_signed_in_teacher(self, *_):
        rows = source_records(5, "ENGLISH")
        self.assertEqual([row["lesson"] for row in rows], list(range(1, 161)))
        for row in rows:
            with self.subTest(lesson=row["lesson"]):
                response = self.client.get("/api/web/rph/availability", query_string={
                    "year": 5, "subject": "ENGLISH", "unit": row["unit"], "lesson": row["token"],
                })
                self.assertEqual(response.status_code, 200, response.get_json())
                self.assertTrue(response.get_json()["download_allowed"])
                self.assertEqual(response.get_json()["formats"], ["word", "pdf"])

    def test_browser_hides_download_until_verified_and_shows_failures(self):
        page=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        self.assertIn('async function checkRphAvailability()', page)
        self.assertIn('/api/web/rph/availability?', page)
        self.assertIn('verifiedRphKey===currentRphLessonKey()', page)
        self.assertIn('if(currentRphLessonKey()!==selectedKey)return;', page)
        self.assertIn('void checkRphAvailability();', page)
        self.assertIn('generateRphFile("word")', page)
        self.assertIn('generateRphFile("pdf")', page)
        self.assertIn('body.download_allowed===false', page)
        self.assertIn('Akses diperlukan', page)
        self.assertIn('RPH disahkan ada dalam Telegram', page)
        self.assertNotIn('id="rph-preview-panel"', page)
        # Error messages remain visible even when unavailable RPH actions are hidden.
        status=page.index('id="rph-download-status"')
        actions=page.index('id="rph-download-actions"')
        self.assertGreater(status, actions)
        self.assertIn('</div><p id="rph-download-status"', page)


if __name__ == "__main__":
    unittest.main()
