"""Test-only SQLite implementation of atomic taught progress (not production DB)."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS test_taught_progress (
 teacher TEXT NOT NULL, school_year INTEGER NOT NULL, class_key TEXT NOT NULL,
 subject_key TEXT NOT NULL, last_lesson INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY (teacher, school_year, class_key, subject_key));
CREATE TABLE IF NOT EXISTS test_taught_events (
 teacher TEXT NOT NULL, school_year INTEGER NOT NULL, class_key TEXT NOT NULL,
 subject_key TEXT NOT NULL, session_id TEXT NOT NULL, lesson INTEGER NOT NULL,
 PRIMARY KEY (teacher, school_year, class_key, subject_key, session_id),
 UNIQUE (teacher, school_year, class_key, subject_key, lesson));
"""


def init_test_db(conn):
    conn.executescript(SCHEMA)


def confirm(conn, *, teacher, school_year, class_key, subject_key, session_id,
            lesson, total, calendar_verified=False, session_verified=False):
    if conn.in_transaction:
        raise ValueError("Use a connection without an active transaction")
    if (not all(isinstance(x, str) and x.strip()
                for x in (teacher, class_key, subject_key, session_id))
        or type(school_year) is not int or not 2020 <= school_year <= 2100
        or type(lesson) is not int or type(total) is not int
        or total < 1 or not 1 <= lesson <= total
        or calendar_verified is not True or session_verified is not True):
        return "blocked"
    key = (teacher, school_year, class_key, subject_key)
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("INSERT OR IGNORE INTO test_taught_progress VALUES (?,?,?,?,0)", key)
        last = conn.execute(
            "SELECT last_lesson FROM test_taught_progress "
            "WHERE teacher=? AND school_year=? AND class_key=? AND subject_key=?", key
        ).fetchone()[0]
        event = conn.execute(
            "SELECT lesson FROM test_taught_events WHERE teacher=? AND school_year=? "
            "AND class_key=? AND subject_key=? AND session_id=?", (*key, session_id)
        ).fetchone()
        if event:
            conn.rollback()
            return "already_confirmed" if event[0] == lesson else "conflict"
        if lesson != last + 1:
            conn.rollback()
            return "non_sequential"
        conn.execute("INSERT INTO test_taught_events VALUES (?,?,?,?,?,?)",
                     (*key, session_id, lesson))
        conn.execute("UPDATE test_taught_progress SET last_lesson=? WHERE "
                     "teacher=? AND school_year=? AND class_key=? AND subject_key=?",
                     (lesson, *key))
        conn.commit()
        return "confirmed"
    except BaseException:
        conn.rollback()
        raise
