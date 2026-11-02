"""Year 2 standalone adapter regression checks; isolated from database."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import english_y2_standalone_render as adapter

LESSON = """# English Year 2 Lesson 14
**Materials:** Student's Book p.10; Workbook p.8 Activity 1
## Set Induction (5 minutes)
**Teacher:** Model. **Pupils:** Respond.
## Activity 1 (20 minutes)
**Teacher:** Guide. **Pupils:** Practise.
## Reinforcement / PBD (10 minutes)
**Teacher:** Check Workbook task. **Pupils:** Correct answers.
## Closure (5 minutes)
**Teacher:** Summarise. **Pupils:** Reflect.
**QA:** Internal note.
"""

class Year2Tests(unittest.TestCase):
    def test_pbd_roles_materials(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lesson_014.md").write_text(LESSON, encoding="utf-8")
            with patch.object(adapter, "ROOT", Path(tmp)):
                result = adapter.apply({"subject":"English","year":"Year 2","lesson_no":14}, {})
            self.assertIn("Workbook p.8", result["BAHAN BANTU MENGAJAR"])
            self.assertIn("Check Workbook task", result["PENTAKSIRAN"])
            self.assertNotIn("**", result["AKTIVITI UTAMA"])
            self.assertNotIn("Internal note", result["PENUTUP"])

    def test_other_year_untouched(self):
        original = {"PENUTUP":"original"}
        self.assertIs(adapter.apply({"subject":"English","year":"Year 4","lesson_no":14}, original), original)

if __name__ == "__main__":
    unittest.main()
