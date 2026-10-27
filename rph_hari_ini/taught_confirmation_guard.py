"""Pure validation for RPH taught-lesson confirmation.

No network calls, database writes, or Telegram side effects.
This module is intentionally NOT wired into the live bot.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Confirmation:
    teacher_id: str
    school_year: int
    class_id: str
    subject_id: str
    session_instance_id: str
    session_date: date
    lesson_sequence: int
    last_confirmed_sequence: int
    lesson_total: int
    calendar_verified: bool
    session_verified: bool


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    next_sequence: Optional[int] = None


def validate_confirmation(c: Confirmation) -> Decision:
    if not all((str(c.teacher_id).strip(), str(c.class_id).strip(),
                str(c.subject_id).strip(), str(c.session_instance_id).strip())):
        return Decision(False, "missing_identity")
    if not isinstance(c.school_year, int) or c.school_year < 2020:
        return Decision(False, "invalid_school_year")
    if not isinstance(c.session_date, date) or c.session_date.year != c.school_year:
        return Decision(False, "invalid_session_date")
    if not c.calendar_verified or not c.session_verified:
        return Decision(False, "unverified_calendar_or_session")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in
               (c.lesson_sequence, c.last_confirmed_sequence, c.lesson_total)):
        return Decision(False, "invalid_sequence_type")
    if c.lesson_total < 1 or not 0 <= c.last_confirmed_sequence <= c.lesson_total:
        return Decision(False, "invalid_progress")
    if c.lesson_sequence != c.last_confirmed_sequence + 1:
        return Decision(False, "non_sequential")
    if c.lesson_sequence > c.lesson_total:
        return Decision(False, "out_of_range")
    return Decision(True, "eligible", c.lesson_sequence)
