"""Service-only quota for completed weekly RPH exports."""

from datetime import date, timedelta

from web.rph_today_progress import _request
from web.teacher_profile_store import ProfileUnavailable


class WeeklyQuotaUnavailable(RuntimeError):
    pass


def weekly_usage(config, teacher_id, *, export_id=None, content_hash=None):
    if not config or config.get("account_backend") != "supabase":
        raise WeeklyQuotaUnavailable("Missing subscription quota backend")
    payload = {"p_teacher_id": teacher_id}
    if export_id is not None:
        payload.update(p_export_id=str(export_id), p_content_hash=content_hash)
    try:
        rows = _request(config, "rpc/web_rph_weekly_usage", "POST", payload)
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError("Invalid quota response")
        row = rows[0]
        start = date.fromisoformat(row["usage_week_start"])
        remaining = row["remaining"]
        allowed = row["allowed"]
        if start.weekday() != 0 or type(remaining) is not int or not 0 <= remaining <= 2 or type(allowed) is not bool:
            raise ValueError("Invalid quota response")
    except (ProfileUnavailable, KeyError, TypeError, ValueError) as exc:
        raise WeeklyQuotaUnavailable("Weekly quota could not be confirmed") from exc
    return {
        "available": allowed, "remaining": remaining, "limit": 2,
        "usage_week_start": start.isoformat(), "usage_week_end": (start + timedelta(days=6)).isoformat(),
    }
