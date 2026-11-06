"""Read-only v25.82 Sains menu audit: Unit appears once, PdP numbered.

This mimics Telegram/Web grouping keys; it cannot certify native document
generation or source page correctness.
"""
from __future__ import annotations
import json
import tempfile
from collections import defaultdict, Counter
from pathlib import Path
from audit_sains_25_82_delta_20261106 import load, SOURCES, ROOT

def audit():
    with tempfile.TemporaryDirectory(prefix="sains_menu_qa_") as d:
        rows=load(SOURCES["v25.82"],ROOT,Path(d))
    years={}
    for y in range(1,7):
        yr=[r for r in rows if r["year_label"]==f"Tahun {y}"]
        groups=defaultdict(list)
        for r in yr:
            key=(str(r.get("unit_code") or "").strip(),
                 str(r.get("unit_title") or "").strip())
            groups[key].append(r)
        bytitle=defaultdict(list)
        for code,title in groups:
            bytitle[title].append(code)
        missing=[r.get("pdp_sequence_code") for r in yr
                 if not r.get("unit_title") or not r.get("pdp_sequence_code")]
        nums=sorted({int(r["source_sequence_no"]) for r in yr
                     if str(r.get("source_sequence_no") or "").isdigit()})
        years[str(y)]={
            "source_rows":len(yr),
            "numbered_pdp_unique":len({r["pdp_sequence_code"] for r in yr}),
            "distinct_unit_groups":len(groups),
            "duplicate_title_with_different_unit_code":{
                k:v for k,v in bytitle.items() if len(set(v))>1},
            "missing_unit_title_or_pdp_code":missing,
            "source_sequence_no_gaps":nums!=list(range(1,len(nums)+1)),
            "year_unit_groups":[{
                "code":u[0], "title":u[1],
                "pdps":len(v),
                "sequence_min":min(int(r["source_sequence_no"]) for r in v),
                "sequence_max":max(int(r["source_sequence_no"]) for r in v)
            } for u,v in groups.items()],
        }
    return {"source":"v25.82 read-only", "release_decision":"HOLD",
            "yearly":years, "release_note":"Check text and native RPH; unit counts alone do not certify teacher usability"}
if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
