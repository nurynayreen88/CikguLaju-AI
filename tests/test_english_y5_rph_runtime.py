"""Offline English Year 5 release gate checks, without importing app.py or touching credits."""
import json
import tempfile
import types
import unittest
from pathlib import Path

from web.english_y5_standalone_runtime import (
    CHOICE_LESSONS, LESSON_ROOT, RELEASE_FLAG, adapt_rows, install, load_lesson,
)


class EnglishY5IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = json.loads((LESSON_ROOT / "sow_standard_gate_2027.json").read_text(encoding="utf-8"))

    def test_exact_inventory_and_sow(self):
        files = sorted(LESSON_ROOT.glob("lesson_[0-9][0-9][0-9].md"))
        self.assertEqual([int(p.stem[-3:]) for p in files], list(range(1, 161)))
        self.assertEqual(len(self.gate["lessons"]), 160)
        self.assertEqual(sum(not item["teacher_choice"] for item in self.gate["lessons"].values()), 151)
        self.assertEqual(set(self.gate["teacher_selected_lessons"]), CHOICE_LESSONS)
        self.assertEqual((self.gate["lessons"]["141"]["main_ls"],
                          self.gate["lessons"]["141"]["complementary_ls"]), ("5.3.1", "4.2.4"))

    def test_documented_draft_preserved(self):
        self.assertIn("DRAF", (LESSON_ROOT / "lesson_088.md").read_text(encoding="utf-8"))
        self.assertIn("DRAF", (LESSON_ROOT / "lesson_160.md").read_text(encoding="utf-8"))

    def test_target_and_fallback_are_nondestructive(self):
        rows = {"OBJEKTIF PEMBELAJARAN": "original", "TARIKH": "03/11"}
        for st in ({"subject": "Matematik", "year": "5", "lesson_no": 1},
                   {"subject": "English", "year": "6", "lesson_no": 1},
                   {"subject": "English", "year": "5", "lesson_no": 0},
                   {"subject": "English", "year": "5", "lesson_no": 161},
                   {"subject": "English", "year": "5", "lesson_no": "../1"},
                   {"subject": "English", "year": "5", "lesson_no": True},
                   {"subject": "English", "year": "5", "lesson_no": 1, "sp_code": "2.3.1"}):
            self.assertIs(adapt_rows(st, rows), rows)
        for lesson in CHOICE_LESSONS | {141}:
            st = {"subject": "English", "year": "5", "lesson_no": lesson}
            self.assertIs(adapt_rows(st, rows), rows)

    def test_markdown_stages_read_from_varied_sources(self):
        # Separate numbered phase, inline phase and combined 40-minute activities.
        for n in (1, 5, 15, 16, 30, 37, 67, 88, 97, 110, 140, 141, 160):
            with self.subTest(lesson=n):
                r = load_lesson(n)
                self.assertIsNotNone(r)
                self.assertTrue(r["intro"])
                self.assertTrue(r["activities"])
                self.assertTrue(r["pbd"])
                self.assertTrue(r["closure"])

    def test_valid_year5_rph_overlays_without_changing_unrelated_fields(self):
        original = {"OBJEKTIF PEMBELAJARAN": "generic", "TARIKH": "03/11",
                    "REFLEKSI": "original", "KUOTA": 10}
        state = {"subject": "Bahasa Inggeris", "year": "Tahun 5",
                 "lesson_no": 1, "sp_code": "1.2.1"}
        data = adapt_rows(state, original)
        self.assertIsNot(data, original)
        self.assertEqual(data["TARIKH"], "03/11")
        self.assertEqual(data["KUOTA"], 10)
        self.assertEqual(data["REFLEKSI"], "original")
        self.assertIn("English Plus", data["BAHAN BANTU MENGAJAR"])
        self.assertIn("Main: 1.2.1", data["STANDARD PEMBELAJARAN"])

    def test_install_is_opt_in_and_preserves_existing_generator(self):
        prior = lambda st, *a, **kw: {"OBJEKTIF PEMBELAJARAN": "original", "TARIKH": "01/01"}
        runtime = types.SimpleNamespace(_rph_rows=prior, callback=lambda: "ok", quota=lambda: 10)
        self.assertFalse(install(runtime, enabled=False))
        self.assertIs(runtime._rph_rows, prior)
        self.assertTrue(install(runtime, enabled=True))
        self.assertTrue(install(runtime, enabled=True))
        self.assertEqual(runtime.callback(), "ok")
        self.assertEqual(runtime.quota(), 10)
        self.assertEqual(runtime._rph_rows({"subject": "Math", "year": "5", "lesson_no": 1}),
                         {"OBJEKTIF PEMBELAJARAN": "original", "TARIKH": "01/01"})

    def test_fixed_source_parse_coverage_report(self):
        fixed = [int(n) for n, row in self.gate["lessons"].items()
                 if not row["teacher_choice"] and int(n) != 141]
        parsed = [n for n in fixed if load_lesson(n) is not None]
        missing = sorted(set(fixed) - set(parsed))
        print("YEAR5_FIXED_PARSED", len(parsed), "/150; FORMAT_PENDING", missing)
        from web.english_y5_standalone_runtime import _field, _sections, _plain
        for n in missing:
            content = (LESSON_ROOT / ("lesson_%03d.md" % n)).read_text(encoding="utf-8")
            clean = "\n".join(_plain(line) for line in content.splitlines())
            blocks = _sections(content)
            print("Y5_UNREADABLE", n, "fields", {
                "material": bool(_field(clean, ("Materials", "Sources"))),
                "objective": bool(_field(clean, ("Suggested learning objectives", "Suggested objectives",
                                                "Learning objectives", "Learning objective", "Objectives", "Objective"))),
                "intro": bool(blocks.get("intro")),
                "main": bool(blocks.get("main") or all(blocks.get("activity%d" % k) for k in (1, 2, 3))),
                "pbd": bool(blocks.get("pbd") or blocks.get("combined")),
                "closure": bool(blocks.get("closure") or blocks.get("combined")),
            })
        self.assertGreaterEqual(len(parsed), 100)

    def test_no_overlay_on_missing_or_modified_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lesson_001.md").write_text((LESSON_ROOT / "lesson_001.md").read_text(encoding="utf-8"), encoding="utf-8")
            rows = {"OBJEKTIF PEMBELAJARAN": "previous"}
            state = {"subject": "English", "year": "5", "lesson_no": 1}
            self.assertIs(adapt_rows(state, rows, root=root), rows)
            (root / "sow_standard_gate_2027.json").write_text('{"version":"wrong"}', encoding="utf-8")
            self.assertIs(adapt_rows(state, rows, root=root), rows)


if __name__ == "__main__":
    unittest.main()
