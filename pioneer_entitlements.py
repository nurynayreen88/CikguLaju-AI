"""Pioneer lifetime entitlement helpers. Integration is deliberately opt-in.

Never infer payment from a QR image or receipt alone: an admin must verify it.
Use the existing persistent database connection; do not create a new database.
"""
import sqlite3

PIONEER = "PIONEER_LIFETIME"


def ensure_pioneer_schema(conn: sqlite3.Connection) -> None:
    """Additive migration: never alter or delete existing user/subscription rows."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pioneer_entitlements (
            telegram_user_id INTEGER PRIMARY KEY,
            entitlement TEXT NOT NULL CHECK(entitlement = 'PIONEER_LIFETIME'),
            payment_reference TEXT NOT NULL UNIQUE,
            approved_by INTEGER NOT NULL,
            approved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def approve_verified_payment(
    conn: sqlite3.Connection,
    *,
    telegram_user_id: int,
    payment_reference: str,
    approved_by: int,
    verified: bool,
) -> bool:
    """Grant once only after a human/admin has verified the DuitNow receipt.

    Returns True on a new grant; False if this exact account/reference was
    already granted. Conflicting reused references fail closed.
    """
    if not verified:
        raise ValueError("Payment must be independently verified before approval")
    reference = payment_reference.strip()
    if not reference:
        raise ValueError("Payment reference is required")
    with conn:
        existing = conn.execute(
            "SELECT payment_reference FROM pioneer_entitlements WHERE telegram_user_id = ?",
            (telegram_user_id,),
        ).fetchone()
        if existing is not None:
            if existing[0] == reference:
                return False
            raise ValueError("User already has a Pioneer entitlement")
        conn.execute(
            """INSERT INTO pioneer_entitlements
               (telegram_user_id, entitlement, payment_reference, approved_by)
               VALUES (?, ?, ?, ?)""",
            (telegram_user_id, PIONEER, reference, approved_by),
        )
    return True


def is_pioneer(conn: sqlite3.Connection, telegram_user_id: int) -> bool:
    """Check durable lifetime access before any expiring plan/referral check."""
    return conn.execute(
        "SELECT 1 FROM pioneer_entitlements WHERE telegram_user_id = ? AND entitlement = ?",
        (telegram_user_id, PIONEER),
    ).fetchone() is not None
