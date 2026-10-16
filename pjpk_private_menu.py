"""Read-only PJPK menu adapter. Creates a TEMP VIEW only when the candidate DB lacks the cached menu table."""
import sqlite3
from pathlib import Path

MENU_TABLE = "pjpk_v26_30_candidate_menu"

def ensure_menu_view(con):
    tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if MENU_TABLE in tables:
        return
    required = {"rpt_entries", "pjpk_v47_generator_gate", "pjpk_v53_entry_classification", "pjpk_v59_source_kind_guard"}
    missing = required - tables
    if missing:
        raise RuntimeError("PJPK preview menu unavailable; missing source tables: " + ", ".join(sorted(missing)))
    con.execute("""
        CREATE TEMP VIEW pjpk_v26_30_candidate_menu AS
        SELECT
            CAST(substr(e.year_label, 7) AS INTEGER) AS year,
            CASE e.subject WHEN 'Pendidikan Jasmani' THEN 'PJ' ELSE 'PK' END AS component,
            e.subject AS subject,
            e.subject || ' — ' || e.year_label AS menu_label,
            0 AS production_enabled,
            e.id AS entry_id,
            e.sequence_no AS sequence_no,
            e.unit_title AS unit_title,
            e.topic AS topic,
            e.source_key AS source_key,
            CASE
                WHEN sg.source_kind = 'TEXTBOOK_UNIT_ANCHOR' THEN 'ANCHOR_NOT_PDP'
                WHEN cl.record_kind = 'PDP_SOURCE_CONFLICT' THEN 'SOURCE_CONFLICT_BLOCKED'
                ELSE 'REVIEW_ONLY'
            END AS entry_status
        FROM rpt_entries e
        JOIN pjpk_v47_generator_gate g ON g.entry_id = e.id
        LEFT JOIN pjpk_v53_entry_classification cl ON cl.entry_id = e.id
        LEFT JOIN pjpk_v59_source_kind_guard sg ON sg.entry_id = e.id
        WHERE e.subject IN ('Pendidikan Jasmani', 'Pendidikan Kesihatan')
          AND e.year_label GLOB 'Tahun [1-6]'
    """)

def list_menu_rows(db_path, year=None, component=None):
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as con:
        con.row_factory = sqlite3.Row
        ensure_menu_view(con)
        sql = "SELECT * FROM pjpk_v26_30_candidate_menu WHERE 1=1"
        args = []
        if year is not None:
            sql += " AND year=?"
            args.append(int(year))
        if component is not None:
            if component not in ("PJ", "PK"):
                raise ValueError("component must be PJ or PK")
            sql += " AND component=?"
            args.append(component)
        sql += " ORDER BY year, component, sequence_no, entry_id"
        return [dict(row) for row in con.execute(sql, args)]

def entry_status(db_path, entry_id):
    rows = list_menu_rows(db_path)
    for row in rows:
        if int(row["entry_id"]) == int(entry_id):
            return row["entry_status"]
    return None
