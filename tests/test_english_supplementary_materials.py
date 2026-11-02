"""Exact-match supplementary worksheet registry regression tests."""
import unittest
from pathlib import Path
from unittest.mock import patch
import english_supplementary_materials as registry


class SupplementaryMaterialsTests(unittest.TestCase):
    def test_all_four_known_worksheets_exist(self):
        for lesson in (4, 79, 89, 90):
            with self.subTest(lesson=lesson):
                result = registry.available({"subject": "English", "year": "Year 4", "lesson_no": lesson})
                self.assertEqual(len(result), 1)
                self.assertTrue(Path(result[0]["path"]).is_file())
                self.assertEqual(result[0]["lesson"], lesson)

    def test_does_not_show_material_for_other_lessons_or_years(self):
        for state in (
            {"subject": "English", "year": "Year 4", "lesson_no": 80},
            {"subject": "English", "year": "Year 3", "lesson_no": 79},
            {"subject": "Mathematics", "year": "Year 4", "lesson_no": 79},
            {"subject": "English", "year": "Year 4", "lesson_no": "../079"},
            {},
        ):
            with self.subTest(state=state):
                self.assertEqual(registry.available(state), [])

    def test_missing_file_never_advertised(self):
        with patch.object(registry, "ROOT", Path("/missing/supplementary_materials")):
            self.assertEqual(registry.available({"subject": "English", "year": "4", "lesson_no": 4}), [])


if __name__ == "__main__":
    unittest.main()
