"""Inspect a local SQLite snapshot schema without reading user records.

Usage: python -m web.audit_rph_schema /path/to/snapshot.sqlite
This tool does not infer approval from rpt_entries.verified.
"""
import json
from pathlib import Path
import sqlite3
import sys


def inspect_schema(database_path: str) -> dict:
    path = Path(database_path).resolve(strict=True)
    if not path.is_file():
        raise ValueError("Expected SQLite file")
    uri = path.as_uri() + "?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True, timeout=3) as conn:
        conn.execute("PRAGMA query_only=ON")
        integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError("SQLite snapshot failed quick_check")
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        tables = {}
        for (name,) in rows:
            escaped = name.replace('"', '""')
            columns = conn.execute(f'PRAGMA table_info("{escaped}")').fetchall()
            tables[name] = [
                {"name": col[1], "type": col[2], "not_null": bool(col[3]),
                 "primary_key": bool(col[5])}
                for col in columns
            ]
    return {"integrity": integrity, "tables": tables,
            "note": "Schema only. Approval semantics require separate audit."}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m web.audit_rph_schema SNAPSHOT.sqlite")
    print(json.dumps(inspect_schema(sys.argv[1]), indent=2, ensure_ascii=False))
