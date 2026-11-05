"""Isolated PSV publication-candidate integration QA; no Telegram or DB calls."""
import importlib.util
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "web" / "psv_2027_rph_release_bridge.py"
spec = importlib.util.spec_from_file_location("psv_bridge", ADAPTER)
psv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(psv)


class PSVBridgeTests(unittest.TestCase):
    def test_all_210_offline_lessons_match_rpt_and_contain_teaching_phases(self):
        count = 0
        for year in range(2, 7):
            for pdp in range(1, 43):
                with self.subTest(year=year, pdp=pdp):
                    p = psv.load_candidate(year, pdp, preview=True)
                    self.assertIsNotNone(p)
                    self.assertEqual((p["year"], p["pdp"]), (year, pdp))
                    self.assertTrue(p["title"])
                    self.assertGreater(len(p["objective"]), 20)
                    self.assertGreater(len(p["evidence"]), 18)
                    self.assertTrue(p["materials"])
                    self.assertEqual(set(p["stages"]), {
                        "set induksi", "aktiviti 1", "aktiviti 2", "pbd", "penutup"
                    })
                    self.assertFalse("kod bercetak" in p["sp"])
                    self.assertTrue(p["safety"])
                    count += 1
        self.assertEqual(count, 210)

    def test_forged_release_json_without_210_signed_textbook_records_cannot_enable(self):
        """A file claiming approval must not bypass the original-page per-PdP ledger."""
        import hashlib
        import json
        with tempfile.TemporaryDirectory(prefix="psv-release-failclosed-") as tmp:
            root = Path(tmp)
            folder = root / "rpt_2027" / "psv"
            folder.mkdir(parents=True)
            approval = {
                "approved": True, "rph_count": 210, "years": [2, 3, 4, 5, 6],
                "source_review": "INDIVIDUAL_TEXTBOOK_DSKP_PASSED",
                "runtime_staging": "PASSED",
                "runtime_staging_commit": "a" * 40,
                "content_sha256": "b" * 64,
                "audit_sha256": "c" * 64,
            }
            (folder / "psv_release_approval.json").write_text(
                json.dumps(approval), encoding="utf-8")
            self.assertFalse(psv._approved(root))
            self.assertIsNone(psv.load_candidate(5, 1, root=root))
            self.assertFalse(psv.install(SimpleNamespace(_rph_rows=lambda s: {}),
                                        enabled=True, root=root))

            audit = root / "rph_standalone" / "psv" / "audits"
            audit.mkdir(parents=True)
            raw = (ROOT / "rph_standalone" / "psv" / "audits"
                   / "psv_individual_210_review_20261105.csv").read_bytes()
            (audit / "psv_individual_210_review_20261105.csv").write_bytes(raw)
            approval["audit_sha256"] = hashlib.sha256(raw).hexdigest()
            (folder / "psv_release_approval.json").write_text(
                json.dumps(approval), encoding="utf-8")
            self.assertFalse(psv._individual_source_audit_passed(
                root, approval["audit_sha256"]))
            self.assertFalse(psv._approved(root))

    def test_current_candidate_has_no_unsigned_runtime_release(self):
        """Candidate is allowed for offline QA only until the full release protocol."""
        self.assertFalse(psv._approved(ROOT))
        self.assertTrue(all(
            psv.load_candidate(year, pdp, preview=True) is not None
            for year in range(2, 7) for pdp in range(1, 43)
        ))
        self.assertTrue(all(
            psv.load_candidate(year, pdp) is None
            for year in range(2, 7) for pdp in range(1, 43)
        ))

    def test_public_user_cannot_receive_draft_even_with_enabled_flag(self):
        base = {"KELAS": "6 Bestari", "TARIKH": "2026-11-05", "REFLEKSI": ""}
        with patch.dict(os.environ, {psv.FLAG: "1"}):
            runtime = SimpleNamespace(_rph_rows=lambda state: base)
            self.assertFalse(psv.install(runtime, enabled=True))
            self.assertIsNone(psv.load_candidate(6, 39))
            for y in range(2, 7):
                state = {"subject": "Pendidikan Seni Visual", "year": f"Tahun {y}", "lesson_no": 1}
                self.assertIs(base, psv.adapt_rows(state, base))
            self.assertEqual(runtime._rph_rows({}), base)

    def test_preview_overlays_only_psv_and_preserves_native_metadata(self):
        base = {"KELAS": "5 Jujur", "TARIKH": "2026-11-05",
                "REFLEKSI": "Guru isi selepas PdP", "CATATAN": "kehadiran sedia ada"}
        runtime = SimpleNamespace(_rph_rows=lambda state: dict(base))
        self.assertTrue(psv.install(runtime, enabled=True, preview=True))
        self.assertTrue(runtime.CIKGULAJU_PSV_RPH_BRIDGE_ACTIVE)
        for y, n in ((2, 20), (3, 9), (4, 39), (5, 39), (6, 34), (6, 39)):
            with self.subTest(year=y, pdp=n):
                state = {"subject": "Pendidikan Seni Visual", "year": f"Tahun {y}",
                         "lesson_no": str(n)}
                row = runtime._rph_rows(state)
                self.assertEqual(row["MATA PELAJARAN"], psv.SUBJECT)
                self.assertEqual(row["STANDARD PEMBELAJARAN"],
                                 psv.load_candidate(y, n, preview=True)["sp"])
                self.assertEqual(row["REFLEKSI"], base["REFLEKSI"])
                self.assertEqual(row["TARIKH"], base["TARIKH"])
                self.assertTrue(row["AKTIVITI UTAMA"])
                self.assertTrue(row["PENTAKSIRAN"])
                self.assertNotIn("DRAF SEMAK", " ".join(str(x) for x in row.values()))
        for subject in ("English", "Pendidikan Islam", "Pendidikan Moral", "Pendidikan Kesenian"):
            state = {"subject": subject, "year": 5, "lesson_no": 39}
            self.assertEqual(runtime._rph_rows(state), base)

    def test_wrong_subject_year_lesson_or_selected_standard_fails_closed(self):
        base = {"old": "native RPH"}
        valid = {"subject": "Pendidikan Seni Visual", "year": 6, "lesson_no": 39}
        cases = [
            dict(valid, subject="Pendidikan Jasmani"),
            dict(valid, year=1),
            dict(valid, year=7),
            dict(valid, lesson_no=43),
            dict(valid, lesson_no="../001"),
            dict(valid, sp_code="999.9.9"),
            dict(valid, sk_code="999.9"),
        ]
        for state in cases:
            with self.subTest(state=state):
                self.assertIs(psv.adapt_rows(state, base, preview=True), base)

    def test_corrupt_source_standard_rejected_and_no_unapproved_fallback(self):
        with tempfile.TemporaryDirectory(prefix="psv-bridge-audit-") as tmp:
            root = Path(tmp)
            target = root / "rpt_2027" / "psv"
            target.mkdir(parents=True)
            shutil.copy(ROOT / "rpt_2027" / "psv" / "RPT_PSV_Tahun_5_2027_DRAF.csv",
                        target / "RPT_PSV_Tahun_5_2027_DRAF.csv")
            source = ROOT / "rph_standalone" / "psv" / "year5" / "lesson_039.md"
            path = root / "rph_standalone" / "psv" / "year5" / "lesson_039.md"
            path.parent.mkdir(parents=True)
            value = source.read_text(encoding="utf-8")
            path.write_text(value, encoding="utf-8")
            self.assertIsNotNone(psv.load_candidate(5, 39, preview=True, root=root))
            self.assertIsNone(psv.load_candidate(5, 39, root=root))
            self.assertIn("**SP:** 3.1.5", value)
            path.write_text(value.replace("**SP:** 3.1.5", "**SP:** 8.8.8"),
                            encoding="utf-8")
            self.assertIsNone(psv.load_candidate(5, 39, preview=True, root=root))


    def test_staging_runtime_entrypoint_gate_remains_off_by_default(self):
        """Source-level contract: production entrypoint remains explicitly opt-in."""
        path = ROOT / "tools" / "psv_candidate_staging_entrypoint.py"
        entrypoint = path.read_text(encoding="utf-8")
        shared = (ROOT / "tools" / "run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        self.assertIn("from web.psv_2027_rph_release_bridge import install", entrypoint)
        self.assertIn("PSV_RPH_CANDIDATE_ACTIVE = bool(install(telegram_runtime))", entrypoint)
        self.assertNotIn("preview=True", entrypoint)
        self.assertNotIn("enabled=True", entrypoint)
        self.assertNotIn("psv_2027_rph_release_bridge", shared)
        with patch.dict(os.environ, {psv.FLAG: ""}):
            fake = SimpleNamespace(_rph_rows=lambda state: {"safe": True})
            self.assertFalse(psv.install(fake))
            self.assertFalse(hasattr(fake, "CIKGULAJU_PSV_RPH_BRIDGE_ACTIVE"))
            self.assertEqual(fake._rph_rows({}), {"safe": True})


    def test_staging_entrypoint_import_with_stub_bot_remains_fail_closed(self):
        """Exercise dedicated WSGI module import without importing real app or bots."""
        import sys
        import types
        runtime = SimpleNamespace(_rph_rows=lambda state: {"native": "unchanged"})
        original = runtime._rph_rows
        stub = types.ModuleType("tools.run_telegram_with_curriculum_api")
        stub.app = object()
        stub.telegram_runtime = runtime
        path = ROOT / "tools" / "psv_candidate_staging_entrypoint.py"
        with patch.dict(os.environ, {psv.FLAG: "1"}):
            with patch.dict(sys.modules, {"tools.run_telegram_with_curriculum_api": stub}):
                entry_spec = importlib.util.spec_from_file_location("psv_staging_wsgi_smoke", path)
                module = importlib.util.module_from_spec(entry_spec)
                entry_spec.loader.exec_module(module)
        self.assertIs(module.app, stub.app)
        self.assertFalse(module.PSV_RPH_CANDIDATE_ACTIVE)
        self.assertIs(runtime._rph_rows, original)
        self.assertFalse(hasattr(runtime, "CIKGULAJU_PSV_RPH_BRIDGE_ACTIVE"))


if __name__ == "__main__":
    unittest.main()
