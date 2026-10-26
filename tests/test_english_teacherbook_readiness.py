"""Unit tests for English Teacher's Book readiness inventory.

Run: python -m unittest tests.test_english_teacherbook_readiness
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import check_english_teacherbook_readiness as check


class ReadinessTest(unittest.TestCase):
    def test_480_files_counted_without_claiming_verification(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for year in (1, 2, 3):
                folder = root / f"year{year}"
                folder.mkdir(parents=True)
                for lesson in range(1, 161):
                    (folder / f"lesson_{lesson:03d}.md").write_text(
                        f"# Lesson {lesson}\n## Activity 1\n## Assessment / PBD\n"
                        "**QA status:** DRAFT; Teacher's Book pending verification\n",
                        encoding="utf-8",
                    )
            with patch.object(check, "BASE", root), patch.object(check, "OUT", root / "report.json"):
                self.assertTrue(check.audit())
                import json
                report = json.loads((root / "report.json").read_text())
                for year in ("1", "2", "3"):
                    self.assertEqual(report["years"][year]["present"], 160)
                    self.assertEqual(len(report["years"][year]["explicit_draft"]), 160)
                    self.assertEqual(len(report["years"][year]["no_teacherbook_attestation"]), 160)

    def test_missing_lesson_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with patch.object(check, "BASE", root), patch.object(check, "OUT", root / "report.json"):
                self.assertFalse(check.audit())


if __name__ == "__main__":
    unittest.main()
