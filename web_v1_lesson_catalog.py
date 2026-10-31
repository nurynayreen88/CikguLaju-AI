"""Read-only contract for future CikguLaju web lesson discovery.

Deliberately does not import the Telegram application or open a database.
An audited adapter must be supplied later. This avoids inventing table names
or making unsafe assumptions about the production schema.
"""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class LessonSummary:
    lesson_id: str
    year: int
    subject_code: str
    unit_title: str
    lesson_title: str


class LessonCatalog(Protocol):
    def list_lessons(self, *, year: int, subject_code: str) -> Sequence[LessonSummary]:
        ...


class UnconfiguredCatalog:
    def list_lessons(self, *, year: int, subject_code: str) -> Sequence[LessonSummary]:
        raise RuntimeError("Web lesson catalog is not connected to an audited data source")


def validate_catalog_query(year: int, subject_code: str) -> None:
    if type(year) is not int or not 1 <= year <= 6:
        raise ValueError("year must be an integer from 1 to 6")
    if not isinstance(subject_code, str) or not subject_code or len(subject_code) > 32:
        raise ValueError("invalid subject code")
    if not all(c.isascii() and (c.isalnum() or c in "_-") for c in subject_code):
        raise ValueError("invalid subject code")
