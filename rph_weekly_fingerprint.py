"""Deterministic digest for RPH Minggu Ini previews.

Use the digest as a preview fingerprint, NOT as an authentication token.
The production handler must bind it to an authenticated teacher session.
"""
import hashlib
import json
from rph_weekly_adapter import WeeklyPreview

def preview_fingerprint(snapshot: WeeklyPreview) -> str:
    c = snapshot.confirmation
    payload = {
        "teacher_id": c.teacher_id,
        "week_start": c.week_start.isoformat(),
        "week_end": c.week_end.isoformat(),
        "official_holidays": sorted(d.isoformat() for d in snapshot.official_holidays),
        "additional_holidays": sorted(d.isoformat() for d in c.extra_holidays),
        "cancelled_sessions": sorted(c.cancelled_sessions),
        "sessions": sorted([
            (s.session_id, s.day.isoformat(), s.class_id, s.subject, s.lesson_id)
            for s in snapshot.sessions
        ]),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def require_unchanged_preview(original: WeeklyPreview, current: WeeklyPreview) -> None:
    if preview_fingerprint(original) != preview_fingerprint(current):
        raise ValueError("Timetable, holiday or lesson data changed; preview again")
