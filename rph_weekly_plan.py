"""Pure planning helpers for RPH Minggu Ini. No DB writes or Telegram side effects."""
from dataclasses import dataclass
from datetime import date
from typing import Iterable, FrozenSet

@dataclass(frozen=True)
class Session:
    session_id: str
    day: date
    class_id: str
    subject: str
    lesson_id: str

@dataclass(frozen=True)
class WeeklyPlan:
    included: tuple[Session, ...]
    excluded: tuple[Session, ...]
    duplicates: tuple[str, ...]

def build_weekly_plan(
    sessions: Iterable[Session],
    official_holidays: FrozenSet[date],
    additional_holidays: FrozenSet[date] = frozenset(),
    cancelled_session_ids: FrozenSet[str] = frozenset(),
) -> WeeklyPlan:
    """Filter sessions without marking lessons taught or consuming quota.

    The caller must verify holidays, user identity, timetable and lesson mappings.
    A cancelled session is excluded; later lessons must not advance on its account.
    """
    included, excluded, duplicates = [], [], []
    seen = set()
    for session in sessions:
        if not session.session_id or not session.lesson_id:
            raise ValueError("Session and lesson IDs are required")
        if session.session_id in seen:
            duplicates.append(session.session_id)
            continue
        seen.add(session.session_id)
        if (session.day in official_holidays
            or session.day in additional_holidays
            or session.session_id in cancelled_session_ids):
            excluded.append(session)
        else:
            included.append(session)
    return WeeklyPlan(tuple(included), tuple(excluded), tuple(duplicates))
