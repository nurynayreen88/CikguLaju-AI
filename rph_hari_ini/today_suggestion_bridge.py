"""Staging-only RPH Hari Ini suggestion from independently verified inputs.

The caller must read confirmed progress from trusted storage. This function
never writes progress and must not treat RPH generation as taught confirmation.
"""
from .session_eligibility import verify_session
from .next_lesson_readonly import suggest_next_lesson


def suggest_today_lesson(*, session, evidence, teacher_id,
                         registered_class_keys, expected_subject,
                         last_confirmed_sequence):
    eligibility = verify_session(
        session, evidence, teacher_id=teacher_id,
        registered_class_keys=registered_class_keys,
        expected_subject=expected_subject)
    return suggest_next_lesson(
        eligibility=eligibility,
        last_confirmed_sequence=last_confirmed_sequence)
