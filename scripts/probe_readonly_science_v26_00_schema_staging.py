"""Read-only, redacted inventory of Sains curriculum in v26.00 split SQLite.

Never print any user account, identifiers, payments, personal names or messages.
"""
from __future__ import annotations
import hashlib
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=["v26_00_part1.bin","v26_00_part2.bin","v26_00_part3.bin"]
DEST=Path("/tmp/cikgulaju_v26_00_sains_probe_readonly.db")
expected="b4c6914afb36747e51c2cb9d4234cf71063283ac31312e1ac235f0b955788ff6"
digest=hashlib.sha256()
with DEST.open("wb") as out:
    for name in FILES:
        src=ROOT/name
        with src.open("rb") as fp:
            while chunk:=fp.read(1024*1024):
                digest.update(chunk);out.write(chunk)
if digest.hexdigest()!=expected:
    DEST.unlink(missing_ok=True)
    raise ValueError("DB source checksum mismatch")
conn=sqlite3.connect(f"file:{DEST}?mode=ro&immutable=1",uri=True)
print("SCIENCE_DB_PROBE: checksum PASS")
tables=[r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("SCHEMA: table_count",len(tables))
print("SCHEMA: curriculum candidates",[t for t in tables if any(k in t.lower() for k in ("lesson","rpt","curric","standard","science","subject","topic","unit"))])
for table in tables:
    if not any(k in table.lower() for k in ("lesson","rpt","curric","standard","science","subject","topic","unit")):
        continue
    cols=[r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
    print("TABLE",table,"COLUMNS",cols)
    # Only aggregate statistics, never row values from potentially user-linked tables.
    print("ROWS",table,conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
print("SAINS_RPT_GROUPS", conn.execute(
    "SELECT academic_year, year_label, count(*), min(sequence_no), max(sequence_no), "
    "SUM(CASE WHEN content_verified=1 THEN 1 ELSE 0 END) "
    "FROM rpt_entries WHERE lower(subject)='sains' "
    "GROUP BY academic_year, year_label ORDER BY academic_year, year_label"
).fetchall())
print("SAINS_STANDARD_GROUPS",conn.execute(
    "SELECT year_label, count(*), count(DISTINCT sp_code), "
    "SUM(CASE WHEN verified=1 THEN 1 ELSE 0 END) "
    "FROM curriculum_standards WHERE lower(subject)='sains' "
    "GROUP BY year_label ORDER BY year_label"
).fetchall())
print("SAINS_RPT_SAMPLES",conn.execute(
    "SELECT academic_year, year_label, sequence_no, week_from, week_to, "
    "unit_code, substr(unit_title,1,80),substr(topic,1,80), "
    "verification_status, verified FROM rpt_entries "
    "WHERE lower(subject)='sains' AND year_label IN ('Tahun 2','Tahun 3','Tahun 4','Tahun 5','Tahun 6') "
    "ORDER BY year_label, academic_year DESC, sequence_no LIMIT 20"
).fetchall())
print("SAINS_JOINED_STANDARD_COUNTS",conn.execute(
    "SELECT r.year_label, r.academic_year, "
    "count(DISTINCT r.id), count(s.id), "
    "sum(CASE WHEN s.standard_type LIKE '%content%' THEN 1 ELSE 0 END) "
    "FROM rpt_entries r LEFT JOIN rpt_entry_standards s ON r.id=s.rpt_entry_id "
    "WHERE lower(r.subject)='sains' "
    "GROUP BY r.year_label,r.academic_year ORDER BY r.year_label,r.academic_year"
).fetchall())
print("MATH_STANDARDS_BY_YEAR",conn.execute(
    "SELECT year_label,count(*),count(DISTINCT sp_code),"
    "sum(CASE WHEN verified=1 THEN 1 ELSE 0 END) FROM curriculum_standards "
    "WHERE subject='Matematik' GROUP BY year_label ORDER BY year_label"
).fetchall())
print("MATH_YEAR2_STANDARD_SAMPLES",conn.execute(
    "SELECT sk_code,substr(sk_text,1,90),sp_code,substr(sp_text,1,140) "
    "FROM curriculum_standards WHERE subject='Matematik' AND year_label='Tahun 2' "
    "ORDER BY sp_code LIMIT 6"
).fetchall())
conn.close()
DEST.unlink(missing_ok=True)
