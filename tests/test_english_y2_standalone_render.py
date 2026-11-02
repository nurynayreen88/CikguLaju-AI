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
**QA:** Internal note.\n**Status:** READY
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

    def test_missing_assessment_preserves_existing_rph(self):
        incomplete = """# Lesson 14
## Set induction
**Teacher:** Start.
## Activity 1
**Pupils:** Write.
## Closure
**Teacher:** Finish.
"""
        original = {"AKTIVITI UTAMA": "existing"}
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lesson_014.md").write_text(incomplete, encoding="utf-8")
            with patch.object(adapter, "ROOT", Path(tmp)):
                result = adapter.apply({"subject":"English","year":"2","lesson_no":14}, original)
            self.assertIs(result, original)

    def test_real_lesson_14_qa_footer_not_in_closure(self):
        result = adapter.apply({"subject":"English","year":"Year 2","lesson_no":14}, {})
        self.assertEqual(result, {})  # Source QA status remains DRAFT

    def test_real_lesson_1_non_textbook(self):
        result = adapter.apply({"subject":"English","year":"Year 2","lesson_no":1}, {})
        self.assertEqual(result, {})  # Source QA status remains DRAFT

    def test_activity_ten_not_mistaken_for_activity_one(self):
        lesson = """# Lesson 14
**Status:** READY
## Set Induction
**Teacher:** Begin.
## Activity 10
**Pupils:** Wrong numbered activity.
## Activity 2
**Pupils:** Correct numbered activity.
## Assessment
**Teacher:** Check learning.
## Closure
**Pupils:** Reflect.
"""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "lesson_014.md").write_text(lesson, encoding="utf-8")
            with patch.object(adapter, "ROOT", Path(tmp)):
                result = adapter.apply({"subject":"English","year":"2","lesson_no":14}, {})
            self.assertIn("Correct numbered activity", result["AKTIVITI UTAMA"])
            self.assertNotIn("Wrong numbered activity", result["AKTIVITI UTAMA"])

    def test_other_year_untouched(self):
        original = {"PENUTUP":"original"}
        self.assertIs(adapter.apply({"subject":"English","year":"Year 4","lesson_no":14}, original), original)

if __name__ == "__main__":
    unittest.main()
