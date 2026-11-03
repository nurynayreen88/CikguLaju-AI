"""Isolated paid Web RPH read/download contract; zero production app imports."""
import io
import unittest
import zipfile
from unittest.mock import patch
from flask import Flask
from web.english_y6_rph_2027_http import create_blueprint, source_rows


class WebRPHYear6Tests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_blueprint())
        self.client = self.app.test_client()
        self.account={"authenticated":True,"telegram_user_id":123,"rakan_pembangun":True}
        p=patch("web.english_y6_rph_2027_http._account",side_effect=lambda:(self.account,None))
        p.start();self.addCleanup(p.stop)

    def test_146_lesson_objective_from_official_sow(self):
        row=source_rows(1)
        self.assertIn("main idea",row["OBJEKTIF PEMBELAJARAN"])
        self.assertIn("Pupils:",row["AKTIVITI UTAMA"])
        self.assertIn("Main: 3.2.1",row["STANDARD PEMBELAJARAN"])

    def test_paid_can_view_and_download_docx(self):
        page=self.client.get("/api/web/english/year6/rph/1")
        self.assertEqual(page.status_code,200)
        self.assertEqual(page.json["lesson"],1)
        self.assertIn("no-store",page.headers["Cache-Control"])
        downloaded=self.client.get("/api/web/english/year6/rph/1.docx")
        self.assertEqual(downloaded.status_code,200)
        self.assertEqual(downloaded.mimetype,"application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with zipfile.ZipFile(io.BytesIO(downloaded.data)) as z:
            self.assertTrue(z.testzip() is None)
            self.assertIn(b"English",z.read("word/document.xml"))
            self.assertIn(b"main idea",z.read("word/document.xml"))

    def test_teacher_choice_not_labelled_official(self):
        page=self.client.get("/api/web/english/year6/rph/16")
        self.assertEqual(page.status_code,200)
        self.assertTrue(page.json["teacher_selection"])

    def test_free_account_denied_without_consuming_credits(self):
        self.account={"authenticated":True,"telegram_user_id":123,"rakan_pembangun":False,"free_remaining":10}
        self.assertEqual(self.client.get("/api/web/english/year6/rph/1").status_code,403)
        self.assertEqual(self.client.get("/api/web/english/year6/rph/1.docx").status_code,403)
        self.assertEqual(self.account["free_remaining"],10)

    def test_no_unknown_lesson(self):
        self.assertEqual(self.client.get("/api/web/english/year6/rph/161").status_code,404)
        self.assertEqual(self.client.get("/api/web/english/year6/rph/161.docx").status_code,404)

    def test_session_required(self):
        with patch("web.english_y6_rph_2027_http._account",return_value=(None,({"error":"Auth required"},401))):
            self.assertEqual(self.client.get("/api/web/english/year6/rph/1").status_code,401)


if __name__ == "__main__":
    unittest.main()
