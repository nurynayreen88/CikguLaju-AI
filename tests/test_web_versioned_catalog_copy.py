"""Safeguards for a separate, checksum-verified Web curriculum database."""
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from web.versioned_catalog_copy import (
    CurriculumCopyUnavailable, get_verified_web_copy,
)
from tools.run_web_v1_preview import app


def make_fixture(folder):
    root = Path(folder)
    original = root / "source.db"
    with sqlite3.connect(original) as db:
        db.execute("""CREATE TABLE rpt_entries (
            id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
            verified INTEGER, notes TEXT, sequence_no INTEGER,
            unit_title TEXT, topic TEXT, subtopic TEXT, skill_focus TEXT)""")
        db.execute("""INSERT INTO rpt_entries VALUES
            (17,'Tahun 2','Bahasa Inggeris',1,'',4,'My Friends',
            'Introductions','Hello','Speaking')""")
    raw = original.read_bytes()
    first, second = raw[:len(raw)//2], raw[len(raw)//2:]
    parts = []
    for i, part in enumerate((first, second), 1):
        filename = "part%d.bin" % i
        (root / filename).write_bytes(part)
        parts.append({"file": filename, "size": len(part),
                      "sha256": sha256(part).hexdigest()})
    manifest = {"source": "source.db", "size": len(raw),
                "sha256": sha256(raw).hexdigest(), "parts": parts}
    (root / "fixture_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return original


class WebVersionedCopyTests(unittest.TestCase):
    def test_verified_copy_is_distinct_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as dirname:
            original = make_fixture(dirname)
            prior = sha256(original.read_bytes()).hexdigest()
            copy = get_verified_web_copy("fixture_manifest.json", repo_root=dirname)
            self.assertTrue(copy["verified"])
            self.assertEqual(copy["version"], "fixture")
            self.assertNotEqual(Path(copy["path"]).resolve(), original.resolve())
            self.assertEqual(sha256(original.read_bytes()).hexdigest(), prior)
            self.assertFalse(os.stat(copy["path"]).st_mode & 0o222)
            with sqlite3.connect(Path(copy["path"]).resolve().as_uri() + "?mode=ro", uri=True) as db:
                self.assertEqual(db.execute(
                    "SELECT COUNT(*) FROM rpt_entries WHERE verified=1").fetchone()[0], 1)

    def test_corrupt_part_fails_closed(self):
        with tempfile.TemporaryDirectory() as dirname:
            make_fixture(dirname)
            (Path(dirname) / "part2.bin").write_bytes(b"broken")
            with self.assertRaises(CurriculumCopyUnavailable):
                get_verified_web_copy("fixture_manifest.json", repo_root=dirname)

    def test_unrecognized_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as dirname:
            with self.assertRaises(CurriculumCopyUnavailable):
                get_verified_web_copy("../../etc/passwd", repo_root=dirname)

    def test_uses_local_copy_without_telegram_catalog_or_supabase_duplication(self):
        from web_v1_telegram_auth_routes import COOKIE
        from web_v1_sessions import issue_session_ticket
        with tempfile.TemporaryDirectory() as dirname:
            make_fixture(dirname)
            secret = "s" * 40
            settings = {"CIKGULAJU_WEB_CATALOG_MODE": "versioned-copy",
                        "CIKGULAJU_WEB_COPY_MANIFEST": "fixture_manifest.json"}
            with patch.dict(os.environ, settings), \
                 patch("web.versioned_catalog_copy.ROOT", Path(dirname)), \
                 patch("web_v1_telegram_auth_routes._config",
                       return_value={"CIKGULAJU_WEB_SESSION_SECRET": secret}), \
                 patch("web_v1_telegram_auth_routes._lookup",
                       return_value={"telegram_user_id": 321, "authenticated": True}), \
                 patch("web.authoritative_http_source.AuthoritativeHttpCurriculumSource",
                       side_effect=AssertionError("Web copy must not call Telegram catalog")):
                client = app.test_client()
                client.set_cookie(COOKIE, issue_session_ticket(321, secret))
                subjects = client.get("/api/options?kind=subjects&year=2")
                self.assertEqual(subjects.status_code, 200, subjects.get_json())
                self.assertIn("ENGLISH", [row["value"] for row in subjects.json])
                units = client.get("/api/options?kind=units&year=2&subject=ENGLISH")
                self.assertEqual(units.status_code, 200)
                self.assertEqual(units.json[0]["value"], "My Friends")
                lessons = client.get(
                    "/api/options?kind=pdp&year=2&subject=ENGLISH&unit=My+Friends")
                self.assertEqual(lessons.status_code, 200)
                self.assertEqual(lessons.json[0]["value"], "17")
                state = client.get("/api/source/status")
                self.assertTrue(state.json["web_copy_verified"])
                self.assertFalse(state.json["shared_source_verified"])
                self.assertFalse(state.json["telegram_parity_verified"])
                self.assertEqual(state.json["copy_version"], "fixture")

    def test_actual_primary_manifest_when_available(self):
        """Telegram production log reports v26.00 as active primary database."""
        root = Path(__file__).resolve().parents[1]
        manifest = root / "v26_00_manifest.json"
        if not manifest.is_file():
            self.skipTest("Versioned source not checked out")
        result = get_verified_web_copy("v26_00_manifest.json", repo_root=root)
        self.assertEqual(result["version"], "v26_00")
        self.assertTrue(result["verified"])


if __name__ == "__main__":
    unittest.main()
