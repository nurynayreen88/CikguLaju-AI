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
