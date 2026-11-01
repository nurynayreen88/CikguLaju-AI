"""Read-only SQLite account schema inspection for Web V1.

Usage: python tools/inspect_web_v1_account_schema.py /path/to/local-copy.db
This prints schema metadata only: no user rows, passwords or tokens.
Do NOT point this tool at production without explicit approval.
"""
import argparse
import json
import sqlite3
from pathlib import Path


def inspect_schema(path):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    result = []
    with sqlite3.connect(uri, uri=True) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        for (name,) in tables:
            escaped = name.replace('"', '""')
            columns = connection.execute(f'PRAGMA table_info("{escaped}")').fetchall()
            result.append({
                "table": name,
                "columns": [{"name": col[1], "type": col[2],
                             "not_null": bool(col[3]), "primary_key": bool(col[5])}
                            for col in columns]
            })
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read-only SQLite schema metadata")
    parser.add_argument("db_path", help="Local copy of the existing SQLite database")
    args = parser.parse_args()
    print(json.dumps(inspect_schema(args.db_path), ensure_ascii=False, indent=2))
