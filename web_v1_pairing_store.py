"""Atomic single-use pairing store for isolated Web V1 development.

Use a dedicated, disposable SQLite database, NEVER the production CikguLaju DB.
This module does not expose HTTP endpoints or authorize Telegram identities.
"""
import sqlite3
import time

from web_v1_pairing_challenges import challenge_storage_key


def initialize_pairing_store(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS web_v1_pairing_challenges (
        challenge_hash TEXT PRIMARY KEY,
        expires_at INTEGER NOT NULL,
        telegram_user_id INTEGER,
        consumed_at INTEGER
    )""")
    connection.commit()


def register_pairing(connection, challenge_hash, expires_at):
    if not isinstance(challenge_hash, str) or len(challenge_hash) != 64:
        raise ValueError("invalid hash")
    if type(expires_at) is not int or expires_at <= 0:
        raise ValueError("invalid expiry")
    connection.execute(
        "INSERT INTO web_v1_pairing_challenges (challenge_hash, expires_at) VALUES (?, ?)",
        (challenge_hash, expires_at),
    )
    connection.commit()


def confirm_pairing(connection, challenge, telegram_user_id, *, now=None):
    """One atomic confirmation; caller MUST verify bot update from.id first."""
    key = challenge_storage_key(challenge)
    if key is None or type(telegram_user_id) is not int or telegram_user_id <= 0:
        return False
    timestamp = int(time.time() if now is None else now)
    cursor = connection.execute(
        """UPDATE web_v1_pairing_challenges
           SET telegram_user_id = ?
           WHERE challenge_hash = ? AND expires_at > ?
             AND telegram_user_id IS NULL AND consumed_at IS NULL""",
        (telegram_user_id, key, timestamp),
    )
    connection.commit()
    return cursor.rowcount == 1


def consume_pairing(connection, challenge_hash, *, now=None):
    """Atomically consume once, returning verified-by-caller Telegram ID or None."""
    if not isinstance(challenge_hash, str) or len(challenge_hash) != 64:
        return None
    timestamp = int(time.time() if now is None else now)
    cursor = connection.execute(
        """UPDATE web_v1_pairing_challenges SET consumed_at = ?
           WHERE challenge_hash = ? AND expires_at > ?
             AND telegram_user_id IS NOT NULL AND consumed_at IS NULL
           RETURNING telegram_user_id""",
        (timestamp, challenge_hash, timestamp),
    )
    row = cursor.fetchone()
    connection.commit()
    return int(row[0]) if row else None
