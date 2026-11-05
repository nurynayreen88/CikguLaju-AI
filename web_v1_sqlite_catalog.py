"""Read-only lesson catalog adapter for an explicitly supplied SQLite database.

This adapter is intentionally NOT connected to the production database.
It does not guess the schema. Caller supplies audited table/column names.
Never expose arbitrary SQL identifiers from an HTTP request.
"""
import re
import sqlite3
from pathlib import Path
from web_v1_lesson_catalog import LessonSummary, validate_catalog_query

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")


def _identifier(name):
    if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
        raise ValueError("invalid schema identifier")
    return '"' + name + '"'


class SqliteLessonCatalog:
    def __init__(self, database_path, *, table, columns):
        self.database_path = Path(database_path)
        self.table = _identifier(table)
        expected = {"lesson_id", "year", "subject_code", "unit_title", "lesson_title"}
        if not isinstance(columns, dict) or set(columns) != expected:
            raise ValueError("explicit audited column mapping required")
        self.columns = {key: _identifier(value) for key, value in columns.items()}

    def list_lessons(self, *, year, subject_code):
        validate_catalog_query(year, subject_code)
        if not self.database_path.is_file():
            raise FileNotFoundError("lesson database not found")
        cols = self.columns
        sql = (
            f"SELECT {cols['lesson_id']}, {cols['year']}, "
            f"{cols['subject_code']}, {cols['unit_title']}, {cols['lesson_title']} "
            f"FROM {self.table} WHERE {cols['year']} = ? "
            f"AND {cols['subject_code']} = ? ORDER BY {cols['lesson_id']} LIMIT 1000"
        )
        uri = self.database_path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=2) as conn:
            conn.execute("PRAGMA query_only = ON")
            return [
                LessonSummary(str(row[0]), int(row[1]), str(row[2]),
                              str(row[3]), str(row[4]))
                for row in conn.execute(sql, (year, subject_code)).fetchall()
            ]
