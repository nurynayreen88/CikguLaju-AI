"""Authoritative curriculum source contract must fail closed by default."""
import unittest
from web.authoritative_curriculum_source import (
    CurriculumKey, UnconfiguredCurriculumSource, SharedSourceUnavailable,
    validate_curriculum_key,
)


class AuthoritativeCurriculumTests(unittest.TestCase):
    def test_unconfigured_source_never_returns_preview_data(self):
        source = UnconfiguredCurriculumSource()
        for operation in (
            lambda: source.list_subjects(2),
            lambda: source.list_units(2, "ENGLISH"),
            lambda: source.list_lessons(2, "ENGLISH", "Unit 1"),
            lambda: source.get_approved_materials(CurriculumKey(2, "ENGLISH", "1")),
        ):
            with self.subTest(operation=operation), self.assertRaises(SharedSourceUnavailable):
                operation()

    def test_curriculum_key_validation(self):
        validate_curriculum_key(CurriculumKey(2, "ENGLISH", "12"))
        for key in (
            CurriculumKey(0, "ENGLISH", "12"),
            CurriculumKey(2, "", "12"),
            CurriculumKey(2, "ENGLISH", ""),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_curriculum_key(key)


if __name__ == "__main__":
    unittest.main()
