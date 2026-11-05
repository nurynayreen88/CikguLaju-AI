"""Safe cleanup for isolated, disposable Web V1 pairing storage.

Never point this module at the production bot database.
"""
import time


def purge_expired_pairings(connection, *, now=None, batch_size=500):
    """Delete at most batch_size expired/consumed challenges, oldest first."""
    if type(batch_size) is not int or not 1 <= batch_size <= 1000:
        raise ValueError("invalid batch size")
    timestamp = int(time.time() if now is None else now)
    cursor = connection.execute(
        """DELETE FROM web_v1_pairing_challenges
           WHERE challenge_hash IN (
               SELECT challenge_hash FROM web_v1_pairing_challenges
               WHERE expires_at <= ? OR consumed_at IS NOT NULL
               ORDER BY expires_at ASC LIMIT ?
           )""",
        (timestamp, batch_size),
    )
    connection.commit()
    return cursor.rowcount
