"""Shared curriculum source adapter contract for Telegram and Web.

Only an explicitly configured shared service may be treated as authoritative.
No implicit fallback to a Web snapshot, a Git checkout or an old local SQLite
file. Adapters can be added after the production data ownership audit.
"""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class CurriculumKey:
    year: int
    subject_code: str
    lesson_id: str


class AuthoritativeCurriculumSource(Protocol):
    def list_subjects(self, year: int) -> Sequence[dict]:
        ...

    def list_units(self, year: int, subject_code: str) -> Sequence[dict]:
        ...

    def list_lessons(self, year: int, subject_code: str, unit: str) -> Sequence[dict]:
        ...

    def get_approved_materials(self, key: CurriculumKey) -> Sequence[dict]:
        ...


class SharedSourceUnavailable(RuntimeError):
    pass


class UnconfiguredCurriculumSource:
    """Do not silently use a preview snapshot when shared source is absent."""
    def _unavailable(self):
        raise SharedSourceUnavailable("Authoritative Telegram/Web curriculum source not connected")

    def list_subjects(self, year):
        self._unavailable()

    def list_units(self, year, subject_code):
        self._unavailable()

    def list_lessons(self, year, subject_code, unit):
        self._unavailable()

    def get_approved_materials(self, key):
        self._unavailable()


def validate_curriculum_key(key):
    if not isinstance(key, CurriculumKey):
        raise ValueError("Invalid curriculum key")
    if type(key.year) is not int or key.year not in range(1, 7):
        raise ValueError("Invalid year")
    if not isinstance(key.subject_code, str) or not key.subject_code.strip() or len(key.subject_code) > 32:
        raise ValueError("Invalid subject")
    if not isinstance(key.lesson_id, str) or not key.lesson_id.strip() or len(key.lesson_id) > 128:
        raise ValueError("Invalid lesson")
