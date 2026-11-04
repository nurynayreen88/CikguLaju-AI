#!/usr/bin/env python3
"""Compare Moral Year 2-6 standalone drafts with the existing v26.00 production DB.

Read-only check: reconstruct a temporary DB file, never replace the live DB.
Run from repository checkout: python scripts/check_pm_v2600_stage_parity.py
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PARTS = [ROOT / f"v26_00_part{i}.bin" for i in (1, 2, 3)]
RPT_ROOT = ROOT / "rpt_2027" / "pendidikan_moral"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold().rstrip(" .")


def compare(con: sqlite3.Connection, year: int) -> list[str]:
    issues: list[str] = []
    label = f"Tahun {year}"
    crosswalk = json.loads((RPT_ROOT / f"year{year}_crosswalk_DSKP.json").read_text(encoding="utf-8"))
    with (RPT_ROOT / f"year{year}_sequence_DRAF.csv").open(encoding="utf-8", newline="") as handle:
        rpt_rows = list(csv.DictReader(handle))
    rows = con.execute(
        """SELECT id, sequence_no, unit_title, verified
           FROM rpt_entries
           WHERE subject='Pendidikan Moral' AND year_label=?
           ORDER BY sequence_no, id""",
        (label,),
    ).fetchall()
    if len(rows) != 42 or len(rpt_rows) != 42 or len(crosswalk["units"]) != 14:
        return [f"{label}: expected 42 DB PdP, 42 RPT rows, 14 DSKP units; got {len(rows)}/{len(rpt_rows)}/{len(crosswalk['units'])}"]
    for index, (db_row, rpt_row) in enumerate(zip(rows, rpt_rows), start=1):
        db_id, seq, _title, verified = db_row
        if seq != index or verified != 1:
            issues.append(f"{label} PdP {index}: DB sequence or verified flag mismatch")
        expected_from_dskp = [f"{1 + (index-1)//3}.{part}" for part in ((1,2) if (index-1)%3==0 else (3,4) if (index-1)%3==1 else (5,))]
        rpt_sp = [x.strip() for x in rpt_row["SP"].split(";") if x.strip()]
        db_sp_rows = con.execute(
            """SELECT standard_code, standard_text, verified
               FROM rpt_entry_standards
               WHERE rpt_entry_id=? AND standard_type='SP'
               ORDER BY sequence_no, id""",
            (db_id,),
        ).fetchall()
        db_sp = [r[0] for r in db_sp_rows]
        if (rpt_sp != expected_from_dskp or db_sp != expected_from_dskp
            or any(r[2] != 1 for r in db_sp_rows)):
            issues.append(f"{label} PdP {index}: SP expected {expected_from_dskp}, RPT {rpt_sp}, DB {db_sp}")
        unit = crosswalk["units"][(index-1)//3]
        reference = {sp["code"]: sp["text"] for sp in unit["sp"]}
        for code, text, verified in db_sp_rows:
            if code in reference and normalize(text) != normalize(reference[code]):
                issues.append(f"{label} PdP {index}: wording differs for SP {code}; DB={text!r}, DSKP={reference[code]!r}")
    print(f"{label}: checked 42 DB lessons, 42 staged RPT lessons")
    return issues


def main() -> int:
    missing = [str(p) for p in PARTS if not p.is_file()]
    if missing:
        print("FAIL missing DB parts:", missing)
        return 1
    with TemporaryDirectory(prefix="pm_v2600_qa_") as folder:
        db_path = Path(folder) / "master_readonly.db"
        with db_path.open("wb") as output:
            for part in PARTS:
                with part.open("rb") as source:
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as con:
            if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                print("FAIL: reconstructed source database integrity check")
                return 1
            issues = []
            for year in range(2, 7):
                issues.extend(compare(con, year))
            if issues:
                for item in issues[:70]:
                    print("FAIL:", item)
                print(f"FAIL: {len(issues)} source-parity mismatches")
                return 1
    print("PASS: 210 staged Moral PdP/SP codes and wording agree with v26.00 master DB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
