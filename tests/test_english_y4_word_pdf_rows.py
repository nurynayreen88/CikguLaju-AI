"""Regression suite: Telegram English Year 4 RPH standalone Word/PDF row bridge.

Only tests source-to-document rows. It does NOT claim that user accounts,
live Telegram delivery, native PDF pagination or audio have been verified.
"""
from pathlib import Path
import json
import types
import unittest
from tempfile import TemporaryDirectory

from web.english_y4_standalone_runtime import (
    OFFICIAL_SOW_INDEX, _selected_y4_lesson,
    adapt_rows, install_rows, load_release_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = {16, 32, 48, 64, 80, 96, 112, 128, 144, 160}


class EnglishY4WordPdfRowsTests(unittest.TestCase):
    def setUp(self):
        self.existing = {
            "MATA PELAJARAN": "English",
            "TAHUN/TINGKATAN": "Tahun 4",
            "TAJUK": "OLD CURRICULUM HEADING",
            "TARIKH": "04/11/2026",
            "MASA": "08:00",
            "KELAS": "4 Cemerlang",
            "BILANGAN MURID": "31",
            "REFLEKSI": "Teacher's reflection",
            "AKTIVITI UTAMA": "GENERIC OLD LESSON PLAN",
            "SET INDUKSI": "GENERIC INDUCTION",
            "PENUTUP": "GENERIC CLOSURE",
        }
        self.state = {"year": "Tahun 4", "subject": "English", "lesson_no": 1,
                      "sp_code": "1.2.2", "comp_sp_code": "1.1.1"}

    def test_lesson_1_document_uses_actual_standalone_tasks(self):
        updated = adapt_rows(self.state, self.existing)
        self.assertIsNot(updated, self.existing)
        self.assertEqual(updated["MAIN LEARNING STANDARD"], "1.2.2")
        self.assertEqual(updated["COMPLEMENTARY LEARNING STANDARD"], "1.1.1")
        self.assertEqual(updated["MAIN CONTENT STANDARD"], "1.2")
        self.assertEqual(updated["COMPLEMENTARY CONTENT STANDARD"], "1.1")
        self.assertIn("Where are you from?", updated["TAJUK"])
        self.assertIn("Class CD1 Track 3", updated["BAHAN BANTU MENGAJAR"])
        self.assertIn("Teacher:", updated["SET INDUKSI"])
        self.assertIn("Pupils:", updated["AKTIVITI UTAMA"])
        self.assertIn("Activity 1", updated["AKTIVITI UTAMA"])
        self.assertIn("Activity 2", updated["AKTIVITI UTAMA"])
        self.assertIn("flag", updated["AKTIVITI UTAMA"].lower())
        self.assertNotIn("GENERIC OLD LESSON", updated["AKTIVITI UTAMA"])
        self.assertNotIn("QA status", "\n".join(updated.values()))
        self.assertNotIn("Verified mapping and limits", "\n".join(updated.values()))

    def test_teacher_entered_metadata_is_preserved(self):
        out = adapt_rows(self.state, self.existing)
        for field in ("TARIKH", "MASA", "KELAS", "BILANGAN MURID", "REFLEKSI"):
            self.assertEqual(out[field], self.existing[field])
        self.assertEqual(self.existing["AKTIVITI UTAMA"], "GENERIC OLD LESSON PLAN")

    def test_mismatched_sow_standard_never_replaces_rows(self):
        for field in ("sp_code", "comp_sp_code", "bi_main_sp_code", "bi_comp_sp_code"):
            with self.subTest(field=field):
                bad = dict(self.state, **{field: "5.1.9"})
                self.assertIs(adapt_rows(bad, self.existing), self.existing)

    def test_explicit_lesson_identity_wins_over_stale_textbook_number(self):
        state = dict(self.state, textbook_lesson_no=40, lesson=70)
        self.assertIn("flag", adapt_rows(state, self.existing)["AKTIVITI UTAMA"].lower())
        self.assertIsNone(_selected_y4_lesson(dict(state, lesson_no="not-a-number")))
        self.assertIsNone(_selected_y4_lesson(dict(state, lesson_no=True,
                                                   textbook_lesson_no=None, lesson=None)))

    def test_years_subjects_and_missing_lessons_unmodified(self):
        for state in (
            {"year": "Tahun 3", "subject": "English", "lesson_no": 1},
            {"year": "Tahun 5", "subject": "English", "lesson_no": 1},
            {"year": "Tahun 4", "subject": "Matematik", "lesson_no": 1},
            {"year": "Tahun 4", "subject": "BM", "lesson_no": 1},
            {"year": "Tahun 4", "subject": "English"},
            {"year": "Tahun 4", "subject": "English", "lesson_no": 161},
        ):
            with self.subTest(state=state):
                self.assertIs(adapt_rows(state, self.existing), self.existing)

    def test_teacher_selected_lessons_and_unreleased_audio_not_overwritten(self):
        for n in sorted(DRAFTS | {30}):
            with self.subTest(lesson=n):
                self.assertIsNone(load_release_candidate(n))
                self.assertIs(adapt_rows({"year": "Year 4", "subject": "English",
                                          "lesson_no": n}, self.existing), self.existing)

    def test_fixed_lessons_use_both_sow_pairs_from_audited_source(self):
        original = json.loads(OFFICIAL_SOW_INDEX.read_text(encoding="utf-8"))
        self.assertEqual(sum(key.startswith("4/") for key in original["lessons"]), 160)
        self.assertEqual({int(k.split("/")[1]) for k, v in original["lessons"].items()
                          if k.startswith("4/") and v["teacher_selected"]}, DRAFTS)
        ready = []
        blocked = []
        for n in range(1, 161):
            item = load_release_candidate(n)
            if item is None:
                blocked.append(n)
                continue
            ready.append(n)
            main = original["lessons"][f"4/{n}"]["main_ls"]
            comp = original["lessons"][f"4/{n}"]["complementary_ls"]
            state = {"year": "Tahun 4", "subject": "Bahasa Inggeris",
                     "lesson_no": n, "sp_code": main, "comp_sp_code": comp}
            rows = adapt_rows(state, self.existing)
            self.assertEqual(rows["MAIN LEARNING STANDARD"], main)
            self.assertEqual(rows["COMPLEMENTARY LEARNING STANDARD"], comp)
            self.assertIn("Teacher:", rows["AKTIVITI UTAMA"])
            self.assertIn("Pupils:", rows["PENUTUP"])
            self.assertNotIn("_DRAFT.md", rows.get("BAHAN BANTU MENGAJAR", ""))
        print("ENGLISH_Y4_RELEASEABLE_FIXED_LESSONS=", len(ready),
              "BLOCKED_REVIEW=", blocked, flush=True)
        self.assertGreaterEqual(len(ready), 140)
        self.assertTrue(DRAFTS.isdisjoint(ready))
        self.assertNotIn(30, ready)

    def test_unapproved_source_and_inconsistent_version_fail_closed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lesson_001.md").write_text(
                "# English Year 4 — Lesson 1: Listening\n"
                "**Main SP:** 3.2.1\n**Complementary SP:** 1.1.1\n"
                "## Set Induction\n**Teacher:** Show.\n**Pupils:** Answer.\n"
                "## Activity 1\n**Teacher:** Guide.\n**Pupils:** Work.\n"
                "## Activity 2\n**Teacher:** Help.\n**Pupils:** Reply.\n"
                "## PBD\n**Teacher:** Check.\n**Pupils:** Correct.\n"
                "## Closure\n**Teacher:** Close.\n**Pupils:** Share.\n"
                "**QA status:** READY — provisional\n", encoding="utf-8")
            self.assertIsNone(load_release_candidate(1, root=root))
            fake = json.loads(OFFICIAL_SOW_INDEX.read_text(encoding="utf-8"))
            fake["version"] = "unreviewed"
            path = root / "index.json"
            path.write_text(json.dumps(fake), encoding="utf-8")
            self.assertIsNone(load_release_candidate(1, index_path=path))

    def test_runtime_installs_once_without_touching_quota_or_callback(self):
        calls = []
        def original(st, ai_text):
            calls.append((dict(st), ai_text))
            return dict(self.existing)
        runtime = types.SimpleNamespace(
            _rph_rows=original,
            _credit_gate=lambda user: "credit-safe",
            callback=lambda *a: "unchanged",
        )
        self.assertTrue(install_rows(runtime))
        self.assertTrue(install_rows(runtime))
        output = runtime._rph_rows(self.state, "old-language-model-rph")
        self.assertNotIn("GENERIC OLD LESSON", output["AKTIVITI UTAMA"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(runtime._credit_gate(4), "credit-safe")
        self.assertEqual(runtime.callback(1, "menu"), "unchanged")

    def test_native_word_pdf_renderers_consume_shared_rph_rows(self):
        # Static integration guard only: actual live PDF delivery remains to verify.
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("def _create_rph_word(", source)
        word = source[source.rfind("def _create_rph_word("):]
        self.assertIn("rph = _rph_rows(s, ai_text)", word[:1200])
        self.assertIn("MAIN LEARNING STANDARD", word[:3200])
        self.assertIn("def create_pdf_file(", source)
        self.assertIn("_rph_rows(s, ai_text)", source)
        wsgi = (ROOT / "tools/run_telegram_with_curriculum_api.py").read_text(
            encoding="utf-8")
        self.assertIn("install_english_y4_rows(telegram_runtime)", wsgi)


if __name__ == "__main__":
    unittest.main()
