"""Read-only staging adapter for confirming a scheduled taught lesson.

Requires an explicit teacher action and independently verified calendar,
class registry, subject mapping and last-confirmed sequence. Never writes DB.
"""
from .stable_timetable_bridge import verified_stable_session
from .verified_confirmation_bridge import check_taught_with_calendar


def confirm_from_legacy_timetable(*, teacher_id, school_year, session_date,
                                  row, lesson_total, registry, evidence,
                                  subject_key, subject_mapping,
                                  lesson_sequence, last_confirmed_sequence,
                                  explicit_action=False):
    if explicit_action is not True:
        return False, "teacher_confirmation_required"
    allowed, reason, session = verified_stable_session(
        teacher_id=teacher_id, school_year=school_year,
        session_date=session_date, row=row, lesson_total=lesson_total,
        registry=registry, evidence=evidence, subject_key=subject_key,
        subject_mapping=subject_mapping)
    if allowed is not True or session is None:
        return False, reason
    return check_taught_with_calendar(
        session=session, evidence=evidence, teacher_id=teacher_id,
        registered_class_keys=frozenset({session.class_key}),
        expected_subject=subject_key, lesson_sequence=lesson_sequence,
        last_confirmed_sequence=last_confirmed_sequence,
        explicit_action=True)
