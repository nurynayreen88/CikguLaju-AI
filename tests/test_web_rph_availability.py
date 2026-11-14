"""RPH readiness is checked before showing native Word/PDF buttons."""
from io import BytesIO
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
    def test_unapproved_year5_is_not_misrepresented_as_telegram_rph(self, *_):
        row = source_records(5, "ENGLISH")[0]
        query = {"year":5, "subject":"ENGLISH", "unit":row["unit"], "lesson":row["token"]}
        response = self.client.get("/api/web/rph/availability", query_string=query)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["code"], "TELEGRAM_RPH_PARITY_NOT_READY")

    @patch("web.native_telegram_sequence_rph_client._read",
           return_value={"available": True, "formats": ["word", "pdf"]})
    @patch("web.unified_rph_web._has_paid_access", return_value=False)
    @patch("web.unified_rph_web._account", return_value=(
        {"authenticated": True, "telegram_user_id": 123, "free_remaining": 10}, None))
    def test_dlp_download_passes_exact_source_and_existing_credit_gate(self, _account, paid, read):
        from web.native_telegram_sequence_rph_client import NativeRPHUnavailable

        query = {"year": 2, "subject": "SCIENCE_DLP", "unit": "10", "lesson": "DLP-SCI-Y2-U10-06"}
        status = self.client.get("/api/web/rph/availability", query_string=query)
        self.assertEqual(status.json, {"available": True, "generator": "telegram-native",
                                       "download_allowed": True, "access_status": "trial",
                                       "formats": ["word", "pdf"]})
        read.assert_called_once_with("availability", query, stream="dlp")
        for invalid in ({"year": 3}, {"unit": "09"}, {"subject": "MATH_DLP"}):
            self.assertEqual(self.client.get("/api/web/rph/pdf",
                                             query_string=query | invalid).status_code, 400)
        self.assertEqual(self.client.get("/api/web/rph/preview", query_string=query).status_code, 404)
        payload = b"%PDF-" + b" " * 1500
        with (
            patch("web.unified_rph_web._fill_roster_count"),
            patch("web.native_telegram_sequence_rph_client.request_dlp_rph",
                  side_effect=[BytesIO(payload), NativeRPHUnavailable(), BytesIO(payload)]) as render,
            patch("web_v1_telegram_auth_routes._config", return_value={
                "account_backend": "supabase", "supabase_url": "https://example.invalid",
                "supabase_key": "fake-key"}),
            patch("web.rph_delivery_quota.authorize_rendered_document",
                  return_value={"allowed": True, "remaining": 9}) as debit,
        ):
            pdf = self.client.post("/api/web/rph/pdf", query_string=query | {"teacher_class": "2 Bestari"},
                                   json={"reflection": "Review the model next lesson."})
            self.assertEqual(pdf.status_code, 200, pdf.get_json(silent=True))
            self.assertEqual(pdf.data, payload)
            self.assertEqual(pdf.headers["X-RPH-Trial-Remaining"], "9")
            self.assertIn("CIKGULAJU_RPH_DLP-SCI-Y2-U10-06.pdf", pdf.headers["Content-Disposition"])
            selection, fmt = render.call_args.args
            self.assertEqual(fmt, "pdf")
            self.assertEqual(selection, query | {
                "source": "telegram-dlp-year2",
                "teacher": {"class": "2 Bestari", "date": "", "time": "", "students": "",
                            "reflection": "Review the model next lesson."},
            })
            self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=query).status_code, 503)
            debit.assert_called_once()
            paid.return_value = True
            self.assertEqual(self.client.get("/api/web/rph/pdf", query_string=query).status_code, 200)
            debit.assert_called_once()

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
