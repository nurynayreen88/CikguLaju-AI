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
conn.close()
DEST.unlink(missing_ok=True)
