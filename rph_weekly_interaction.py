"""Telegram-agnostic weekly RPH interaction state machine.

Caller owns persistence, authorization, calendar retrieval, and actual generation.
No side effects, quota changes, or database updates are performed here.
"""
from dataclasses import dataclass, replace
from datetime import date
from typing import FrozenSet

@dataclass(frozen=True)
class WeeklySelection:
    teacher_id: str
    week_start: date
    week_end: date
    holiday_dates: FrozenSet[date] = frozenset()
    cancelled_session_ids: FrozenSet[str] = frozenset()
    preview_token: str = ""
    confirmed: bool = False

def add_holiday(state: WeeklySelection, day: date) -> WeeklySelection:
    if not state.week_start <= day <= state.week_end:
        raise ValueError("Holiday outside week")
    return replace(state, holiday_dates=state.holiday_dates | {day}, preview_token="", confirmed=False)

def remove_holiday(state: WeeklySelection, day: date) -> WeeklySelection:
    return replace(state, holiday_dates=state.holiday_dates - {day}, preview_token="", confirmed=False)

def toggle_cancelled_session(state: WeeklySelection, session_id: str) -> WeeklySelection:
    if not session_id:
        raise ValueError("Session ID required")
    cancelled = (state.cancelled_session_ids - {session_id}
                 if session_id in state.cancelled_session_ids
                 else state.cancelled_session_ids | {session_id})
    return replace(state, cancelled_session_ids=cancelled, preview_token="", confirmed=False)

def mark_previewed(state: WeeklySelection, token: str) -> WeeklySelection:
    if not token:
        raise ValueError("Preview token required")
    return replace(state, preview_token=token, confirmed=False)

def confirm(state: WeeklySelection, token: str) -> WeeklySelection:
    if not state.preview_token or token != state.preview_token:
        raise ValueError("Preview expired or missing")
    return replace(state, confirmed=True)

def require_ready(state: WeeklySelection, token: str) -> None:
    if not state.confirmed or not state.preview_token or state.preview_token != token:
        raise PermissionError("Teacher must confirm the current preview")
