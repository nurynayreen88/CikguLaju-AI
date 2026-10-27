"""Staging-only, read-only bridge. No DB or Telegram writes."""
from .session_eligibility import Eligibility, TimetableSession
from .taught_confirmation_guard import Confirmation
from .explicit_taught_handoff import check_taught_action


def check_verified_taught_action(*, eligibility, teacher_id,
                                 lesson_sequence, last_confirmed_sequence,
                                 explicit_action=False):
    if explicit_action is not True:
        return False, "teacher_confirmation_required"
    if not isinstance(eligibility, Eligibility) or not eligibility.allowed:
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
