"""Regression tests: diagnostic T1 must not leak files or claim missing downloads."""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from web import diagnostik_tahun1_resources as resources


class DiagnosticYearOneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.body = b"%PDF-1.4\nCikguLaju test resource\n"
        self.item = {
            "id": "bm",
            "label": "Bahasa Melayu",
            "file": "bm.pdf",
            "mime": "application/pdf",
            "pages": 1,
            "size_bytes": len(self.body),
            "sha256": hashlib.sha256(self.body).hexdigest(),
        }
        self.manifest = {
            "package_id": "CIKGULAJU-AI-T1-DIAG-2027",
            "label": "Ujian Diagnostik Tahun 1",
            "notice": "Bukan saringan kemasukan",
            "items": [self.item],
        }
        self.root_patch = patch.object(resources, "_asset_root", return_value=self.root)
        self.manifest_patch = patch.object(
            resources, "_manifest", return_value=self.manifest
        )
        self.root_patch.start()
        self.manifest_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.manifest_patch.stop)

    def _client(self, permitted=True):
        app = Flask(__name__)
        app.testing = True
        app.register_blueprint(
            resources.create_blueprint(lambda: permitted)
        )
        return app.test_client()

    def test_missing_file_is_not_offered_for_download(self):
        client = self._client()
        with patch.dict(
            os.environ, {"CIKGULAJU_T1_DIAGNOSTIK_ENABLED": "1"}
        ):
            result = client.get("/bahan/diagnostik/tahun-1")
            self.assertEqual(result.status_code, 200)
            item = result.json["items"][0]
            self.assertEqual(item["status"], "akan_datang")
            self.assertNotIn("download_url", item)
            self.assertEqual(
                client.get("/bahan/diagnostik/tahun-1/download/bm").status_code,
                404,
            )

    def test_verified_resource_downloads_with_auth(self):
        (self.root / "bm.pdf").write_bytes(self.body)
        client = self._client()
        with patch.dict(
            os.environ, {"CIKGULAJU_T1_DIAGNOSTIK_ENABLED": "1"}
        ):
            data = client.get("/bahan/diagnostik/tahun-1").json
            self.assertEqual(data["items"][0]["status"], "ready")
            self.assertIn("download_url", data["items"][0])
            response = client.get("/bahan/diagnostik/tahun-1/download/bm")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, self.body)
            self.assertIn("attachment", response.headers["Content-Disposition"])
            self.assertEqual(response.headers["Cache-Control"], "private, no-store")

    def test_denies_anonymous_and_disabled_requests(self):
        (self.root / "bm.pdf").write_bytes(self.body)
        with patch.dict(
            os.environ, {"CIKGULAJU_T1_DIAGNOSTIK_ENABLED": "1"}
        ):
            client = self._client(permitted=False)
            self.assertEqual(
                client.get("/bahan/diagnostik/tahun-1").status_code, 403
            )
            self.assertEqual(
                client.get("/bahan/diagnostik/tahun-1/download/bm").status_code,
                403,
            )
        with patch.dict(
            os.environ, {"CIKGULAJU_T1_DIAGNOSTIK_ENABLED": "0"}
        ):
            self.assertEqual(
                self._client().get("/bahan/diagnostik/tahun-1").status_code,
                404,
            )

    def test_changed_file_is_never_marked_ready(self):
        (self.root / "bm.pdf").write_bytes(self.body + b"x")
        self.assertIsNone(resources._verified_path(self.item, self.root))
        bad = dict(self.item, file="../other.pdf")
        self.assertIsNone(resources._verified_path(bad, self.root))
        self.assertEqual(resources.catalogue()["items"][0]["status"], "akan_datang")


if __name__ == "__main__":
    unittest.main()
