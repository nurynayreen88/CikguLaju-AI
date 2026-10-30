"""Read-only weekly RPH preview adapter.

Production integrations must supply verified timetable and holiday data.
No implicit date, calendar, quota, or database lookups happen here.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Iterable, FrozenSet
from rph_weekly_plan import Session
from rph_weekly_workflow import Confirmation, preview, approved_sessions, manifest

@dataclass(frozen=True)
class WeeklyPreview:
    confirmation: Confirmation
    official_holidays: FrozenSet[date]
    sessions: tuple[Session, ...]
    included_count: int
    excluded_count: int
    duplicate_ids: tuple[str, ...]

def week_bounds(today: date, school_week_start_weekday: int) -> tuple[date, date]:
    """0=Monday through 6=Sunday. Must come from verified state calendar."""
    if not 0 <= school_week_start_weekday <= 6:
        raise ValueError("Invalid school week start weekday")
    start = today - timedelta(days=(today.weekday()-school_week_start_weekday)%7)
    return start, start + timedelta(days=6)

def make_preview(
    confirmation: Confirmation,
    timetable_reader: Callable[[str, date, date], Iterable[Session]],
    holiday_reader: Callable[[date, date], Iterable[date]],
) -> WeeklyPreview:
    """Dependencies must be authorization-scoped by caller, including school/state."""
    sessions = tuple(timetable_reader(confirmation.teacher_id, confirmation.week_start, confirmation.week_end))
    official = frozenset(holiday_reader(confirmation.week_start, confirmation.week_end))
    if any(not confirmation.week_start <= d <= confirmation.week_end for d in official):
        raise ValueError("Official holiday outside week")
    plan = preview(sessions, official, confirmation)
    return WeeklyPreview(confirmation, official, sessions, len(plan.included), len(plan.excluded), plan.duplicates)

def confirmed_manifest(snapshot: WeeklyPreview, confirmation: Confirmation) -> tuple[dict, ...]:
    """Reject stale preview: teacher must approve the same inputs as shown."""
    if confirmation != snapshot.confirmation:
        raise ValueError("Confirmation changed: refresh preview")
    plan = preview(snapshot.sessions, snapshot.official_holidays, confirmation)
    approved_sessions(plan, confirmation)
    return manifest(plan, confirmation.teacher_id)
