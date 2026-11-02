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

    def test_year3_untouched(self):
        original = {"PENUTUP":"unchanged"}
        self.assertIs(adapter.apply({"subject":"English","year":"Year 3","lesson_no":14}, original), original)

if __name__ == "__main__":
    unittest.main()
