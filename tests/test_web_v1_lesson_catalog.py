"""Tests for the read-only, fail-closed lesson catalog contract."""
import unittest

from web_v1_lesson_catalog import (
    LessonSummary, UnconfiguredCatalog, validate_catalog_query
)


class LessonCatalogContractTests(unittest.TestCase):
    def test_unconfigured_catalog_never_returns_fake_lessons(self):
        with self.assertRaisesRegex(RuntimeError, "not connected"):
            UnconfiguredCatalog().list_lessons(year=3, subject_code="ENGLISH")

    def test_valid_query(self):
        validate_catalog_query(3, "ENGLISH")
        validate_catalog_query(1, "PENDIDIKAN_ISLAM")

    def test_rejects_bad_year(self):
        for year in (0, 7, True, "3"):
            with self.subTest(year=year), self.assertRaises(ValueError):
                validate_catalog_query(year, "ENGLISH")

    def test_rejects_bad_subject(self):
        for subject in ("", "ENGLISH/../../", "A B", "x" * 33, None):
            with self.subTest(subject=subject), self.assertRaises(ValueError):
                validate_catalog_query(3, subject)

    def test_lesson_is_immutable(self):
        lesson = LessonSummary("EN3-001", 3, "ENGLISH", "Welcome", "Lesson 1")
        with self.assertRaises(AttributeError):
            lesson.lesson_title = "changed"


if __name__ == "__main__":
    unittest.main()
