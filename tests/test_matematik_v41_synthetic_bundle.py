"""Offline acceptance with a synthetic 585-Lesson ZIP, no private teacher files."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("math_v41", ROOT / "rph_standalone/matematik/staging_preview.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class Reply:
    ok = True
    def json(self): return {"ok": True}

class SyntheticBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = TemporaryDirectory(prefix="math_ci_")
        cls.archive = Path(cls.dir.name) / "synthetic.zip"
        with zipfile.ZipFile(cls.archive, "w", compression=zipfile.ZIP_STORED) as z:
            for year in range(2, 7):
                for lesson in range(1, 118):
                    for folder, ext, header in (
                        ("PDF", "pdf", b"%PDF-1.7\n"),
                        ("Word", "docx", b"PK\x03\x04"),
                        ("Markdown", "md", b"# RPH\n"),
                    ):
                        payload = header + f"y={year},n={lesson},ext={ext}\n".encode() + b"X" * 620
                        z.writestr(f"Tahun_{year}/{folder}/lesson_{lesson:03d}.{ext}", payload)
            z.writestr("AUDIT/V41_RELEASE_GATE.json", json.dumps({"lessons_total": 585, "final_ready": False}))
        cls.sha = hashlib.sha256(cls.archive.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls): cls.dir.cleanup()

    def test_all_lessons_and_formats_present(self):
        self.assertEqual(mod.verify_archive(self.archive, self.sha), self.archive)
        for year in range(2, 7):
            for lesson in range(1, 118):
                for fmt in ("pdf", "docx"):
                    data = mod.extract_rph_bytes(self.archive, year, lesson, fmt, self.sha)
                    self.assertIn(f"y={year},n={lesson}".encode(), data)

    def test_sha_mismatch_is_blocked(self):
        with self.assertRaises(mod.PreviewUnavailable):
            mod.verify_archive(self.archive, "0" * 64)

    def test_callback_never_activates_without_both_flags(self):
        ns = {"callback": lambda *a: None, "send": lambda *a: None, "send_document": lambda *a: None,
              "_access_info": lambda *a: {"active": True}, "_is_admin": lambda *a: False}
        for env in ({}, {mod.STAGING_FLAG: "1"}, {"CIKGULAJU_ENVIRONMENT": "staging"}):
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True):
                self.assertFalse(mod.install(ns, self.archive))

    def test_paid_preview_returns_only_selected_lesson(self):
        sent = []
        ns = {
            "callback": lambda cid, data: ("legacy", cid, data),
            "send": lambda cid, message: message,
            "send_document": lambda cid, path, caption: sent.append((Path(path).name, Path(path).read_bytes())) or Reply(),
            "_access_info": lambda cid: {"active": True},
            "_is_admin": lambda cid: False,
        }
        with patch.dict(os.environ, {mod.STAGING_FLAG:"1", "CIKGULAJU_ENVIRONMENT":"staging"}, clear=True):
            with patch.object(mod, "EXPECTED_SHA256", self.sha):
                self.assertTrue(mod.install(ns, self.archive))
                self.assertEqual(ns["callback"](41,"home"),("legacy",41,"home"))
                result = ns["callback"](41,"mathrph_v41_preview_y4_l117_pdf")
                self.assertTrue(result.ok)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], "matematik_tahun4_lesson117.pdf")
        self.assertIn(b"y=4,n=117", sent[0][1])

    def test_unpaid_never_reads_archive(self):
        sends = []
        ns = {
            "callback": lambda cid,d:("legacy",cid,d),
            "send": lambda cid,t:sends.append(t) or t,
            "send_document":lambda *a:self.fail("no delivery for unpaid"),
            "_access_info":lambda cid:{"active":False},
            "_is_admin":lambda cid:False
        }
        with patch.dict(os.environ,{mod.STAGING_FLAG:"1","CIKGULAJU_ENVIRONMENT":"staging"},clear=True):
            self.assertTrue(mod.install(ns, "/missing/file.zip"))
        ns["callback"](41, "mathrph_v41_preview_y4_l117_pdf")
        self.assertTrue(any("disahkan" in s for s in sends))

if __name__ == "__main__": unittest.main()
