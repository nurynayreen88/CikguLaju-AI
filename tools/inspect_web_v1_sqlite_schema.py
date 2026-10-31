"""Local, read-only SQLite schema inventory for an explicitly supplied file.

Usage:
  python tools/inspect_web_v1_sqlite_schema.py /path/to/copy-of-database.sqlite

Do NOT pass secrets, production database URLs or Telegram tokens.
This tool prints only table and column names, never row data.
"""
import argparse
from pathlib import Path
import sqlite3


def inspect_schema(database_path):
    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError("Database file not found; nothing was created")
    uri = path.as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=2) as conn:
        conn.execute("PRAGMA query_only = ON")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        inventory = []
        for (name,) in tables:
            # table-valued PRAGMA accepts a parameter for the table name.
            cols = conn.execute("SELECT name, type FROM pragma_table_info(?)", (name,)).fetchall()
            inventory.append({"table": name, "columns": [{"name": c, "type": t} for c, t in cols]})
        return inventory


def main():
    parser = argparse.ArgumentParser(description="Read-only local SQLite schema inventory")
    parser.add_argument("database_file", help="Path to an existing local database copy")
    args = parser.parse_args()
    for item in inspect_schema(args.database_file):
        print(item["table"])
        for col in item["columns"]:
            print("  -", col["name"], col["type"])


if __name__ == "__main__":
    main()
