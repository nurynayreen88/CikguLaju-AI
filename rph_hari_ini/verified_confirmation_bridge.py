"""Staging-only, read-only bridge. No DB or Telegram writes."""
from .session_eligibility import Eligibility, TimetableSession, verify_session
from .taught_confirmation_guard import Confirmation
from .explicit_taught_handoff import check_taught_action


def check_verified_taught_action(*, eligibility, teacher_id,
                                 lesson_sequence, last_confirmed_sequence,
                                 explicit_action=False):
    if explicit_action is not True:
        return False, "teacher_confirmation_required"
    if (not isinstance(eligibility, Eligibility) or eligibility.allowed is not True
            or eligibility.reason != "eligible"):
        return False, "unverified_session"
    session = eligibility.session
    if not isinstance(session, TimetableSession) or type(teacher_id) is not int:
        return False, "invalid_session"
    if session.teacher_id != teacher_id:
        return False, "teacher_mismatch"
    confirmation = Confirmation(
        str(teacher_id), session.school_year, session.class_key,
        session.subject_key, session.session_id, session.session_date,
        lesson_sequence, last_confirmed_sequence, session.lesson_total,
        True, True)
    return check_taught_action(confirmation, explicit_action=True)


def check_taught_with_calendar(*, session, evidence, teacher_id,
                               registered_class_keys, expected_subject,
                               lesson_sequence, last_confirmed_sequence,
                               explicit_action=False):
    """Recheck calendar and ownership before permitting a confirmation."""
    if explicit_action is not True:
        return False, "teacher_confirmation_required"
    eligibility = verify_session(
        session, evidence, teacher_id=teacher_id,
        registered_class_keys=registered_class_keys,
        expected_subject=expected_subject)
    return check_verified_taught_action(
        eligibility=eligibility, teacher_id=teacher_id,
        lesson_sequence=lesson_sequence,
        last_confirmed_sequence=last_confirmed_sequence,
        explicit_action=True)
