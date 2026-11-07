"""Isolated Web staging RPT 2027 tests: no Telegram import, no user DB writes."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask, jsonify

from web.rpt_2027_all_http import SUBJECTS, YEARS, create_all_rpt_blueprint, pdf_path, pdf_ready


class AllSubjectRPTTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.app = Flask(__name__)
        self.app.register_blueprint(create_all_rpt_blueprint(root=self.root))
        self.client = self.app.test_client()
        target = pdf_path("bahasa_melayu", 2, root=self.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"%PDF-" + b"x" * 9000)

    def tearDown(self):
        self.tmp.cleanup()

    def test_year_and_subject_inventory_is_explicit(self):
        self.assertEqual(set(SUBJECTS), {
            "english", "bahasa_melayu", "matematik", "sains",
            "pendidikan_islam", "pjpk", "pendidikan_moral", "psv",
            "bahasa_arab", "muzik", "rbt", "sejarah",
        })
        self.assertEqual(YEARS, (2, 3, 4, 5, 6))
        self.assertTrue(pdf_ready("bahasa_melayu", 2, root=self.root))
        self.assertFalse(pdf_ready("bahasa_melayu", 3, root=self.root))
        self.assertFalse(pdf_ready("sains", 2, root=self.root))
        self.assertFalse(pdf_ready("../private", 2, root=self.root))

    @patch("web.rpt_2027_all_http._has_paid_access", return_value=False)
    @patch("web.rpt_2027_all_http._account", return_value=({"authenticated": True}, None))
    def test_free_user_sees_catalog_but_cannot_download(self, *_mocks):
        r = self.client.get("/api/rpt/2027/catalog")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(len(data["subjects"]), 12)
        self.assertEqual(data["total_rpt"], 56)
        bm = next(s for s in data["subjects"] if s["code"] == "bahasa_melayu")
        self.assertTrue(bm["years"][0]["pdf_ready"])
        self.assertFalse(bm["years"][0]["download_enabled"])
        download = self.client.get("/api/rpt/2027/all/bahasa_melayu/2.pdf")
        self.assertEqual(download.status_code, 403)

    @patch("web.rpt_2027_all_http._has_paid_access", return_value=True)
    @patch("web.rpt_2027_all_http._account", return_value=({"authenticated": True}, None))
    def test_paid_exact_pdf_only_and_no_fallback(self, *_mocks):
        r = self.client.get("/api/rpt/2027/all/bahasa_melayu/2.pdf")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "application/pdf")
        self.assertEqual(r.data[:5], b"%PDF-")
        self.assertEqual(r.headers["Cache-Control"], "no-store, private")
        self.assertIn("attachment", r.headers["Content-Disposition"])
        self.assertEqual(self.client.get("/api/rpt/2027/all/bahasa_melayu/3.pdf").status_code, 503)
        self.assertEqual(self.client.get("/api/rpt/2027/all/sains/2.pdf").status_code, 503)
        self.assertEqual(self.client.get("/api/rpt/2027/all/not-a-subject/2.pdf").status_code, 404)
        self.assertEqual(self.client.get("/api/rpt/2027/all/bahasa_melayu/1.pdf").status_code, 404)

    @patch("web.rpt_2027_all_http._has_paid_access", return_value=True)
    @patch("web.rpt_2027_all_http._account", return_value=({"authenticated": True}, None))
    def test_bad_pdf_and_symlink_fail_closed(self, *_mocks):
        wrong = pdf_path("matematik", 2, root=self.root)
        wrong.parent.mkdir(parents=True, exist_ok=True)
        wrong.write_bytes(b"%PDX-" + b"x" * 9000)
        self.assertFalse(pdf_ready("matematik", 2, root=self.root))
        self.assertEqual(self.client.get("/api/rpt/2027/all/matematik/2.pdf").status_code, 503)
        wrong.unlink()
        wrong.symlink_to(pdf_path("bahasa_melayu", 2, root=self.root))
        self.assertFalse(pdf_ready("matematik", 2, root=self.root))

    def test_catalog_requires_login(self):
        def unauthenticated():
            return None, (jsonify({"error": "Authentication required"}), 401)
        with patch("web.rpt_2027_all_http._account", side_effect=unauthenticated):
            self.assertEqual(self.client.get("/api/rpt/2027/catalog").status_code, 401)
            self.assertEqual(self.client.get("/api/rpt/2027/all/english/2.pdf").status_code, 401)


if __name__ == "__main__":
    unittest.main()
