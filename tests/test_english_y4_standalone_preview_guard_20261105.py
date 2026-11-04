"""Offline regression for Year 4 staging preview; no Telegram or database calls."""
import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import english_y4_standalone_render as adapter

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = {"SET INDUKSI": "Current production RPH", "PENUTUP": "Untouched"}


class EnglishYear4Preview(unittest.TestCase):
    def state(self, lesson, year="Year 4", subject="English"):
        return {"year": year, "subject": subject, "lesson_no": lesson}

    def test_default_off_even_for_source_provisional_ready(self):
        result = adapter.apply(self.state(14), ORIGINAL)
        self.assertIs(result, ORIGINAL)

    def test_actual_year4_lesson14_preview_keeps_source_and_clean_roles(self):
        source = adapter.ROOT / "lesson_014.md"
        before = source.read_bytes()
        result = adapter.apply(self.state(14), ORIGINAL, allow_provisional=True)
        self.assertIsNot(result, ORIGINAL)
        self.assertEqual(ORIGINAL["SET INDUKSI"], "Current production RPH")
        self.assertIn("personal details", result["SET INDUKSI"].lower())
        self.assertIn("Teacher:", result["AKTIVITI UTAMA"])
        self.assertIn("Pupils:", result["AKTIVITI UTAMA"])
        self.assertIn("p.26", result["BAHAN BANTU MENGAJAR"])
        self.assertIn("punctuation", result["PENTAKSIRAN"].lower())
        self.assertIn("correct", result["PENUTUP"].lower())
        self.assertTrue(result["_standalone_y4_preview_only"])
        teacher_text = "\n".join(result[k] for k in
            ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP"))
        self.assertNotIn("QA status:", teacher_text)
        self.assertNotIn("READY — provisional", teacher_text)
        self.assertNotIn("PBD and differentiation", result["PENUTUP"])
        self.assertNotIn("**", teacher_text)
        self.assertEqual(source.read_bytes(), before)

    def test_year4_lesson30_audio_and_pbd_not_approved(self):
        self.assertIs(adapter.apply(self.state(30), ORIGINAL, allow_provisional=True), ORIGINAL)

    def test_real_audio_dependent_lesson1_not_substituted(self):
        self.assertIs(adapter.apply(self.state(1), ORIGINAL, allow_provisional=True), ORIGINAL)

    def test_all_ten_teacher_selected_year4_lessons_keep_existing_route(self):
        for n in (16, 32, 48, 64, 80, 96, 112, 128, 144, 160):
            with self.subTest(lesson=n):
                self.assertIs(adapter.apply(self.state(n), ORIGINAL, allow_provisional=True), ORIGINAL)

    def test_invalid_or_other_year_state_no_override(self):
        for state in (
            self.state(True), self.state(14.0), self.state("-14"),
            self.state("١٤"), self.state(0), self.state(161),
            self.state("14", year="Year 3"), self.state("14", subject="BM"),
            {"year": "Year 4", "subject": "English", "lesson_no": False, "lesson": 14},
        ):
            with self.subTest(state=state):
                self.assertIs(adapter.apply(state, ORIGINAL, allow_provisional=True), ORIGINAL)

    def test_malformed_candidate_and_unapproved_source_fail_closed(self):
        template = (
            "# Lesson 14\n"
            "**Main SP:** 4.3.1\n"
            "**Complementary SP:** 2.1.5\n"
            "**QA status:** READY — provisional, pending teacher's final review.\n"
            "## Set induction (5 minutes)\n"
            "**Teacher:** Ask. **Pupils:** Respond.\n"
            "## Activity 1 (15 minutes)\n"
            "**Teacher:** Guide. **Pupils:** Work.\n"
            "## Reinforcement / PBD (10 minutes)\n"
            "**Teacher:** Check. **Pupils:** Show.\n"
            "## Closure (5 minutes)\n"
            "**Teacher:** Close. **Pupils:** Reflect.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "lesson_014.md"
            with patch.object(adapter, "ROOT", Path(tmp)):
                for fixture in (
                    template,  # only 35 of 60 minutes and no Activity 2
                    template.replace("READY — provisional", "NOT READY FOR RELEASE"),
                    template.replace("4.3.1", "Teacher-selected"),
                ):
                    target.write_text(fixture, encoding="utf-8")
                    self.assertIs(adapter.apply(self.state(14), ORIGINAL, allow_provisional=True), ORIGINAL)

    def test_app_wrapper_is_default_off_and_preserves_prior_renderer(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        marker = "# === ENGLISH YEAR 4 STANDALONE PREVIEW (STAGING OPT-IN; NO RELEASE) ==="
        self.assertEqual(app.count(marker), 1)
        guard = app.split(marker, 1)[1]
        self.assertIn("_EN_Y4_STANDALONE_PREVIEW_BASE_20261105 = _rph_rows", guard)
        self.assertIn("CIKGULAJU_ENGLISH_Y4_STANDALONE_PREVIEW_20261105", guard)
        self.assertIn("!= '1'", guard)
        self.assertIn("from english_y4_standalone_render import apply", guard)
        self.assertIn("return rows", guard)
        ast.parse(guard)  # No Python syntax regression in the appended wrapper.


if __name__ == "__main__":
    unittest.main()
