"""Isolated Year 4 standalone adapter regression tests (no DB/network)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import english_y4_standalone_render as adapter

LESSON = """# English Year 4 — Lesson 14
**References:** SB model email; TB pp.26–27

## Set induction (10 minutes)
**Teacher:** Show a model email.
**Pupils:** Read the email.

## Activity 1 (15 minutes)
**Teacher:** Model punctuation.
**Pupils:** Mark punctuation.

## Reinforcement / PBD (10 minutes)
**Teacher:** Check email.
**Pupils:** Correct email.

## Closure (5 minutes)
**Teacher:** Summarise.
**Pupils:** Reflect.

**Status:** DRAFT; not for classroom output.
"""

class Year4Tests(unittest.TestCase):
    def test_lesson_14_phases_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lesson_014.md").write_text(LESSON, encoding="utf-8")
            with patch.object(adapter, "ROOT", Path(tmp)):
                result = adapter.apply({"subject":"English","year":"Year 4","lesson_no":14},
                                       {"BAHAN BANTU MENGAJAR":"generic"})
            self.assertIn("SB model email", result["BAHAN BANTU MENGAJAR"])
            self.assertIn("Check email", result["PENTAKSIRAN"])
            self.assertIn("Model punctuation", result["AKTIVITI UTAMA"])
            self.assertNotIn("DRAFT", result["PENUTUP"])
            self.assertNotIn("**", result["AKTIVITI UTAMA"])

    def test_project_pbd(self):
        lesson = """# Lesson 80
**Resources:** SOW teacher-selected topic
## Set induction (10 minutes)
**Teacher:** Introduce topic.
**Pupils:** Discuss.
## Activity 1 (15 minutes)
**Teacher:** Guide project.
**Pupils:** Plan.
## PBD / reinforcement (10 minutes)
**Teacher:** Check criteria.
**Pupils:** Present.
## Closure (5 minutes)
**Teacher:** Reflect.
**Pupils:** Respond.
"""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lesson_080.md").write_text(lesson, encoding="utf-8")
            with patch.object(adapter, "ROOT", Path(tmp)):
                rows = adapter.apply({"subject":"English","year":"4","lesson_no":80}, {})
            self.assertIn("Check criteria", rows["PENTAKSIRAN"])
            self.assertNotIn("Workbook", rows["BAHAN BANTU MENGAJAR"])

    def test_inline_pbd_not_leaked_into_closure(self):
        lesson = """# Lesson 80
## Set induction
**Teacher:** Introduce.
## Activity 1
**Pupils:** Prepare a poster.
## Closure
**Teacher:** Summarise.
**PBD:** Observe presentation.
**Differentiation:** Give sentence frames.
"""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lesson_080.md").write_text(lesson, encoding="utf-8")
            with patch.object(adapter, "ROOT", Path(tmp)):
                result = adapter.apply({"subject":"English","year":"Year 4","lesson_no":80}, {})
            self.assertEqual(result["PENTAKSIRAN"], "Observe presentation.")
            self.assertNotIn("Differentiation", result["PENUTUP"])
            self.assertNotIn("Observe presentation", result["PENUTUP"])

    def test_missing_lesson_preserves_existing_rows(self):
        original = {"PENUTUP": "existing"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(adapter, "ROOT", Path(tmp)):
                result = adapter.apply({"subject":"English","year":"4","lesson_no":99}, original)
            self.assertIs(result, original)

    def test_invalid_lesson_preserves_existing_rows(self):
        original = {"PENUTUP": "existing"}
        self.assertIs(adapter.apply({"subject":"English","year":"4","lesson_no":161}, original), original)

    def test_year3_untouched(self):
        original = {"PENUTUP":"unchanged"}
        self.assertIs(adapter.apply({"subject":"English","year":"Year 3","lesson_no":14}, original), original)

if __name__ == "__main__":
    unittest.main()
