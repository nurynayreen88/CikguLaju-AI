"""Regression guard for KP2027 source inventory; no fake SK/SP or legacy fallback."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask

from curriculum.kp2027.inventory import (
    STATUS, KP2027SourceUnverified, load_inventory, subjects_for, status_for,
    verified_standards_for, request_rph, request_rpt,
)
from curriculum_version_selector import resolve_curriculum
from web.kp2027_status_api import (
    create_kp2027_status_blueprint, register_if_enabled,
)

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "S" * 40


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.digest = load_inventory()

    def test_2027_levels_and_scope(self):
        self.assertEqual(self.data["release_status"], STATUS)
        self.assertEqual(self.data["as_of"], "2026-11-06")
        self.assertEqual(self.data["policy"]["no_legacy_substitution"], True)
        self.assertEqual(self.data["policy"]["no_inferred_standards"], True)
        self.assertEqual(self.data["policy"]["no_silent_fallback"], True)
        self.assertEqual(self.data["policy"]["legacy_db_untouched"], True)
        self.assertEqual(len(self.data["subject_records"]), 21)
        self.assertEqual(len(subjects_for("Tahun 1")[0]), 8)
        self.assertEqual(len(subjects_for("Tingkatan 1")[0]), 13)
        self.assertFalse(any(row["subject"] == "Sejarah"
                             for row in subjects_for("Tahun 1")[0]))
        self.assertTrue(any(row["subject"] == "Alam dan Manusia"
                            for row in subjects_for("Tahun 1")[0]))
        self.assertTrue(any(row["subject"] == "Sejarah"
                            for row in subjects_for("Tingkatan 1")[0]))

    def test_every_candidate_unverified_and_blocked(self):
        for r in self.data["subject_records"]:
            with self.subTest(level=r["level"], subject=r["subject"]):
                status = status_for(r["level"], r["subject"], self.digest)
                self.assertEqual(status["readiness"], "WAITING_ORIGINAL_DK")
                self.assertFalse(status["document_pdf_downloaded"])
                self.assertFalse(status["rph_ready"])
                self.assertFalse(status["rpt_ready"])
                self.assertFalse(r["standards_extracted"])
                self.assertFalse(r["standards_audited"])
                self.assertEqual(r["standard_count_verified"], 0)
                with self.assertRaises(KP2027SourceUnverified):
                    verified_standards_for(r["level"], r["subject"])
                with self.assertRaises(KP2027SourceUnverified):
                    request_rpt(r["level"], r["subject"])
                with self.assertRaises(KP2027SourceUnverified):
                    request_rph(r["level"], r["subject"])
                self.assertFalse(resolve_curriculum(
                    "kp2027", r["level"], r["subject"])["enabled"])

    def test_bad_subject_year_or_digest_is_rejected(self):
        with self.assertRaises(ValueError):
            subjects_for("Tahun 2")
        with self.assertRaises(KP2027SourceUnverified):
            status_for("Tingkatan 1", "Matematik", "0" * 64)
        with self.assertRaises(KP2027SourceUnverified):
            status_for("Tahun 1", "Sejarah")

    def test_tampered_source_cannot_mark_rph_ready(self):
        bad = json.loads(json.dumps(self.data))
        bad["subject_records"][0]["rph_ready"] = True
        with tempfile.TemporaryDirectory() as dirname:
            f = Path(dirname) / "tampered.json"
            f.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(KP2027SourceUnverified):
                load_inventory(f)
        bad = json.loads(json.dumps(self.data))
        bad["subject_records"][0]["document_original_sha256"] = "a" * 64
        with tempfile.TemporaryDirectory() as dirname:
            f = Path(dirname) / "tampered.json"
            f.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(KP2027SourceUnverified):
                load_inventory(f)

    def test_sidecar_schema_has_no_synthetic_standards(self):
        schema = (ROOT / "curriculum" / "kp2027" / "staging_schema.sql").read_text()
        self.assertNotIn("DROP TABLE", schema.upper())
        self.assertNotIn("ALTER TABLE", schema.upper())
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(schema)
            for table in (
                "kp2027_source_documents", "kp2027_curriculum_standards",
                "kp2027_learning_sequences", "kp2027_sequence_standards"
            ):
                count = conn.execute("SELECT count(*) FROM " + table).fetchone()[0]
                self.assertEqual(count, 0)
            conn.execute("PRAGMA foreign_keys=ON")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("""INSERT INTO kp2027_curriculum_standards
                    (source_id,standard_kind,standard_text,source_page,source_section)
                    VALUES (999,'SP','FAKE',1,'FAKE')""")
        finally:
            conn.close()


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(create_kp2027_status_blueprint())
        self.client = self.app.test_client()
        self.headers = {"Authorization": "Bearer " + TOKEN}
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": TOKEN,
            "CIKGULAJU_KP2027_STAGING_ENABLED": "1",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()

    def test_staging_off_by_default(self):
        with patch.dict(os.environ, {"CIKGULAJU_KP2027_STAGING_ENABLED": "0"}):
            r = self.client.get("/internal/kp2027/v1/levels", headers=self.headers)
            self.assertEqual(r.status_code, 503)
        unauthorized = self.client.get("/internal/kp2027/v1/levels")
        self.assertEqual(unauthorized.status_code, 401)

    def test_authoritative_inventory_only(self):
        root = "/internal/kp2027/v1"
        r = self.client.get(root + "/subjects?level=Tahun%201", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["items"]), 8)
        self.assertEqual(r.get_json()["status"], STATUS)
        self.assertFalse(r.get_json()["rph_available"])
        digest = r.get_json()["source_digest"]
        detail = self.client.get(
            root + "/status?level=Tahun%201&subject=Alam%20dan%20Manusia"
            + "&source_digest=" + digest, headers=self.headers)
        self.assertEqual(detail.status_code, 200)
        self.assertFalse(detail.get_json()["rph_ready"])
        missing = self.client.get(
            root + "/standards?level=Tahun%201&subject=Alam%20dan%20Manusia",
            headers=self.headers)
        self.assertEqual(missing.status_code, 503)
        render = self.client.post(root + "/render", json={"year": 1},
                                  headers=self.headers)
        self.assertEqual(render.status_code, 503)

    def test_scope_security(self):
        root = "/internal/kp2027/v1"
        r = self.client.get(root + "/subjects?level=Tahun%202", headers=self.headers)
        self.assertEqual(r.status_code, 400)
        r = self.client.get(root + "/subjects?level=Tahun%201&bogus=1",
                            headers=self.headers)
        self.assertEqual(r.status_code, 400)
        r = self.client.get(root + "/subjects?level=Tahun%201&level=Tahun%201",
                            headers=self.headers)
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
