"""Read-only verified RPT/PdP navigation; never infers lessons from weeks.

Uses the exact rpt_entries schema inspected in the main app.py source.
This is a candidate navigation dataset, NOT proof of standalone RPH completeness.
No import of production app.py and no database mutations.
"""
import sqlite3
from pathlib import Path
from web.pi_navigation import GENERIC_RPT_ACTIVITIES, pi_navigation_unit
from web_v1_verified_topics import SUBJECTS


class VerifiedPdpCatalog:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def list_pdp(self, *, year, subject_code, limit=500):
        if type(year) is not int or not 1 <= year <= 6:
            raise ValueError("invalid year")
        if subject_code not in SUBJECTS:
            raise ValueError("invalid subject")
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("invalid limit")
        if not self.database_path.is_file():
            raise FileNotFoundError("curriculum database unavailable")
        uri = self.database_path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=2) as con:
            con.execute("PRAGMA query_only=ON")
            rows = con.execute(
                """SELECT id, sequence_no, unit_title, topic, subtopic, skill_focus
                   FROM rpt_entries
                   WHERE year_label=? AND subject=? AND verified=1
                     AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                   ORDER BY sequence_no, id LIMIT ?""",
                (f"Tahun {year}", SUBJECTS[subject_code], limit + 1),
            ).fetchall()
            eligible_pi_ids = set()
            if subject_code == "PI" and any(not str(r[2] or "").strip() for r in rows):
                eligible_pi_ids = self._eligible_pi_ids(con, year)
        if len(rows) > limit:
            raise ValueError("verified curriculum exceeds navigation limit")
        return [
            {"id": r[0], "pdp_no": r[1],
             "unit_title": pi_navigation_unit({"unit_title": r[2], "skill_focus": r[5]})
                           if r[0] in eligible_pi_ids else r[2],
             "topic": r[3], "subtopic": r[4], "skill_focus": r[5]}
            for r in rows
        ]

    @staticmethod
    def _eligible_pi_ids(con, year):
        tables = con.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' "
            "AND name IN ('pi_pdp_details_v2591', 'rpt_entry_standards')"
        ).fetchone()[0]
        if tables != 2:
            return set()
        return {r[0] for r in con.execute(
            """SELECT r.id FROM rpt_entries r
               WHERE r.year_label=? AND r.subject='Pendidikan Islam' AND r.verified=1
                 AND trim(COALESCE(r.unit_title, ''))=''
                 AND length(trim(COALESCE(r.activity_note, '')))>=30
                 AND lower(trim(r.activity_note)) NOT IN (?, ?)
                 AND EXISTS (SELECT 1 FROM pi_pdp_details_v2591 d
                             WHERE d.year_label=r.year_label AND d.pdp_no=r.sequence_no
                               AND d.verified=1)
                 AND (SELECT count(DISTINCT s.standard_type) FROM rpt_entry_standards s
                      WHERE s.rpt_entry_id=r.id AND s.verified=1
                        AND s.standard_type IN ('SK','SP')
                        AND trim(COALESCE(s.standard_code, ''))<>'')=2""",
            (f"Tahun {year}", *GENERIC_RPT_ACTIVITIES),
        )}


def list_explicit_pjpk_entries(database_path, year, component):
    """Only use audited mapping rows; absence of mapping yields no lessons."""
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("invalid year")
    if component not in ("PJ", "PK"):
        raise ValueError("invalid component")
    path = Path(database_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as con:
        con.execute("PRAGMA query_only=ON")
        exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='web_v1_pjpk_map'"
        ).fetchone()
        if not exists:
            return []
        rows = con.execute(
            "SELECT DISTINCT r.id, r.sequence_no, r.unit_title, r.topic, r.subtopic "
            "FROM rpt_entries r JOIN web_v1_pjpk_map m ON m.rpt_entry_id=r.id "
            "WHERE r.year_label=? AND r.subject=? AND r.verified=1 "
            "AND m.verified=1 AND m.component=? "
            "AND NOT EXISTS (SELECT 1 FROM web_v1_pjpk_map conflicting "
            "WHERE conflicting.rpt_entry_id=r.id AND conflicting.verified=1 "
            "AND conflicting.component<>m.component) "
            "AND lower(COALESCE(r.notes,'')) NOT LIKE '%superseded%' "
            "ORDER BY r.sequence_no,r.id LIMIT 500",
            (f"Tahun {year}", SUBJECTS["PJPK"], component),
        ).fetchall()
    return [{"id": r[0], "pdp_no": r[1], "unit_title": r[2],
             "topic": r[3], "subtopic": r[4]} for r in rows]
