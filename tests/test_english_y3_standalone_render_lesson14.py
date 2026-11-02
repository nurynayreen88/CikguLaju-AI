"""Regression checks for English Year 3 standalone mapping (no DB/network)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import english_y3_standalone_render as adapter


LESSON = """# English Year 3 — Lesson 14: Writing
**Materials:** Student's Book p.11 Activity 1; Teacher's Book p.27; optional family photos

## Set Induction (5 minutes)
**Teacher:** Review family words from Lesson 13. **Pupils:** Recall prior learning.

## Activity 1 — Guided preparation (15 minutes)
**Teacher:** Show a family model. **Pupils:** Read and rehearse.

## Activity 2 — Main task (25 minutes)
**Teacher:** Guide drafting. **Pupils:** Write two sentences.

## Reinforcement / PBD (10 minutes)
**CikguLaju original assessment:** Write three family sentences.
**Teacher:** Check capitals. **Pupils:** Correct punctuation.

## Closure (5 minutes)
**Teacher:** Share a sentence. **Pupils:** Reflect.
"""


class Year3AdapterTests(unittest.TestCase):
    def test_lesson14_maps_materials_pbd_and_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lesson_014.md").write_text(LESSON, encoding="utf-8")
            state = {"subject": "Bahasa Inggeris", "year": "Tahun 3", "lesson_no": 14}
            with patch.object(adapter, "ROOT", Path(tmp)):
                rows = adapter.apply(state, {"BAHAN BANTU MENGAJAR": "generic", "PENTAKSIRAN": "generic"})
            self.assertIn("Student's Book p.11", rows["BAHAN BANTU MENGAJAR"])
            self.assertIn("Write three family sentences", rows["PENTAKSIRAN"])
            self.assertIn("Lesson 13", rows["SET INDUKSI"])
            self.assertIn("Teacher:\\n", rows["SET INDUKSI"])
            self.assertIn("Pupils:", rows["AKTIVITI UTAMA"])
            self.assertNotIn("**", rows["AKTIVITI UTAMA"])

    def test_non_year3_untouched(self):
        state = {"subject": "Bahasa Inggeris", "year": "Tahun 2", "lesson_no": 14}
        original = {"PENTAKSIRAN": "unchanged"}
        self.assertIs(adapter.apply(state, original), original)


if __name__ == "__main__":
    unittest.main()
