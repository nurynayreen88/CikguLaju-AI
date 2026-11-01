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

    def test_missing_files_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            rows = audit(Path(folder))
        self.assertEqual(len(rows), 160)
        self.assertTrue(all("missing_lesson_file" in r["blockers"] for r in rows))


if __name__ == "__main__":
    unittest.main()
