"""Tests for the read-only database file format detector."""
import tempfile
import unittest
from pathlib import Path
from tools.detect_web_v1_database import detect_local_database_file


class DatabaseDetectionTests(unittest.TestCase):
    def test_sqlite_header(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "db"
            path.write_bytes(b"SQLite format 3\x00" + b"\x00" * 100)
            self.assertEqual(detect_local_database_file(path), "sqlite3")

    def test_unknown_header(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "other"
            path.write_bytes(b"not a database")
            self.assertEqual(detect_local_database_file(path), "unknown")

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                detect_local_database_file(Path(d) / "missing")


if __name__ == "__main__":
    unittest.main()
