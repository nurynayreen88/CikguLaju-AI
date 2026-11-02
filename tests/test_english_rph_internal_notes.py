"""Regression checks: internal QA metadata must not reach teacher-facing RPH."""
import unittest
from unittest.mock import patch

import english_standalone_adapter as adapter
import english_y2_standalone_render as y2
import english_y3_standalone_render as y3


class InternalNotesTests(unittest.TestCase):
    def test_reader_removes_qa_status_but_keeps_closure(self):
        text = "# English Year 2 Lesson 4\n## Closure (5 minutes)\n**Teacher:** Ask pupils.\n**Pupils:** Respond.\n\n**QA status:** SOURCE-CHECKED DRAFT; do not publish.\n"
        result = adapter._strip_internal_review_notes(text)
        self.assertIn("**Pupils:** Respond.", result)
        self.assertNotIn("SOURCE-CHECKED", result)
        self.assertNotIn("QA status", result)

    def test_reader_keeps_following_sections(self):
        text = "# Lesson 4\n**QA:** Pending\n## Closure (5 minutes)\n**Teacher:** Finish.\n"
        result = adapter._strip_internal_review_notes(text)
        self.assertNotIn("Pending", result)
        self.assertIn("**Teacher:** Finish.", result)

    def test_real_year2_lesson4_does_not_leak_internal_status(self):
        content = adapter.load_english_rph(2, 4)
        self.assertIsNotNone(content)
        self.assertIn("Workbook", content)
        self.assertNotIn("SOURCE-CHECKED DRAFT", content)
        self.assertNotIn("do not publish", content)

    def test_year2_renderer_preserves_workbook_and_removes_qa(self):
        st = {"subject": "English", "year": "Tahun 2", "lesson_no": 4}
        rows = {"BAHAN BANTU MENGAJAR": "original"}
        result = y2.apply(st, rows)
        self.assertIn("Workbook", str(result))
        self.assertNotIn("SOURCE-CHECKED DRAFT", str(result))
        self.assertNotIn("do not publish", str(result))

    def test_year3_renderer_does_not_leak_review_notes(self):
        source = ("## Set Induction (5 minutes)\nTeacher: greet\n"
                  "## Activity 1 (20 minutes)\nPupils: work\n"
                  "## Closure (5 minutes)\nTeacher: conclude\n"
                  "**QA status:** NOT READY FOR RELEASE\n")
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp:
            path = Path(temp) / "lesson_004.md"
            path.write_text(source, encoding="utf-8")
            with patch.object(y3, "ROOT", Path(temp)):
                result = y3.apply({"subject": "English", "year": "3", "lesson_no": 4}, {})
        self.assertIn("Teacher: conclude", result["PENUTUP"])
        self.assertNotIn("NOT READY", str(result))


if __name__ == "__main__":
    unittest.main()
