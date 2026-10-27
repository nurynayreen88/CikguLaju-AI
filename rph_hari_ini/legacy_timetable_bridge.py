"""Read-only bridge from existing CikguLaju timetable rows to eligibility checks.

No writes and no production wiring. The trusted caller must load an approved
calendar independently; a user-provided calendar is NOT trusted evidence.
"""
from datetime import date
from .session_eligibility import TimetableSession, verify_session

DAYS = ("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad")


def candidate_from_legacy_row(*, teacher_id, school_year, session_date,
                              row, lesson_total):
    if type(teacher_id) is not int or type(school_year) is not int:
        return None
    if type(session_date) is not date or session_date.year != school_year:
        return None
    if not isinstance(row, dict):
        return None
    if any(not isinstance(row.get(k), str) for k in ("day", "class_name", "subject", "start", "end")):
        return None
    day = str(row.get("day") or "").strip()
    klass = str(row.get("class_name") or "").strip()
    subject = str(row.get("subject") or "").strip()
    start = str(row.get("start") or "").strip()
    end = str(row.get("end") or "").strip()
    if day != DAYS[session_date.weekday()] or not klass or not subject:
        return None
    # Require strict HH:MM; no inference from incomplete timetable entries.
    import re
    pattern = r"(?:0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]"
    if not re.fullmatch(pattern, start) or not re.fullmatch(pattern, end):
        return None
    if end <= start or type(lesson_total) is not int or lesson_total < 1:
        return None
    # Existing class_name is not a stable class ID. Names are provisional,
    # and renaming/multiple years must be addressed before deployment.
    session_id = f"{school_year}:{session_date.isoformat()}:{klass}:{subject}:{start}-{end}"
    return TimetableSession(teacher_id, school_year, klass, subject,
                            session_id, session_date, session_date.weekday(),
                            lesson_total)


def check_legacy_row(*, teacher_id, school_year, session_date, row,
                     lesson_total, evidence, registered_class_keys):
    session = candidate_from_legacy_row(
        teacher_id=teacher_id, school_year=school_year,
        session_date=session_date, row=row, lesson_total=lesson_total)
    if session is None:
        return False, "invalid_timetable_row", None
    decision = verify_session(
        session, evidence, teacher_id=teacher_id,
        registered_class_keys=registered_class_keys,
        expected_subject=session.subject_key)
    return decision.allowed, decision.reason, decision.session
