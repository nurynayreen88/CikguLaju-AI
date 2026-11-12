"""English Y3 standalone plain-text rows for native Word/PDF, without DB access.

Checks the existing RPH row contract. Teacher approval and live Telegram
downloads remain separate from these technical regression checks.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

import english_y3_standalone_render as renderer


EXAMPLE = """# English Year 3 — Lesson 14: Writing

**Materials:** Student's Book p.11 Activity 1; Teacher's Book p.27

## Set Induction (5 minutes)
**Teacher:** Review the family model. **Pupils:** Recall family words.

## Activity 1 — Preparation (15 minutes)
**Teacher:** Show the family writing tip. **Pupils:** Rehearse sentences.

## Activity 2 — Writing (25 minutes)
**Teacher:** Guide drafting. **Pupils:** Write two sentences.

## Reinforcement / PBD (10 minutes)
**Teacher:** Check capitals. **Pupils:** Revise punctuation.

## Closure (5 minutes)
**Teacher:** Share feedback. **Pupils:** Summarise their learning.

**Resource status:** Unverified audio. NOT READY FOR RELEASE.
**QA status:** Internal developer only.
"""


class EnglishY3RoleLayoutTests(unittest.TestCase):
    def test_year3_lesson14_teacher_pupils_pbd_and_resource_gate(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "lesson_014.md").write_text(EXAMPLE, encoding="utf-8")
            original = {
                "BAHAN BANTU MENGAJAR": "Legacy materials",
                "PENTAKSIRAN": "Legacy PBD",
                "TARIKH": "10/11/2026",
                "REFLEKSI": "Teacher's own reflection",
            }
            with patch.object(renderer, "ROOT", root):
                out = renderer.apply(
                    {"subject": "English", "year": "Tahun 3", "lesson_no": 14}, original
                )
        self.assertIsNot(out, original)
        self.assertEqual(original["PENTAKSIRAN"], "Legacy PBD")
        self.assertEqual(out["TARIKH"], original["TARIKH"])
        self.assertEqual(out["REFLEKSI"], original["REFLEKSI"])
        self.assertIn("Student's Book p.11", out["BAHAN BANTU MENGAJAR"])
        self.assertEqual(out["PENTAKSIRAN"], "Teacher: Check capitals.\nPupils: Revise punctuation.")
        self.assertIn("Teacher: Review", out["SET INDUKSI"])
        self.assertIn("\nPupils: Recall", out["SET INDUKSI"])
        self.assertIn("Activity 1", out["AKTIVITI UTAMA"])
        self.assertIn("\nPupils: Write two sentences", out["AKTIVITI UTAMA"])
        self.assertNotIn("Assessment / PBD", out["AKTIVITI UTAMA"])
        for field in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP"):
            self.assertNotIn("**", out[field])
            self.assertNotIn("NOT READY", out[field])
        self.assertIn("\nPupils: Summarise", out["PENUTUP"])
        self.assertNotIn("Resource status", out["PENUTUP"])

    def test_real_lesson14_rows_preserve_source_and_teacher_choice(self):
        out = renderer.apply(
            {"subject": "Bahasa Inggeris", "year": "Year 3", "lesson_no": "014"},
            {"TARIKH": "13/11/2026", "REFLEKSI": "Teacher supplied"},
        )
        self.assertTrue(out.get("_standalone_y3_source", "").endswith("lesson_014.md"))
        self.assertIn("Student's Book p.11", out["BAHAN BANTU MENGAJAR"])
        self.assertIn("\nPupils:", out["SET INDUKSI"])
        self.assertIn("\nPupils:", out["AKTIVITI UTAMA"])
        self.assertIn("\nPupils:", out["PENTAKSIRAN"])
        self.assertNotIn("**", out["AKTIVITI UTAMA"])
        self.assertNotIn("NOT READY FOR RELEASE", out["PENUTUP"])
        self.assertEqual(out["TARIKH"], "13/11/2026")
        self.assertEqual(out["REFLEKSI"], "Teacher supplied")

    def test_lesson14_assessment_does_not_leak_author_working_path(self):
        # Preserve the actual pupil writing task but not the internal source
        # filename or developer-only source label in teacher-facing Word/PDF.
        out = renderer.apply(
            {"subject": "English", "year": "Year 3", "lesson_no": 14}, {}
        )
        assessment = out["PENTAKSIRAN"]
        self.assertIn("Use a checklist to assess two family-description sentences", assessment)
        self.assertIn("Teacher: Use a checklist", assessment)
        self.assertIn("Pupils: Submit two family-description sentences", assessment)
        self.assertNotIn("CikguLaju original assessment", assessment)
        self.assertNotIn("materials/lesson_", assessment)
        self.assertNotIn("`", assessment)

    def test_supplementary_materials_require_separate_teacher_preparation(self):
        # These original worksheets exist in the project source, but are not
        # bundled in the one-page RPH download. Do not imply they were sent.
        for lesson in (25, 70, 87, 155):
            with self.subTest(lesson=lesson):
                rows = renderer.apply(
                    {"subject": "English", "year": "Year 3", "lesson_no": lesson}, {}
                )
                pbd = rows["PENTAKSIRAN"]
                self.assertIn("prepare separately", pbd)
                self.assertNotIn("materials/lesson_", pbd)
                self.assertNotIn("CikguLaju material", pbd)
                self.assertIn("Pupils:", pbd)

    def test_unrelated_year_subject_and_invalid_lesson_fail_closed(self):
        for state in (
            {"subject": "English", "year": "Year 2", "lesson_no": 14},
            {"subject": "Matematik", "year": "Year 3", "lesson_no": 14},
            {"subject": "English", "year": "Year 3", "lesson_no": True},
            {"subject": "English", "year": "Year 3", "lesson_no": 1.5},
            {"subject": "English", "year": "Year 3", "lesson_no": "../14"},
        ):
            base = {"PENTAKSIRAN": "untouched"}
            self.assertIs(renderer.apply(state, base), base)

    def test_160_lessons_mapping_does_not_leak_markdown_roles(self):
        for n in range(1, 161):
            with self.subTest(lesson=n):
                out = renderer.apply(
                    {"subject": "English", "year": "3", "lesson_no": n},
                    {"TARIKH": "10/11/2026"},
                )
                self.assertIn("_standalone_y3_source", out)
                for field in ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP"):
                    self.assertTrue(out[field].strip(), (n, field))
                    self.assertNotIn("**Teacher:**", out[field])
                    self.assertNotIn("**Pupils:**", out[field])
                    self.assertNotIn("NOT READY FOR RELEASE", out[field])
                    self.assertNotIn("CikguLaju original assessment", out[field])
                    self.assertNotIn("`materials/lesson_", out[field])
                    self.assertNotIn("**Resource status:", out[field])


if __name__ == "__main__":
    unittest.main()
