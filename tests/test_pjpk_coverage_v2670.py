"""PJPK coverage audit v26.70 tests with a temporary SQLite database."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.audit_pjpk_coverage_v2670 import audit

class CoverageAuditTests(unittest.TestCase):
    def test_verified_and_unverified_rows(self):
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "test.db")
            with sqlite3.connect(path) as con:
                con.executescript("""
                CREATE TABLE rpt_entries (id INTEGER PRIMARY KEY,year_label TEXT,subject TEXT,verified INTEGER,content_verified INTEGER);
                CREATE TABLE rpt_entry_standards (rpt_entry_id INTEGER,standard_type TEXT,standard_code TEXT,standard_text TEXT,verified INTEGER);
                INSERT INTO rpt_entries VALUES (1,'Tahun 1','Pendidikan Jasmani',1,1);
                INSERT INTO rpt_entries VALUES (2,'Tahun 1','Pendidikan Kesihatan',1,0);
                INSERT INTO rpt_entry_standards VALUES (1,'SK','1.1','SK sah',1);
                INSERT INTO rpt_entry_standards VALUES (1,'SP','1.1.1','SP sah',1);
                """)
            result = audit(path)
            self.assertEqual(result["Tahun 1 / Pendidikan Jasmani"]["single_verified_sk_sp"], 1)
            self.assertEqual(result["Tahun 1 / Pendidikan Kesihatan"]["needs_review"], 1)
            self.assertEqual(len(result), 12)

    def test_missing_schema(self):
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "empty.db")
            with sqlite3.connect(path):
                pass
            self.assertIn("error", audit(path))

if __name__ == "__main__":
    unittest.main()
