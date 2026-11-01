"""Explicit, read-only mapping from an existing SQLite account table.

No schema guessing. A trusted operator must configure exact table and column
names after checking a local database copy. Never accept these names from users.
"""
import sqlite3


def _identifier(value):
    if not isinstance(value, str) or not value.isidentifier():
        raise ValueError("invalid schema identifier")
    return '"' + value + '"'


def lookup_existing_sqlite_account(db_path, telegram_id, *, table, id_column,
                                   lifetime_column=None, vip_column=None,
                                   credits_column=None):
    if type(telegram_id) is not int or telegram_id <= 0:
        return None
    identifiers = [table, id_column, lifetime_column, vip_column, credits_column]
    for name in identifiers:
        if name is not None:
            _identifier(name)
    selected = [id_column]
    selected.extend(name for name in (lifetime_column, vip_column, credits_column) if name is not None)
    if len(selected) != len(set(selected)):
        raise ValueError("account mapping columns must be distinct")
    # Use read-only mode; never create a missing DB or modify records.
    from pathlib import Path
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    query = ("SELECT " + ", ".join(_identifier(col) for col in selected) +
             " FROM " + _identifier(table) + " WHERE " + _identifier(id_column) +
             " = ? LIMIT 2")
    with sqlite3.connect(uri, uri=True) as conn:
        rows = conn.execute(query, (telegram_id,)).fetchall()
    if len(rows) != 1:
        return None
    row = dict(zip(selected, rows[0]))
    if type(row[id_column]) is not int or row[id_column] != telegram_id:
        return None
    result = {"authenticated": True, "telegram_user_id": telegram_id}
    if lifetime_column is not None:
        raw = row[lifetime_column]
        if type(raw) is not int or raw not in (0, 1):
            return None
        result["rakan_pembangun"] = bool(raw)
    if vip_column is not None:
        result["vip_until"] = row[vip_column]
    if credits_column is not None:
        credits = row[credits_column]
        if type(credits) is not int or credits < 0 or credits > 10:
            return None
        result["free_remaining"] = credits
    return result
