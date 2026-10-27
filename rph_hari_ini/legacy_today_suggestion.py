"""Staging-only timetable-to-lesson adapter; never writes progress."""
from .stable_timetable_bridge import verified_stable_session
from .session_eligibility import Eligibility
from .next_lesson_readonly import suggest_next_lesson, LessonSuggestion


def suggest_from_legacy_timetable(*, teacher_id, school_year, session_date,
                                  row, lesson_total, registry, evidence,
                                  subject_key, subject_mapping,
                                  last_confirmed_sequence):
    allowed, reason, session = verified_stable_session(
        teacher_id=teacher_id, school_year=school_year,
        session_date=session_date, row=row, lesson_total=lesson_total,
        registry=registry, evidence=evidence, subject_key=subject_key,
        subject_mapping=subject_mapping)
    if allowed is not True or session is None:
        return LessonSuggestion(False, reason)
    return suggest_next_lesson(
        eligibility=Eligibility(True, "eligible", session),
        last_confirmed_sequence=last_confirmed_sequence)
