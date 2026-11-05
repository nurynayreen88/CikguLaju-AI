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
        self.assertEqual(response.get_json(), {"available": True, "generator": "telegram-native"})
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")
        self.assertNotIn(b"telegram_layout", response.data)
        self.assertNotIn(b"teacher", response.data)
        self.assertNotIn(b"activity", response.data)

    @patch("web.unified_rph_web._has_paid_access", return_value=False)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":123}, None))
    def test_readiness_rejects_unpaid(self, *_):
        response = self.client.get("/api/web/rph/availability", query_string=self.query)
        self.assertEqual(response.status_code, 403)

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
        self.assertEqual(response.get_json()["code"], "RPH_SOURCE_NOT_VERIFIED")

    def test_browser_hides_download_until_verified_and_shows_failures(self):
        page=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        self.assertIn('async function checkRphAvailability()', page)
        self.assertIn('/api/web/rph/availability?', page)
        self.assertIn('verifiedRphKey===currentRphLessonKey()', page)
        self.assertIn('if(currentRphLessonKey()!==selectedKey)return;', page)
        self.assertIn('void checkRphAvailability();', page)
        self.assertIn('generateRphFile("word")', page)
        self.assertIn('generateRphFile("pdf")', page)
        self.assertNotIn('id="rph-preview-panel"', page)
        # Error messages remain visible even when unavailable RPH actions are hidden.
        status=page.index('id="rph-download-status"')
        actions=page.index('id="rph-download-actions"')
        self.assertGreater(status, actions)
        self.assertIn('</div><p id="rph-download-status"', page)


if __name__ == "__main__":
    unittest.main()
