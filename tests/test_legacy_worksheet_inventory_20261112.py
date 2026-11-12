"""Guard rails for the historical worksheet banks: no silent promotion."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.audit_legacy_worksheet_banks_20261112 import audit, inspect_db


class LegacyWorksheetAuditTests(unittest.TestCase):
    def test_inventory_is_read_only_and_unapproved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = root / "CikguLaju_Worksheet_Content.db"
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE worksheet_content (id INTEGER PRIMARY KEY, body TEXT)")
                con.execute("INSERT INTO worksheet_content (body) VALUES ('DRAF - NOT APPROVED')")
            before = db.read_bytes()
            manifest = {"sources": [{"path": db.name, "role": "worksheet content"},
                                    {"path": "not_present.db", "role": "old template"}]}
            result = audit(manifest, root)
            self.assertEqual(result["approval"], "NONE")
            self.assertEqual(result["production_feature_gate"], "OFF")
            self.assertEqual(result["sources"][0]["state"], "INSPECTED_NOT_APPROVED")
            self.assertEqual(result["sources"][0]["tables"][0]["rows"], 1)
            self.assertEqual(result["sources"][0]["tables"][0]["status"], "UNREVIEWED_ROWS")
            self.assertEqual(result["sources"][1]["state"], "MISSING_OR_LINK")
            self.assertEqual(db.read_bytes(), before)
            self.assertFalse((root / (db.name + "-wal")).exists())
            self.assertFalse((root / (db.name + "-shm")).exists())

    def test_disallow_path_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(ValueError):
                audit({"sources": [{"path": "../secrets.db", "role": "x"}]}, root)
            with self.assertRaises(ValueError):
                audit({"sources": [{"path": "outside.sqlite", "role": "x"}]}, root)
            outside = root / "actual.db"
            with sqlite3.connect(outside) as con:
                con.execute("CREATE TABLE worksheet_content (id INTEGER)")
            (root / "alias.db").symlink_to(outside)
            self.assertEqual(inspect_db(root / "alias.db")["state"], "MISSING_OR_LINK")

    def test_legacy_manifest_contains_no_ready_status(self):
        manifest_path = (Path(__file__).resolve().parents[1] /
                         "audits/legacy_worksheet_sources_staging_20261112.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["production_feature_gate"], "OFF")
        self.assertEqual(manifest["visibility"], "internal_staging_only")
        self.assertGreaterEqual(len(manifest["sources"]), 10)
        self.assertTrue(all(x["status"] == "UNREVIEWED" for x in manifest["sources"]))
        self.assertIn("CikguLaju_Worksheet_Content.db",
                      {x["path"] for x in manifest["sources"]})


if __name__ == "__main__":
    unittest.main()
