"""Regression for one-click direct native Web RPH Word/PDF without preview."""
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from web.unified_rph_web import create_blueprint, source_records, _docx

ROOT = Path(__file__).resolve().parents[1]

class OneClickPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        cls.client = app.test_client()
        cls.native_fake = patch("web.native_telegram_rph_client.request_native_rph",
            side_effect=lambda selected, fmt: _docx(selected))
        cls.native_fake.start()
        cls.addClassCleanup(cls.native_fake.stop)

    def test_form_allows_immediate_preview_without_teacher_details(self):
        html = (ROOT / "web_v1_static_preview" / "index.html").read_text(encoding="utf8")
        self.assertLess(html.index('id="lesson"'), html.index('id="teacher-info"'))
        self.assertLess(html.index('id="teacher-info"'), html.index('id="rph-download-actions"'))
        self.assertNotIn('id="rph-preview-button"', html)
        self.assertNotIn('id="rph-preview-panel"', html)
        self.assertIn('id="rph-word"', html)
        self.assertIn('id="rph-pdf"', html)
        self.assertNotIn('id="teacher-class" type="text" autocomplete="off" maxlength="40" placeholder="Contoh: 4 Bestari" required', html)
        self.assertNotIn('id="teacher-date" type="date" required', html)
        self.assertNotIn('id="teacher-time" type="time" required', html)
        self.assertIn('if(!teacherClass.checkValidity()||!teacherDate.checkValidity()||', html)
        self.assertIn('!teacherTimeStart.checkValidity()||!teacherTimeEnd.checkValidity()', html)
        self.assertNotIn('if(!teacherClass.value.trim()||!teacherDate.value||!teacherTime.value', html)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_source_backed_paid_preview_then_word_without_metadata(self, *_):
        row = source_records(6, "ENGLISH")[0]
        args = {"year":6,"subject":"ENGLISH","unit":row["unit"],"lesson":row["token"]}
        response = self.client.get("/api/web/rph/preview", query_string=args)
        self.assertEqual(response.status_code, 200, response.get_json())
        payload=response.get_json()
        self.assertEqual(payload["selection"],row["token"])
        self.assertEqual(payload["teacher"],{"class":"","date":"","time":"","students":""})
        doc=self.client.get("/api/web/rph/word",query_string=args)
        self.assertEqual(doc.status_code,200)
        self.assertTrue(doc.data.startswith(b"PK"))

    @patch("web.unified_rph_web._account", return_value=(None, ({"error":"login required"}, 401)))
    def test_anonymous_users_cannot_preview(self, *_):
        self.assertEqual(self.client.get("/api/web/rph/preview").status_code,401)

if __name__ == "__main__":
    unittest.main()
