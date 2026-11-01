"""Synthetic tests for the read-only approved RPH database adapter.

These do not establish that the production database uses the same schema.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from web.approved_rph_reader import RPHLookupConfig, load_approved_rph


class ApprovedReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "fixture.sqlite"
        with sqlite3.connect(self.db) as conn:
            conn.execute(
                "CREATE TABLE standalone_rph "
                "(lesson_id INTEGER, title TEXT, content TEXT, "
                "approval_status TEXT, approval_ref TEXT)"
            )
            conn.executemany(
                "INSERT INTO standalone_rph VALUES (?, ?, ?, ?, ?)",
                [
                    (1, "Lesson One", "Approved content", "approved", "audit-1"),
                    (2, "Lesson Two", "Draft content", "draft", "audit-2"),
                    (3, "Lesson Three", "", "approved", "audit-3"),
                ],
            )
        self.config = RPHLookupConfig(
            str(self.db), "standalone_rph", "lesson_id", "title",
            "content", "approval_status", "approved", "approval_ref"
        )

    def test_approved_record(self):
        rph = load_approved_rph(self.config, 1)
        self.assertEqual(rph.content, "Approved content")

    def test_draft_rejected(self):
        with self.assertRaises(LookupError):
            load_approved_rph(self.config, 2)

    def test_missing_content_rejected(self):
        with self.assertRaises(LookupError):
            load_approved_rph(self.config, 3)

    def test_unknown_lesson_rejected(self):
        with self.assertRaises(LookupError):
            load_approved_rph(self.config, 99)

    def test_bad_identifier_rejected(self):
        bad = RPHLookupConfig(
            str(self.db), "standalone_rph; DROP TABLE standalone_rph",
            "lesson_id", "title", "content",
            "approval_status", "approved", "approval_ref"
        )
        with self.assertRaises(ValueError):
            load_approved_rph(bad, 1)

    def test_boolean_id_rejected(self):
        with self.assertRaises(ValueError):
            load_approved_rph(self.config, True)


if __name__ == "__main__":
    unittest.main()
