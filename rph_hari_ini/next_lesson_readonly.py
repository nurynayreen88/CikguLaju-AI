"""Staging-only lesson selection; never advances taught progress."""
from dataclasses import dataclass
from .session_eligibility import Eligibility, TimetableSession


@dataclass(frozen=True)
class LessonSuggestion:
    allowed: bool
    reason: str
    lesson_sequence: int | None = None


def suggest_next_lesson(*, eligibility, last_confirmed_sequence):
    if (not isinstance(eligibility, Eligibility)
            or eligibility.allowed is not True
            or eligibility.reason != "eligible"
            or not isinstance(eligibility.session, TimetableSession)):
        return LessonSuggestion(False, "unverified_session")
    session = eligibility.session
    if (type(last_confirmed_sequence) is not int
            or type(session.lesson_total) is not int
            or session.lesson_total < 1
            or not 0 <= last_confirmed_sequence <= session.lesson_total):
        return LessonSuggestion(False, "invalid_progress")
    if last_confirmed_sequence == session.lesson_total:
        return LessonSuggestion(False, "all_lessons_confirmed")
    return LessonSuggestion(True, "suggested", last_confirmed_sequence + 1)
