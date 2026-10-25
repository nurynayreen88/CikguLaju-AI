"""PJPK runtime adapter smoke tests against isolated in-memory-shaped temp SQLite files.

No production DB is opened, rebuilt, or mutated.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from scripts.pjpk_v26_16_adapter import ready_pdp

SCHEMA = """CREATE TABLE pjpk_ready_pdp (
 id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
 sequence_no INTEGER, content_verified INTEGER, sequence_verified INTEGER, schedule_verified INTEGER,
 topic TEXT
)"""

class PJPKAdapterSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "fixture.db"
        with sqlite3.connect(self.path) as con:
            con.execute(SCHEMA)
            con.executemany("""INSERT INTO pjpk_ready_pdp
                (id,year_label,subject,sequence_no,content_verified,sequence_verified,schedule_verified,topic)
                VALUES (?,?,?,?,?,?,?,?)""", [
                (1,"Tahun 5","Pendidikan Kesihatan",1,1,1,1,"Existing verified"),
                (2259,"Tahun 5","Pendidikan Kesihatan",2,1,1,0,"Not yet schedule verified"),
                (2260,"Tahun 5","Pendidikan Kesihatan",3,1,0,1,"Not yet sequence verified"),
                (2261,"Tahun 5","Pendidikan Kesihatan",4,0,1,1,"Not yet content verified"),
                (2,"Tahun 4","Pendidikan Kesihatan",1,1,1,1,"Other year"),
                (3,"Tahun 5","Pendidikan Jasmani",1,1,1,1,"Other subject"),
            ])
    def tearDown(self):
        self.temp.cleanup()
    def test_only_fully_verified_rows_are_exposed(self):
        rows = ready_pdp("Tahun 5","Pendidikan Kesihatan",self.path)
        self.assertEqual([r["id"] for r in rows], [1])
    def test_other_subject_year_filtered(self):
        self.assertEqual([r["id"] for r in ready_pdp("Tahun 5","Pendidikan Jasmani",self.path)], [3])
    def test_invalid_year_and_subject_fail_closed(self):
        self.assertEqual(ready_pdp("Tahun 7","Pendidikan Kesihatan",self.path), [])
        self.assertEqual(ready_pdp("Tahun 5","Other",self.path), [])
    def test_t2_unverified_editorial_rows_never_exposed(self):
        from scripts.pjpk_t2_pk_evidence_queue import build
        items = build()
        with sqlite3.connect(self.path) as con:
            con.executemany("""INSERT INTO pjpk_ready_pdp
                (id,year_label,subject,sequence_no,content_verified,sequence_verified,schedule_verified,topic)
                VALUES (?,?,?,?,?,?,?,?)""", [
                (item["entry_id"], "Tahun 2", "Pendidikan Kesihatan", item["entry_id"], 0, 0, 0, item["topic"])
                for item in items
            ])
        self.assertEqual(len(items), 18)
        self.assertEqual(ready_pdp("Tahun 2", "Pendidikan Kesihatan", self.path), [])

    def test_verified_rows_are_ordered_by_lesson_sequence(self):
        with sqlite3.connect(self.path) as con:
            con.execute("""INSERT INTO pjpk_ready_pdp
                (id,year_label,subject,sequence_no,content_verified,sequence_verified,schedule_verified,topic)
                VALUES (?,?,?,?,?,?,?,?)""", (4, "Tahun 5", "Pendidikan Kesihatan", 0, 1, 1, 1, "Earlier lesson"))
        self.assertEqual([r["id"] for r in ready_pdp("Tahun 5", "Pendidikan Kesihatan", self.path)], [4, 1])

    def test_invalid_sqlite_file_fails_closed(self):
        bad = self.path.parent / "invalid.db"
        bad.write_text("not a sqlite database", encoding="utf-8")
        self.assertEqual(ready_pdp("Tahun 5", "Pendidikan Kesihatan", bad), [])

    def test_missing_db_fails_closed(self):
        self.assertEqual(ready_pdp("Tahun 5","Pendidikan Kesihatan",self.path.parent/"missing.db"), [])
    def test_missing_verification_column_fails_closed(self):
        bad = self.path.parent / "bad.db"
        with sqlite3.connect(bad) as con:
            con.execute("CREATE TABLE pjpk_ready_pdp (year_label TEXT, subject TEXT, content_verified INTEGER)")
        self.assertEqual(ready_pdp("Tahun 5","Pendidikan Kesihatan",bad), [])

if __name__ == "__main__":
    unittest.main()
