#!/usr/bin/env python3
"""Safe PM Year 2 SP 4.4 correction preview on a disposable v26.00 database.

Requires v26_00_part1/2/3.bin in repository root. This tool NEVER writes the
original v26.00 database, or any active bot database. It only writes to a
TemporaryDirectory and exits without publishing a replacement.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PARTS = [ROOT / f"v26_00_part{i}.bin" for i in (1, 2, 3)]
SUBJECT = "Pendidikan Moral"
YEAR = "Tahun 2"
PDP = 11
SP = "4.4"
WRONG = "Mengamalkan sikap berterima kasih terhadap keluarga."
CORRECT = "Melahirkan perasaan apabila berterima kasih terhadap keluarga."


def main():
    if any(not p.is_file() for p in PARTS):
        raise SystemExit("Missing versioned v26.00 parts; no repair done.")
    with TemporaryDirectory(prefix="cikgulaju_pm44_preview_") as temp:
        target = Path(temp) / "v26_00_pm44_preview.db"
        with target.open("wb") as out:
            for part in PARTS:
                with part.open("rb") as src:
                    while data := src.read(1024 * 1024):
                        out.write(data)
        with sqlite3.connect(target) as db:
            before = db.execute("PRAGMA integrity_check").fetchone()[0]
            if before != "ok":
                raise SystemExit("Original reconstructed database failed integrity check")
            rows = db.execute(
                """SELECT s.id, s.standard_text
                   FROM rpt_entry_standards s
                   JOIN rpt_entries r ON r.id=s.rpt_entry_id
                   WHERE r.subject=? AND r.year_label=? AND r.sequence_no=?
                     AND s.standard_type='SP' AND s.standard_code=?""",
                (SUBJECT, YEAR, PDP, SP),
            ).fetchall()
            if len(rows) != 1 or rows[0][1] != WRONG:
                raise SystemExit(f"Expected exact precondition not met; got {rows!r}")
            wrong_id = rows[0][0]
            valid_next = db.execute(
                """SELECT s.standard_text FROM rpt_entry_standards s
                   JOIN rpt_entries r ON r.id=s.rpt_entry_id
                   WHERE r.subject=? AND r.year_label=? AND r.sequence_no=?
                     AND s.standard_type='SP' AND s.standard_code='4.5'""",
                (SUBJECT, YEAR, PDP + 1),
            ).fetchall()
            if len(valid_next) != 1 or valid_next[0][0] != WRONG:
                raise SystemExit("SP 4.5 precondition not met. No copy changes applied.")
            db.execute("UPDATE rpt_entry_standards SET standard_text=? WHERE id=?",
                       (CORRECT, wrong_id))
            verify = db.execute(
                "SELECT standard_text FROM rpt_entry_standards WHERE id=?",
                (wrong_id,),
            ).fetchone()
            if verify[0] != CORRECT or db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise SystemExit("Post-change QA failed. Disposable copy discarded.")
            db.commit()
            print("PASS: proposed isolated SP 4.4 patch fixes exact target in disposable DB")
            print("UNDEPLOYED: source parts, production DB, and Telegram remain unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
