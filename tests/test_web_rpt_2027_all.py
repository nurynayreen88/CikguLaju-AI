"""Isolated Web staging RPT 2027 tests: no Telegram import, no user DB writes."""
from hashlib import sha256
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

    @patch("web.rpt_2027_all_http._has_paid_access", return_value=True)
    @patch("web.rpt_2027_all_http._account", return_value=({"authenticated": True}, None))
    def test_approved_rpt_uses_aligned_pdf_and_signed_cover_source(self, *_mocks):
        root = Path(__file__).resolve().parents[1] / "rpt_2027"
        app = Flask(__name__)
        app.register_blueprint(create_all_rpt_blueprint(root=root))
        client = app.test_client()
        from json import loads

        config = loads((root / "web_2027_pdfs/original_cover_layout_verified.json").read_text())
        layouts = config["science_year6_covers"] | config["aligned_rpt_covers"]
        catalog = client.get("/api/rpt/2027/catalog").get_json()
        for subject, year in (("matematik_dpk", 2), ("matematik_dpk", 3),
                              ("sains", 5), ("sains", 6), ("science_dlp", 5),
                              ("mathematics_dlp", 5), ("science_dlp", 6), ("mathematics_dlp", 6)):
            with self.subTest(subject=subject, year=year):
                choice = next(item for item in catalog["subjects"] if item["code"] == subject)
                entry = next(item for item in choice["years"] if item["year"] == year)
                self.assertEqual(entry["status"], "TERSEDIA")
                self.assertFalse(entry["is_draft"])
                response = client.get(f"/api/rpt/2027/all/{subject}/{year}.pdf")
                self.addCleanup(response.close)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("DRAF", response.headers["Content-Disposition"].upper())
                digest = sha256(response.data).hexdigest()
                self.assertEqual(response.headers["X-RPT-Source-SHA256"], digest)
                self.assertEqual(response.headers["X-RPT-Personalization-Allowed"], "1")
                layout = layouts[f"{subject}:{year}"]
                self.assertEqual(layout["source_sha256_by_subject_year"], {f"{subject}:{year}": digest})

    @patch("web.rpt_2027_all_http._has_paid_access", return_value=False)
    @patch("web.rpt_2027_all_http._account", return_value=({"authenticated": True}, None))
    def test_free_user_sees_catalog_and_downloads_without_cover(self, *_mocks):
        r = self.client.get("/api/rpt/2027/catalog")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(len(data["subjects"]), 17)
        iban = next(s for s in data["subjects"] if s["code"] == "bahasa_iban")
        self.assertEqual([item["year"] for item in iban["years"]], list(YEARS))
        self.assertTrue(all(item["coming_soon"] and not item["download_enabled"]
                            and not item["pdf_ready"] for item in iban["years"]))
        self.assertEqual(data["total_rpt"], 56)
        bm = next(s for s in data["subjects"] if s["code"] == "bahasa_melayu")
        by_year={r["year"]:r for r in bm["years"]}
        self.assertFalse(by_year[1]["pdf_ready"])
        self.assertFalse(by_year[1]["download_enabled"])
        self.assertIn("KP2027",by_year[1]["status"])
        self.assertTrue(by_year[2]["pdf_ready"])
        self.assertTrue(by_year[2]["download_enabled"])
        self.assertTrue(data["allowed"])
        self.assertFalse(data["personalization_allowed"])
        download = self.client.get("/api/rpt/2027/all/bahasa_melayu/2.pdf")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.headers["X-RPT-Personalization-Allowed"],"0")
        self.assertEqual(download.data,b"%PDF-"+b"x"*9000)
        self.assertEqual(download.headers["X-RPT-Source-SHA256"], sha256(download.data).hexdigest())

    @patch("web.rpt_2027_all_http._has_paid_access", return_value=True)
    @patch("web.rpt_2027_all_http._account", return_value=({"authenticated": True}, None))
    def test_paid_exact_pdf_only_and_no_fallback(self, *_mocks):
        # A valid legacy PDF remains downloadable; unverified cover is never stamped.
        original=pdf_path("bahasa_melayu",2,root=self.root).read_bytes()
        fallback=self.client.get("/api/rpt/2027/all/bahasa_melayu/2.pdf")
        self.assertEqual(fallback.status_code, 200)
        self.assertEqual(fallback.data, original)
        self.assertEqual(fallback.headers["X-RPT-Source-SHA256"], sha256(original).hexdigest())
        self.assertEqual(fallback.headers["X-RPT-Personalization-Allowed"], "1")
        self.assertEqual(fallback.headers["X-RPT-Cover-Status"], "unverified")
        import json
        layout=self.root/"web_2027_pdfs"/"original_cover_layout_verified.json"
        layout.parent.mkdir(parents=True,exist_ok=True)
        layout.write_text(json.dumps({"source_sha256_by_subject_year":{"bahasa_melayu:2":sha256(original).hexdigest()}}))
        r = self.client.get("/api/rpt/2027/all/bahasa_melayu/2.pdf")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "application/pdf")
        self.assertEqual(r.data, original)
        self.assertEqual(r.headers["X-RPT-Source-SHA256"], sha256(original).hexdigest())
        self.assertEqual(r.headers["Cache-Control"], "no-store, private")
        self.assertEqual(r.headers["X-RPT-Personalization-Allowed"],"1")
        self.assertNotIn("X-RPT-Cover-Status", r.headers)
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
