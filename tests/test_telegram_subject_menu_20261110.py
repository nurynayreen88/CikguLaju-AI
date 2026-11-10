"""Regression: unavailable language subjects should not be in Telegram menu.

Only validates teacher-facing menu constants. It does not delete language
curriculum data or remove access to existing records.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "app.py"


class SubjectMenuGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), str(SOURCE))
        cls.assignments = {}
        for node in tree.body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id in ("SUBJECTS", "SUBJECTS_BY_GRADE"):
                    try:
                        value = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        continue
                    cls.assignments.setdefault(target.id, []).append(value)

    def test_two_menu_definitions_are_conservatively_aligned(self):
        subjects = self.assignments.get("SUBJECTS", [])
        grades = self.assignments.get("SUBJECTS_BY_GRADE", [])
        self.assertEqual(len(subjects), 2)
        self.assertEqual(len(grades), 2)
        for menu in subjects:
            codes = [code for label, code in menu]
            self.assertNotIn("Bahasa Cina", codes)
            self.assertNotIn("Bahasa Tamil", codes)
            self.assertIn("Bahasa Melayu", codes)
            self.assertIn("Bahasa Inggeris", codes)
            self.assertIn("Matematik", codes)
        for grade_map in grades:
            y1 = grade_map["Tahun 1"]
            self.assertNotIn("Bahasa Cina", y1)
            self.assertNotIn("Bahasa Tamil", y1)
            self.assertIn("Bahasa Melayu", y1)
            self.assertIn("Matematik", y1)

    def test_no_additional_grade_subjects_modified(self):
        a, b = self.assignments["SUBJECTS_BY_GRADE"]
        for year in set(a).union(b):
            self.assertEqual(a.get(year), b.get(year))


if __name__ == "__main__":
    unittest.main()
