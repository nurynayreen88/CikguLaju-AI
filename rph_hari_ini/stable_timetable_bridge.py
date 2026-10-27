"""Read-only stable identity bridge for legacy timetable sessions.

Trusted caller supplies the server-managed registry and independently verified
calendar evidence. Never writes to the legacy profile or production database.
"""
from dataclasses import replace
from .class_identity import resolve_class_identity
from .legacy_timetable_bridge import candidate_from_legacy_row
from .session_eligibility import verify_session


def verified_stable_session(*, teacher_id, school_year, session_date, row,
                            lesson_total, registry, evidence, subject_key):
    candidate = candidate_from_legacy_row(
        teacher_id=teacher_id, school_year=school_year,
        session_date=session_date, row=row, lesson_total=lesson_total)
    if candidate is None:
        return False, "invalid_timetable_row", None
    identity = resolve_class_identity(
        teacher_id=teacher_id, school_year=school_year,
        class_name=candidate.class_key, registry=registry)
    if identity is None:
        return False, "unregistered_class_identity", None
    if not isinstance(subject_key, str) or not subject_key.strip():
        return False, "invalid_subject_key", None
    # A subject identifier must be resolved by a trusted curriculum mapping.
    # Never accept a mismatched subject for the timetable row.
    if not isinstance(row.get("subject"), str) or not row["subject"].strip():
        return False, "invalid_timetable_subject", None
    # Session ID deliberately excludes display name to survive class renames.
    stable_id = (f"{teacher_id}:{school_year}:{session_date.isoformat()}:"
                 f"{identity.class_id}:{subject_key}:{row['start']}-{row['end']}")
    stable = replace(candidate, class_key=identity.class_id,
                     subject_key=subject_key, session_id=stable_id)
    decision = verify_session(
        stable, evidence, teacher_id=teacher_id,
        registered_class_keys=frozenset({identity.class_id}),
        expected_subject=subject_key)
    return decision.allowed, decision.reason, decision.session
