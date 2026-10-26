"""Persistent, fail-closed 5-RPH trial gate for the EXISTING SQLite user DB.

Integrate reserve() BEFORE any RPH generation, and complete() after delivery.
Never use a curriculum database or a temporary filesystem database for this.
Pioneer and active paid subscriptions are determined by the existing access
service, not inferred from a Telegram callback or payment screenshot.
"""
import sqlite3

TRIAL_LIMIT = 5

class QuotaDenied(Exception):
    pass

def ensure_schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS rph_trial_usage (
        telegram_user_id INTEGER PRIMARY KEY,
        used INTEGER NOT NULL DEFAULT 0 CHECK(used >= 0)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS rph_trial_operations (
        operation_id TEXT PRIMARY KEY,
        telegram_user_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('reserved','completed','failed'))
    )""")
    conn.commit()

def remaining(conn, user_id):
    row = conn.execute("SELECT used FROM rph_trial_usage WHERE telegram_user_id=?", (int(user_id),)).fetchone()
    return max(0, TRIAL_LIMIT - (int(row[0]) if row else 0))

def reserve(conn, user_id, operation_id, *, has_full_access=False):
    """Atomically reserve a trial use; duplicate operation IDs cannot double-charge.

    Caller must use the same durable database for all bot workers.
    A crashed reservation counts until explicitly reconciled by an admin.
    """
    if has_full_access:
        return None
    if not operation_id or not str(operation_id).strip():
        raise ValueError("Unique operation_id required")
    uid = int(user_id)
    conn.execute("BEGIN IMMEDIATE")
    try:
        previous = conn.execute("SELECT telegram_user_id,status FROM rph_trial_operations WHERE operation_id=?", (str(operation_id),)).fetchone()
        if previous:
            if int(previous[0]) != uid:
                raise QuotaDenied("Operation ID belongs to another user")
            conn.commit()
            return previous[1]
        conn.execute("INSERT OR IGNORE INTO rph_trial_usage(telegram_user_id,used) VALUES (?,0)", (uid,))
        changed = conn.execute("UPDATE rph_trial_usage SET used=used+1 WHERE telegram_user_id=? AND used<?", (uid, TRIAL_LIMIT)).rowcount
        if changed != 1:
            raise QuotaDenied("Percubaan percuma telah habis (0/5).")
        conn.execute("INSERT INTO rph_trial_operations(operation_id,telegram_user_id,status) VALUES (?,?,'reserved')", (str(operation_id),uid))
        conn.commit()
        return "reserved"
    except BaseException:
        conn.rollback()
        raise

def complete(conn, operation_id, *, delivered):
    """Mark delivery success, or refund exactly once when generation/delivery fails."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute("SELECT telegram_user_id,status FROM rph_trial_operations WHERE operation_id=?", (str(operation_id),)).fetchone()
        if row is None:
            raise ValueError("Unknown trial operation")
        uid, status = row
        if status == "reserved":
            new_status = "completed" if delivered else "failed"
            conn.execute("UPDATE rph_trial_operations SET status=? WHERE operation_id=?", (new_status,str(operation_id)))
            if not delivered:
                conn.execute("UPDATE rph_trial_usage SET used=used-1 WHERE telegram_user_id=? AND used>0", (uid,))
        conn.commit()
    except BaseException:
        conn.rollback()
        raise

def quota_message(conn, user_id, *, has_full_access=False):
    return "♾️ Akses tanpa had" if has_full_access else f"🎁 Baki janaan RPH percuma: {remaining(conn,user_id)}/5"
