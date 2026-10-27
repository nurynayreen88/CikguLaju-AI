"""Fail-closed staging eligibility gate for RPH Hari Ini.

Pure functions only: never accepts caller-provided 'verified' flags as proof.
The backend must supply records obtained from independently audited sources.
"""
from dataclasses import dataclass
from datetime import date
from typing import FrozenSet, Optional


@dataclass(frozen=True)
class TimetableSession:
    teacher_id: int
    school_year: int
    class_key: str
    subject_key: str
    session_id: str
    session_date: date
    weekday: int  # Monday=0
    lesson_total: int


@dataclass(frozen=True)
class CalendarEvidence:
    school_year: int
    state_name: str
    source_id: str
    verified_school_dates: FrozenSet[date]


@dataclass(frozen=True)
class Eligibility:
    allowed: bool
    reason: str
    session: Optional[TimetableSession] = None


def verify_session(session: TimetableSession, evidence: CalendarEvidence,
                   *, teacher_id: int, registered_class_keys: FrozenSet[str],
                   expected_subject: str) -> Eligibility:
    if not isinstance(session, TimetableSession) or not isinstance(evidence, CalendarEvidence):
        return Eligibility(False, "invalid_evidence_or_session")
    if type(teacher_id) is not int or type(session.teacher_id) is not int:
        return Eligibility(False, "invalid_teacher")
    if teacher_id != session.teacher_id:
        return Eligibility(False, "teacher_mismatch")
    if not session.class_key or session.class_key not in registered_class_keys:
        return Eligibility(False, "unregistered_class")
    if not session.subject_key or session.subject_key != expected_subject:
        return Eligibility(False, "subject_mismatch")
    if (not session.session_id or not session.session_id.strip()
            or type(session.lesson_total) is not int or session.lesson_total < 1):
        return Eligibility(False, "invalid_session")
    if (type(session.school_year) is not int
            or type(evidence.school_year) is not int
            or session.school_year != evidence.school_year
            or type(session.session_date) is not date
            or session.session_date.year != session.school_year):
        return Eligibility(False, "year_mismatch")
    if (not isinstance(evidence.state_name, str)
            or not isinstance(evidence.source_id, str)
            or not evidence.state_name.strip() or not evidence.source_id.strip()):
        return Eligibility(False, "unverified_calendar_source")
    if (type(session.session_date) is not date
            or not isinstance(evidence.verified_school_dates, frozenset)):
        return Eligibility(False, "invalid_calendar_dates")
    if session.session_date not in evidence.verified_school_dates:
        return Eligibility(False, "not_verified_school_day")
    if session.weekday != session.session_date.weekday():
        return Eligibility(False, "timetable_day_mismatch")
    return Eligibility(True, "eligible", session)
