"""Non-destructive event analytics for CikguLaju user funnel.

This module is deliberately not wired into app.py until the current handlers
and database interface have been reviewed. Uses a separate SQLite database.
"""
import os
import sqlite3
import hashlib
import hmac
from datetime import datetime, timezone

EVENTS = frozenset(("promo_click", "bot_start", "registration_complete", "first_rph_success"))
DB_PATH = os.environ.get("CIKGULAJU_FUNNEL_DB", "/tmp/cikgulaju_funnel.sqlite3")
SECRET = os.environ.get("CIKGULAJU_FUNNEL_SECRET", "")


def _connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("""CREATE TABLE IF NOT EXISTS funnel_events (
        event_type TEXT NOT NULL,
        actor_hash TEXT NOT NULL,
        campaign TEXT NOT NULL DEFAULT '',
        occurred_at TEXT NOT NULL,
        PRIMARY KEY (event_type, actor_hash, campaign)
    )""")
    return conn


def record_event(event_type, actor_id, campaign=""):
    """Idempotently record a unique actor/event/campaign.

    Never pass a raw Telegram ID as campaign. For promo_click, actor_id
    must be a random visitor cookie identifier, not an IP address.
    """
    if event_type not in EVENTS:
        raise ValueError("Unsupported funnel event")
    if not SECRET:
        raise RuntimeError("CIKGULAJU_FUNNEL_SECRET must be configured")
    if actor_id is None or str(actor_id) == "":
        raise ValueError("actor_id is required")
    campaign = str(campaign or "")[:80]
    digest = hmac.new(SECRET.encode(), str(actor_id).encode(), hashlib.sha256).hexdigest()
    with _connection() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO funnel_events(event_type,actor_hash,campaign,occurred_at) VALUES (?,?,?,?)",
            (event_type, digest, campaign, datetime.now(timezone.utc).isoformat()))
        return cursor.rowcount == 1


def summary(campaign=None):
    """Unique actors per event; not a cross-stage conversion calculation.

    Anonymous promo visitors and Telegram users cannot be joined reliably.
    """
    with _connection() as conn:
        if campaign is None:
            rows = conn.execute("SELECT event_type, COUNT(DISTINCT actor_hash) FROM funnel_events GROUP BY event_type").fetchall()
        else:
            rows = conn.execute("SELECT event_type, COUNT(DISTINCT actor_hash) FROM funnel_events WHERE campaign=? GROUP BY event_type", (campaign,)).fetchall()
    counts = {event: 0 for event in EVENTS}
    counts.update(rows)
    return counts
