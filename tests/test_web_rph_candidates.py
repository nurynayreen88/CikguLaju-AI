"""Check schema candidate discovery without accessing production records."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from web.audit_rph_candidates import candidate_report


class CandidateAuditTests(unittest.TestCase):
    def test_identifies_candidate_tables_without_row_content(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.sqlite"
            with sqlite3.connect(path) as conn:
                conn.execute("CREATE TABLE standalone_rph (lesson_id INTEGER, approval_status TEXT, body TEXT)")
                conn.execute("CREATE TABLE unrelated (id INTEGER, label TEXT)")
                conn.execute(
                    "INSERT INTO standalone_rph VALUES (?, ?, ?)",
                    (1, "draft", "PRIVATE RPH TEXT"),
                )
            result = candidate_report(str(path))
            self.assertEqual(result["integrity"], "ok")
            self.assertEqual(len(result["candidates"]), 1)
            self.assertEqual(result["candidates"][0]["table"], "standalone_rph")
            self.assertNotIn("PRIVATE RPH TEXT", str(result))
            self.assertIn("Manual approval mapping", result["warning"])


if __name__ == "__main__":
    unittest.main()
