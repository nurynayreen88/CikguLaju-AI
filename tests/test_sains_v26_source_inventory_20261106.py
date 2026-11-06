"""Sains source-gate tests: no fictitious 587 completion and no DB writes."""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.audit_sains_v26_readonly_20261106 import (
    audit, summarize_rows, verify_and_rebuild,
)


class SainsV26ReadOnlyTests(unittest.TestCase):
    def test_multiple_sps_are_one_pdp_not_two_or_one_week(self):
        rows = [
            {"year_label": "Tahun 2", "subject": "Sains", "pdp_sequence_code": "SCI-2-007",
             "source_sequence_no": 7, "week_no": 3, "unit_code": "U1",
             "unit_title": "Benda Hidup", "sk_code": "1.1", "sp_code": "1.1.1",
             "textbook_ref": "BT ms. 22"},
            {"year_label": "Tahun 2", "subject": "Sains", "pdp_sequence_code": "SCI-2-007",
             "source_sequence_no": 7, "week_no": 3, "unit_code": "U1",
             "unit_title": "Benda Hidup", "sk_code": "1.1", "sp_code": "1.1.2",
             "textbook_ref": "BT ms. 22"},
            {"year_label": "Tahun 2", "subject": "Sains", "pdp_sequence_code": "SCI-2-008",
             "source_sequence_no": 8, "week_no": 3, "unit_code": "U1",
             "unit_title": "Benda Hidup", "sk_code": "", "sp_code": "",
             "textbook_ref": ""},
        ]
        info = summarize_rows(rows)["2"]
        self.assertEqual(info["db_rows"], 3)
        self.assertEqual(info["db_distinct_pdp"], 2)
        self.assertEqual(info["groups_without_sksp"], 1)
        self.assertEqual(info["groups_without_textbook_ref"], 1)
        self.assertEqual(info["difference_from_working_target"], 2 - 92)

    def test_rejected_status_never_counts_as_verified_source(self):
        with sqlite3.connect(":memory:") as db:
            db.execute("""CREATE TABLE verified_pdp_sequence (
                year_label TEXT, subject TEXT, pdp_sequence_code TEXT,
                sk_code TEXT, sp_code TEXT, unit_code TEXT, unit_title TEXT,
                textbook_ref TEXT, source_sequence_no INTEGER,
                verification_status TEXT, week_no INTEGER)""")
            db.executemany("""INSERT INTO verified_pdp_sequence
                (year_label,subject,pdp_sequence_code,sk_code,sp_code,unit_code,
                 unit_title,textbook_ref,source_sequence_no,verification_status,week_no)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?)""", [
                ("Tahun 2", "Sains", "SCI-2-001", "1", "1.1", "U1", "Sains",
                 "BT ms. 4", 1, "VERIFIED", 1),
                ("Tahun 2", "Sains", "SCI-2-002", "1", "1.2", "U1", "Sains",
                 "BT ms. 5", 2, "REJECTED", 1),
                ("Tahun 2", "Matematik", "M2-001", "1", "1.1", "U1", "Nombor",
                 "BT ms. 6", 1, "VERIFIED", 1),
            ])
            result = audit(db)
            self.assertEqual(result["release_decision"], "HOLD")
            self.assertEqual(result["rejected_rows_excluded"], 1)
            self.assertEqual(result["db_distinct_pdp_total"], 1)
            self.assertEqual(result["yearly"]["2"]["db_distinct_pdp"], 1)
            self.assertEqual(result["yearly"]["1"]["db_distinct_pdp"], 0)

    def test_manifest_hash_before_any_inventory(self):
        with tempfile.TemporaryDirectory() as dir:
            root = Path(dir)
            payloads = [b"aa", b"bb", b"cc"]
            entries = []
            for idx, data in enumerate(payloads, 1):
                path = root / f"v26_00_part{idx}.bin"
                path.write_bytes(data)
                entries.append({"file": path.name, "size": len(data),
                                "sha256": hashlib.sha256(data).hexdigest()})
            (root / "v26_00_manifest.json").write_text(json.dumps({
                "source": "CikguLaju_Curriculum_Master_v26_00.db",
                "parts": entries,
                "size": 6,
                "sha256": hashlib.sha256(b"".join(payloads)).hexdigest(),
            }))
            with tempfile.TemporaryDirectory() as tmp:
                output = verify_and_rebuild(Path(tmp), root)
                self.assertEqual(output.read_bytes(), b"aabbcc")
            # Tamper with a single original part: fail closed.
            (root / "v26_00_part3.bin").write_bytes(b"dd")
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    verify_and_rebuild(Path(tmp), root)


if __name__ == "__main__":
    unittest.main()
