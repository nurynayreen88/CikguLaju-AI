"""Read-only database technology detection without opening or modifying a DB.

Only accepts a local file path. SQLite header recognition is a preliminary
indicator, NOT a confirmation of the production database engine.
"""
from pathlib import Path


SQLITE_HEADER = b"SQLite format 3\x00"


def detect_local_database_file(path):
    candidate = Path(path).expanduser()
    if not candidate.is_file():
        raise FileNotFoundError("Database file not found")
    with candidate.open("rb") as handle:
        header = handle.read(len(SQLITE_HEADER))
    if header == SQLITE_HEADER:
        return "sqlite3"
    return "unknown"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Detect a local SQLite file by header")
    parser.add_argument("database_file")
    args = parser.parse_args()
    print(detect_local_database_file(args.database_file))


if __name__ == "__main__":
    main()
