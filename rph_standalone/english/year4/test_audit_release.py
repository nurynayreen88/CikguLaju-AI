import tempfile
import unittest
from pathlib import Path
from audit_standalone_release import audit


class ReleaseAuditTests(unittest.TestCase):
    def test_160_lessons_pending(self):
        rows = audit()
        self.assertEqual(len(rows), 160)
        self.assertEqual([r["lesson"] for r in rows], list(range(1, 161)))
        self.assertTrue(all(r["approval"] == "PENDING" for r in rows))

    def test_teacher_selected_gates(self):
        rows = {r["lesson"]: r for r in audit()}
        for number in (80, 96, 112, 128, 144, 160):
            self.assertIn("teacher_selected_main_sp", rows[number]["blockers"])
            self.assertIn("teacher_selected_complementary_sp", rows[number]["blockers"])

    def test_audio_disc_gates(self):
        rows = {r["lesson"]: r for r in audit()}
        for number in (139, 145, 147):
            self.assertIn("manual_source_audio_review", rows[number]["blockers"])
            self.assertTrue(any("audio_disc" in reason for reason in rows[number]["blockers"]))

    def test_empty_sections_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "lesson_001.md").write_text(
                "**Topic:** Sample\\n**Main SP:** Listening 1.2.2\\n"
                "**Complementary SP:** Speaking 2.1.1\\n"
                "## Set induction\\n\\n## Activity 1\\nTask\\n"
                "## Activity 2\\nTask\\n## Closure\\n\\n",
                encoding="utf-8")
            row = audit(root)[0]
        self.assertIn("renderer_empty_set_induction", row["blockers"])
        self.assertIn("renderer_empty_closure", row["blockers"])
        self.assertIn("renderer_missing_assessment", row["blockers"])

    def test_missing_linked_resource_is_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "lesson_001.md").write_text(
                "**Topic:** Sample\\n**Main SP:** Listening 1.2.2\\n"
                "**Complementary SP:** Speaking 2.1.1\\n"
                "**References:** resources/lesson_001_missing_DRAFT.md\\n"
                "## Set induction\\nStart\\n## Activity 1\\nTask\\n"
                "## Activity 2\\nTask\\n## PBD / reinforcement\\nAssess\\n"
                "## Closure\\nEnd\\n**PBD:** Check response\\n",
                encoding="utf-8")
            row = audit(root)[0]
        self.assertIn(
            "missing_linked_resource:resources/lesson_001_missing_DRAFT.md",
            row["blockers"])

    def test_missing_files_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            rows = audit(Path(folder))
        self.assertEqual(len(rows), 160)
        self.assertTrue(all("missing_lesson_file" in r["blockers"] for r in rows))


if __name__ == "__main__":
    unittest.main()
