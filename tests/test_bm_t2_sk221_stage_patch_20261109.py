"""Non-destructive tests: a copied DB may change, the master never does."""
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.bm_t2_sk221_stage_patch_20261109 import (
    SafetyHold, make_staging_copy, verify_source,
)


class BMT2CopyRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "master.db"
        self.target = Path(self.temp.name) / "candidate.db"
        with sqlite3.connect(self.source) as conn:
            conn.executescript("""
                CREATE TABLE verified_pdp_sequence (
                    id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                    unit_title TEXT, pdp_title TEXT, sk_code TEXT,
                    sp_code TEXT, verification_status TEXT);
                CREATE TABLE curriculum_standards (
                    id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                    sk_code TEXT, sk_text TEXT, sp_code TEXT,
                    sp_text TEXT, verified INTEGER);
            """)
            conn.executemany(
                "INSERT INTO verified_pdp_sequence VALUES (?,?,?,?,?,?,?,?)",
                [
                    (17, "Tahun 2", "Bahasa Melayu", "Hidup Berjiran",
                     "Majlis Pengikat Kemesraan", "2.1", "2.2.1",
                     "SOURCE_VERIFIED"),
                    (18, "Tahun 2", "Bahasa Melayu", "Jiran Sepakat",
                     "Cerita Jiran", "2.2", "2.2.1", "SOURCE_VERIFIED"),
                    (19, "Tahun 3", "Bahasa Melayu", "Hidup Berjiran",
                     "Majlis Pengikat Kemesraan", "2.1", "2.2.1",
                     "SOURCE_VERIFIED"),
                ],
            )
            conn.execute(
                "INSERT INTO curriculum_standards VALUES (?,?,?,?,?,?,?,?)",
                (41, "Tahun 2", "Bahasa Melayu", "2.2",
                 "Membaca, memahami, dan menaakul bahan grafik dan bukan grafik",
                 "2.2.1",
                 "Membaca, memahami dan mengenal pasti kosa kata, isi tersurat, "
                 "isi tersirat, idea utama, idea sampingan, idea keseluruhan", 1),
            )

    def digest(self):
        return hashlib.sha256(self.source.read_bytes()).hexdigest()

    def test_candidate_changes_exactly_one_row_and_source_unchanged(self):
        before = self.digest()
        result = make_staging_copy(self.source, self.target,
                                   expected_source_sha256=before)
        self.assertEqual(result["updated_rows"], 1)
        self.assertEqual(result["source_sha256"], before)
        self.assertEqual(self.digest(), before)
        with sqlite3.connect(self.source) as db:
            self.assertEqual(db.execute(
                "SELECT sk_code FROM verified_pdp_sequence WHERE id=17"
            ).fetchone()[0], "2.1")
        with sqlite3.connect(self.target) as db:
            self.assertEqual(db.execute(
                "SELECT id,sk_code FROM verified_pdp_sequence ORDER BY id"
            ).fetchall(), [(17, "2.2"), (18, "2.2"), (19, "2.1")])
            self.assertEqual(db.execute("PRAGMA quick_check").fetchone()[0],
                             "ok")

    def test_verify_only_does_not_create_candidate(self):
        self.assertEqual(verify_source(self.source)["target_rowid"], 17)
        self.assertFalse(self.target.exists())

    def test_refuses_overwrite_of_source_and_existing_target(self):
        with self.assertRaises(SafetyHold):
            make_staging_copy(self.source, self.source)
        self.target.write_bytes(b"keep this existing file")
        with self.assertRaises(SafetyHold):
            make_staging_copy(self.source, self.target)
        self.assertEqual(self.target.read_bytes(), b"keep this existing file")

    def test_stale_hash_does_not_create_candidate(self):
        with self.assertRaises(SafetyHold):
            make_staging_copy(self.source, self.target,
                              expected_source_sha256="bad-hash")
        self.assertFalse(self.target.exists())

    def test_refuses_conflicting_or_unverified_sp_proof(self):
        with sqlite3.connect(self.source) as db:
            db.execute(
                "INSERT INTO curriculum_standards VALUES (?,?,?,?,?,?,?,?)",
                (42, "Tahun 2", "Bahasa Melayu", "2.1", "Conflicting",
                 "2.2.1", "Conflicting verified text", 1),
            )
        with self.assertRaises(SafetyHold):
            make_staging_copy(self.source, self.target)
        self.assertFalse(self.target.exists())

    def test_refuses_missing_verified_proof(self):
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE curriculum_standards SET verified=0")
        with self.assertRaises(SafetyHold):
            make_staging_copy(self.source, self.target)
        self.assertFalse(self.target.exists())

    def test_refuses_source_row_already_updated(self):
        with sqlite3.connect(self.source) as db:
            db.execute(
                "UPDATE verified_pdp_sequence SET sk_code='2.2' WHERE id=17"
            )
        with self.assertRaises(SafetyHold):
            make_staging_copy(self.source, self.target)
        self.assertFalse(self.target.exists())

    def test_refuses_ambiguous_lesson_identity(self):
        with sqlite3.connect(self.source) as db:
            db.execute(
                "INSERT INTO verified_pdp_sequence VALUES (?,?,?,?,?,?,?,?)",
                (20, "Tahun 2", "Bahasa Melayu", "Hidup Berjiran",
                 "Majlis Pengikat Kemesraan", "2.1", "2.2.1",
                 "SOURCE_VERIFIED"),
            )
        with self.assertRaises(SafetyHold):
            make_staging_copy(self.source, self.target)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
