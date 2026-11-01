"""HTTP contract tests for the staging-only RPH endpoint."""
import io
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from docx import Document
from web.approved_rph_reader import RPHLookupConfig
from web.staging_rph_http import create_staging_rph_blueprint


class StagingHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name) / "fixture.sqlite"
        with sqlite3.connect(path) as conn:
            conn.execute(
                "CREATE TABLE rph (lesson_id INTEGER PRIMARY KEY, title TEXT, "
                "content TEXT, approval_status TEXT, approval_ref TEXT)"
            )
            conn.executemany("INSERT INTO rph VALUES (?, ?, ?, ?, ?)", [
                (1, "English Lesson 1", "Pupils practise.", "approved", "review-1"),
                (2, "Draft Lesson", "Unapproved", "draft", ""),
            ])
        config = RPHLookupConfig(
            str(path), "rph", "lesson_id", "title", "content",
            "approval_status", "approved", "approval_ref"
        )
        self.authorized = True
        app = Flask(__name__)
        app.testing = True
        with patch.dict(os.environ, {
            "CIKGULAJU_WEB_RPH_STAGING_ENABLED": "1",
            "CIKGULAJU_ENV": "staging",
        }):
            app.register_blueprint(create_staging_rph_blueprint(
                config, lambda req: self.authorized
            ))
        self.client = app.test_client()

    def test_word_download(self):
        response = self.client.post(
            "/api/staging/rph/generate", json={"lesson_id": 1, "format": "docx"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        document = Document(io.BytesIO(response.data))
        self.assertIn("English Lesson 1", document.paragraphs[0].text)

    def test_pdf_download(self):
        response = self.client.post(
            "/api/staging/rph/generate", json={"lesson_id": 1, "format": "pdf"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(b"%PDF-"))

    def test_unauthorized(self):
        self.authorized = False
        response = self.client.post(
            "/api/staging/rph/generate", json={"lesson_id": 1, "format": "pdf"}
        )
        self.assertEqual(response.status_code, 403)

    def test_draft_not_downloadable(self):
        response = self.client.post(
            "/api/staging/rph/generate", json={"lesson_id": 2, "format": "pdf"}
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_request(self):
        for payload in ({"lesson_id": True, "format": "pdf"},
                        {"lesson_id": 1, "format": "txt"},
                        {"lesson_id": 1, "format": "pdf", "approved": True}):
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/staging/rph/generate", json=payload
                )
                self.assertEqual(response.status_code, 400)

    def test_missing_config_rejected(self):
        with patch.dict(os.environ, {
            "CIKGULAJU_WEB_RPH_STAGING_ENABLED": "1",
            "CIKGULAJU_ENV": "staging",
        }):
            with self.assertRaises(TypeError):
                create_staging_rph_blueprint(None, lambda req: True)

    def test_disabled_outside_staging(self):
        with patch.dict(os.environ, {
            "CIKGULAJU_WEB_RPH_STAGING_ENABLED": "1",
            "CIKGULAJU_ENV": "production",
        }):
            with self.assertRaises(RuntimeError):
                create_staging_rph_blueprint(None, lambda req: True)


if __name__ == "__main__":
    unittest.main()
