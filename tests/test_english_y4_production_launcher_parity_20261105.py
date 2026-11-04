"""Production-launcher English Y4 Word/PDF row path regression (offline).

Runs the already-installed bridge, not a replacement adapter. No Flask import,
Telegram API, user credits, payments, database, or production writes.
"""
import unittest
from pathlib import Path
from types import SimpleNamespace

from web.english_y4_standalone_runtime import adapt_rows, install_rows, _sow_record

ROOT = Path(__file__).resolve().parents[1]
PENDING = {16, 30, 32, 48, 64, 80, 96, 112, 128, 144, 160}
BASE = {
    "TAJUK": "GENERIC OLD RPH",
    "MAIN CONTENT STANDARD": "OLD",
    "MAIN LEARNING STANDARD": "OLD",
    "COMPLEMENTARY LEARNING STANDARD": "OLD",
    "OBJEKTIF PEMBELAJARAN": "OLD OBJECTIVE",
    "SET INDUKSI": "OLD INDUCTION",
    "AKTIVITI UTAMA": "OLD ACTIVITIES",
    "PENTAKSIRAN": "OLD ASSESSMENT",
    "PENUTUP": "OLD CLOSURE",
    "TARIKH": "2026-11-05",
    "KELAS": "4 Amanah",
    "BILANGAN MURID": "30",
    "REFLEKSI": "Teacher-entered reflection",
}


def state(lesson, **extra):
    s = {"subject": "English", "year": "Year 4", "lesson_no": lesson}
    s.update(extra)
    return s


class EnglishYear4ActualLauncherParity(unittest.TestCase):
    def test_launcher_really_installs_word_pdf_bridge_before_pending_and_audio_guards(self):
        launcher = (ROOT / "tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        installation = "ENGLISH_Y4_WORD_PDF_ROWS_ACTIVE = install_english_y4_rows(telegram_runtime)"
        self.assertIn("from web.english_y4_standalone_runtime import install_rows", launcher)
        self.assertIn(installation, launcher)
        self.assertIn("ENGLISH_Y4_PENDING_DRAFT_PREVIEW_ACTIVE = install_y4_pending_drafts(telegram_runtime)", launcher)
        self.assertIn("ENGLISH_Y4_L030_AUDIO_GUARD_ACTIVE = install_y4_l030_audio_guard(telegram_runtime)", launcher)
        self.assertLess(launcher.index(installation), launcher.index("ENGLISH_Y4_PENDING_DRAFT_PREVIEW_ACTIVE ="))
        self.assertLess(launcher.index(installation), launcher.index("ENGLISH_Y4_L030_AUDIO_GUARD_ACTIVE ="))

    def test_all_160_official_y4_ids_fixed_149_vs_pending_11(self):
        upgraded = set()
        untouched = set()
        for lesson in range(1, 161):
            with self.subTest(lesson=lesson):
                original = dict(BASE)
                out = adapt_rows(state(lesson), original)
                self.assertEqual(original, BASE)  # no in-place mutation
                if lesson in PENDING:
                    untouched.add(lesson)
                    self.assertIs(out, original)
                    continue
                sow = _sow_record(lesson)
                self.assertIsNotNone(sow)
                self.assertIsNot(out, original)
                self.assertEqual(out["MAIN LEARNING STANDARD"], sow["main_ls"])
                self.assertEqual(out["COMPLEMENTARY LEARNING STANDARD"], sow["complementary_ls"])
                self.assertNotIn("GENERIC OLD RPH", out["TAJUK"])
                self.assertNotIn("OLD ACTIVITIES", out["AKTIVITI UTAMA"])
                self.assertIn("Teacher:", out["AKTIVITI UTAMA"])
                self.assertIn("Pupils:", out["AKTIVITI UTAMA"])
                self.assertNotIn("QA status:", out["AKTIVITI UTAMA"] + out["PENUTUP"])
                for key in ("TARIKH", "KELAS", "BILANGAN MURID", "REFLEKSI"):
                    self.assertEqual(out[key], original[key])
                upgraded.add(lesson)
        self.assertEqual(len(upgraded), 149)
        self.assertEqual(untouched, PENDING)

    def test_production_install_rows_fake_runtime_safe_for_lesson14(self):
        fake = SimpleNamespace(_rph_rows=lambda _state, *a, **kw: dict(BASE))
        self.assertTrue(install_rows(fake))
        self.assertTrue(fake.CIKGULAJU_ENGLISH_Y4_RPH_ROWS_ACTIVE)
        out = fake._rph_rows(state(14), "legacy AI")
        self.assertEqual(out["MAIN LEARNING STANDARD"], "4.3.1")
        self.assertIn("Writing", out["TAJUK"])
        self.assertIn("punctuation", (out["PENTAKSIRAN"] + out["AKTIVITI UTAMA"]).lower())
        self.assertNotIn("OLD ACTIVITIES", out["AKTIVITI UTAMA"])
        self.assertEqual(out["TARIKH"], BASE["TARIKH"])
        # Re-installing the same hook must not wrap recursively.
        self.assertTrue(install_rows(fake))
        self.assertEqual(fake._rph_rows(state(14))["MAIN LEARNING STANDARD"], "4.3.1")

    def test_l030_and_teacher_choice_not_promoted_by_fixed_sow_bridge(self):
        for n in sorted(PENDING):
            with self.subTest(lesson=n):
                self.assertIs(adapt_rows(state(n), BASE), BASE)

    def test_other_year_subject_or_stale_standard_falls_back(self):
        samples = (
            state(14, year="Year 5"),
            state(14, subject="Mathematics"),
            state(14, sp_code="1.2.5"),
            state(14, comp_sp_code="3.1.2"),
            state(True),
            state(14.0),
        )
        for s in samples:
            with self.subTest(state=s):
                self.assertIs(adapt_rows(s, BASE), BASE)


if __name__ == "__main__":
    unittest.main()
