"""Annotate original RBT draft notes with 2026 SP week-block provenance only.

Never convert historical 2026 week numbers to a 2027 school period.
Only cite exact RBT DSKP SP codes that occur in the source row.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT / "audits/rbt_t4_t6_rpt2026_23_sp_week_block_source_evidence_20261107.json"
CODE_RE=re.compile(r"(?<!\d)\d+\.\d+\.\d+(?!\d)")


def annotate_rbt_2026_week_reference(year: int, rows: list[dict]) -> list[dict]:
    if year not in (4,5,6):
        raise ValueError("RBT 2026 source evidence covers only T4–T6")
    data=json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if data.get("status")!="SOURCE_2026_WEEK_BLOCK_EVIDENCE_ONLY_NOT_2027_SCHEDULE":
        raise ValueError("2026 RBT calendar source unexpectedly promoted")
    mapping={}
    for item in data["records"]:
        if item["year"]!=year:
            continue
        for code in item["sp_codes"]:
            if code in mapping:
                raise ValueError("Duplicate SP code in RBT 2026 week evidence")
            mapping[code]=item
    for row in rows:
        if row.get("week") or any(row.get(k) for k in ("a_start","a_end","b_start","b_end")):
            raise ValueError("2027 source week already exists: do not annotate as unresolved")
        codes=set(CODE_RE.findall(str(row["sp"])))
        segments={(mapping[c]["start_week_2026"],mapping[c]["end_week_2026"])
                  for c in codes if c in mapping}
        if not segments:
            continue
        formatted=", ".join(f"M{a:02d}–M{b:02d}" for a,b in sorted(segments))
        row["source_2026_rpt_week_blocks"]=formatted
        row["source_2026_sp_matched"]=sorted(c for c in codes if c in mapping)
        row["note"]+=(" Rujukan RPT 2026 mengikut kod SP: "+formatted+
                      " (pola projek sumber sahaja; BUKAN minggu/tarikh 2027).")
        row["rbt_2027_week_signoff"]=False
    return rows
