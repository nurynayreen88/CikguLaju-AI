import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from tools.run_web_v1_preview import app


class DatabaseHealthTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_missing_db_is_disconnected(self):
        with patch.dict(os.environ, {"CIKGULAJU_WEB_PREVIEW_DB": "/missing/test.sqlite"}):
            response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.json["database_connected"], False)
        self.assertIs(response.json["generation_enabled"], False)

    def test_invalid_sqlite_file_is_not_connected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "invalid.sqlite")
            with open(path, "wb") as handle:
                handle.write(b"not a sqlite database")
            with patch.dict(os.environ, {"CIKGULAJU_WEB_PREVIEW_DB": path}):
                self.assertIs(self.client.get("/health").json["database_connected"], False)

    def test_valid_sqlite_is_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "test.sqlite")
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
            with patch.dict(os.environ, {"CIKGULAJU_WEB_PREVIEW_DB": path}):
                response = self.client.get("/health")
            self.assertIs(response.json["database_connected"], True)
            self.assertIs(response.json["generation_enabled"], False)


if __name__ == "__main__":
    unittest.main()
