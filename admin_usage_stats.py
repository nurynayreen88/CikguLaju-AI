"""Non-destructive usage-event storage for CikguLaju admin analytics.

Integrate explicitly at existing bot handlers; importing this module does not
change the database or register routes.
"""
import sqlite3
from datetime import datetime, timedelta, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS admin_usage_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 telegram_user_id TEXT NOT NULL,
 event_type TEXT NOT NULL CHECK(event_type IN ('bot_active','rph_success','rph_failed')),
 subject TEXT,
 grade TEXT,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_usage_delivery_keys (
 telegram_message_key TEXT PRIMARY KEY,
 recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_admin_usage_events_time
 ON admin_usage_events(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_usage_events_user_time
 ON admin_usage_events(telegram_user_id, created_at);
"""

def initialize(connection: sqlite3.Connection):
    """Add tables without dropping or changing existing tables."""
    connection.executescript(SCHEMA)

def record_event(connection, user_id, event_type, subject=None, grade=None, when=None):
    if event_type not in ('bot_active', 'rph_success', 'rph_failed'):
        raise ValueError('Unsupported usage event')
    stamp = (when or datetime.now(timezone.utc)).isoformat()
    connection.execute(
        'INSERT INTO admin_usage_events '
        '(telegram_user_id,event_type,subject,grade,created_at) VALUES (?,?,?,?,?)',
        (str(user_id), event_type, subject, grade, stamp),
    )
    connection.commit()

def summary(connection, now=None):
    """Counts are based only on recorded events, not inferred history."""
    now = now or datetime.now(timezone.utc)
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    def unique_since(since):
        return connection.execute(
            'SELECT COUNT(DISTINCT telegram_user_id) FROM admin_usage_events WHERE created_at >= ?',
            (since.isoformat(),),
        ).fetchone()[0]
    counts = dict(connection.execute(
        'SELECT event_type, COUNT(*) FROM admin_usage_events GROUP BY event_type'
    ).fetchall())
    subjects = connection.execute(
        "SELECT subject, COUNT(*) AS total FROM admin_usage_events "
        "WHERE event_type='rph_success' AND subject IS NOT NULL "
        "GROUP BY subject ORDER BY total DESC LIMIT 10"
    ).fetchall()
    return {
        'active_today': unique_since(day),
        'active_7d': unique_since(now - timedelta(days=7)),
        'active_30d': unique_since(now - timedelta(days=30)),
        'rph_success': counts.get('rph_success', 0),
        'rph_failed': counts.get('rph_failed', 0),
        'top_subjects': subjects,
    }

def record_confirmed_delivery(connection, user_id, telegram_message_id, subject=None, grade=None):
    """Exactly once per Telegram chat/message; atomic with the event insert.

    Returns True if recorded, False if this Telegram message was already seen.
    """
    if telegram_message_id is None:
        return False
    key = f'{user_id}:{telegram_message_id}'
    stamp = datetime.now(timezone.utc).isoformat()
    with connection:
        inserted = connection.execute(
            'INSERT OR IGNORE INTO admin_usage_delivery_keys '
            '(telegram_message_key, recorded_at) VALUES (?,?)', (key, stamp)
        ).rowcount
        if not inserted:
            return False
        connection.execute(
            'INSERT INTO admin_usage_events '
            '(telegram_user_id,event_type,subject,grade,created_at) VALUES (?,?,?,?,?)',
            (str(user_id), 'rph_success', subject, grade, stamp),
        )
    return True

def record_daily_active(connection, user_id, when=None):
    """Record only the first activity per user per UTC date."""
    stamp = (when or datetime.now(timezone.utc)).isoformat()
    day = stamp[:10]
    with connection:
        if not connection.in_transaction:
            connection.execute('BEGIN IMMEDIATE')
        inserted = connection.execute(
            "INSERT INTO admin_usage_events "
            "(telegram_user_id,event_type,subject,grade,created_at) "
            "SELECT ?, 'bot_active', NULL, NULL, ? "
            "WHERE NOT EXISTS (SELECT 1 FROM admin_usage_events "
            "WHERE telegram_user_id=? AND event_type='bot_active' "
            "AND substr(created_at,1,10)=?)",
            (str(user_id), stamp, str(user_id), day),
        ).rowcount
    return bool(inserted)
