"""State-free weekly RPH workflow helpers. Does not mutate RPT or quota."""
from dataclasses import dataclass
from datetime import date, timedelta
from hashlib import sha256
from typing import Iterable, Mapping, FrozenSet
from rph_weekly_plan import Session, WeeklyPlan, build_weekly_plan

@dataclass(frozen=True)
class Confirmation:
    teacher_id: str
    week_start: date
    week_end: date
    extra_holidays: FrozenSet[date] = frozenset()
    cancelled_sessions: FrozenSet[str] = frozenset()
    confirmed: bool = False

def validate_confirmation(c: Confirmation) -> None:
    if not c.teacher_id or c.week_end < c.week_start:
        raise ValueError("Invalid teacher or week range")
    if (c.week_end - c.week_start).days != 6:
        raise ValueError("Weekly range must cover exactly seven calendar days")
    if any(not c.week_start <= d <= c.week_end for d in c.extra_holidays):
        raise ValueError("Additional holiday outside selected week")

def preview(sessions: Iterable[Session], official_holidays: FrozenSet[date], c: Confirmation) -> WeeklyPlan:
    validate_confirmation(c)
    sessions = tuple(sessions)
    if any(not c.week_start <= s.day <= c.week_end for s in sessions):
        raise ValueError("Session outside selected week")
    ids = {s.session_id for s in sessions}
    if not c.cancelled_sessions.issubset(ids):
        raise ValueError("Unknown cancelled session")
    return build_weekly_plan(sessions, official_holidays, c.extra_holidays, c.cancelled_sessions)

def approved_sessions(plan: WeeklyPlan, c: Confirmation) -> tuple[Session, ...]:
    validate_confirmation(c)
    if not c.confirmed:
        raise PermissionError("Teacher must confirm holidays and preview first")
    if plan.duplicates:
        raise ValueError("Duplicate session IDs must be resolved")
    return plan.included

def generation_key(teacher_id: str, session: Session) -> str:
    if not teacher_id:
        raise ValueError("Teacher ID required")
    raw = "|".join((teacher_id, session.day.isoformat(), session.session_id, session.class_id, session.subject, session.lesson_id))
    return sha256(raw.encode("utf-8")).hexdigest()

def manifest(plan: WeeklyPlan, teacher_id: str) -> tuple[dict, ...]:
    return tuple({
        "session_id": s.session_id, "date": s.day.isoformat(),
        "class_id": s.class_id, "subject": s.subject, "lesson_id": s.lesson_id,
        "generation_key": generation_key(teacher_id, s)
    } for s in plan.included)
