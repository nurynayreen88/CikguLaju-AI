"""Trace all PI 2027 Year2-6 catalog SP code numbers to DSKP text presence.

Year3 and Year4 original DSKP PDF text extraction lacks most 3-level
codes. Absence there is *not* proof that a code is invalid. For Year2/5/6
machine-readable source code presence is a POSITIVE check only: it does
not certify the surrounding standard language, edition, academic alignment,
Jawi spelling, or permission to publish.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re

from pi_quality_audit import COUNT, HELD, ROOT

INVENTORY="pi_dskp_extracted_code_inventory_20261108.json"
PATTERN=re.compile(r"\b[1-9]\.\d{1,2}\.\d{1,2}\b")
CHECKABLE=(2,5,6)
UNREADABLE=(3,4)
COLUMNS=("id","year","lesson","status","sp_codes","source_drive_id",
         "source_text_verifiable","direct_wording_verified","expert_approved",
         "can_publish")


def audit(root=ROOT):
    root=Path(root)
    evidence=json.loads((root/INVENTORY).read_text(encoding="utf-8"))
    assert evidence["release"]=="NO_GO" and evidence["ready_for_teacher"] is False
    index={item["year"]:item for item in evidence["years"]}
    assert set(index)==set(COUNT)
    assert {y:len(index[y]["extracted_codes"]) for y in COUNT}=={
        2:83,3:0,4:5,5:114,6:109
    }
    rows=[]
    for year,total in COUNT.items():
        source=json.loads((root/f"year{year}.json").read_text(encoding="utf-8"))
        assert len(source["records"])==total and not source["ready"]
        observed=set(index[year]["extracted_codes"])
        for record in source["records"]:
            key=(year,record["lesson"])
            if key in HELD:
                assert record["withheld"] and "fields" not in record
                status="HELD_NO_TEACHER_SP"
                codes=[]
                positive=False
            else:
                assert record["verified_ready"] is False and not record["withheld"]
                codes=list(dict.fromkeys(PATTERN.findall(record["fields"]["sp"])))
                positive=year in CHECKABLE and bool(codes)
                if positive:
                    missing=set(codes)-observed
                    assert not missing,(record["id"],sorted(missing))
                    status="CODE_NUMBERS_PRESENT_IN_DSKP_TEXT_NOT_WORDING_CERTIFIED"
                elif codes:
                    assert year in UNREADABLE
                    status="DSKP_PDF_TEXT_INCOMPLETE_VISUAL_REVIEW_REQUIRED"
                else:
                    status="NO_OFFICIAL_THREE_LEVEL_CODE_IN_SOURCE_RPT"
            rows.append({
                "id":record["id"],"year":year,"lesson":record["lesson"],
                "status":status,"sp_codes":",".join(codes),
                "source_drive_id":index[year]["source_drive_id"],
                "source_text_verifiable":positive,
                "direct_wording_verified":False,
                "expert_approved":False,"can_publish":False
            })
    assert len(rows)==696
    counts=Counter(x["status"] for x in rows)
    assert counts["HELD_NO_TEACHER_SP"]==6
    assert all(not x["expert_approved"] and not x["can_publish"] for x in rows)
    return {
        "scope":"Pendidikan Islam Year2-6; 696 draft records",
        "evidence_type":"Literal DSKP PDF text code-number presence, NOT textual SP validation",
        "source_files_by_year":{str(y):index[y]["source_drive_id"] for y in COUNT},
        "source_pdf_code_types_by_year":{str(y):len(index[y]["extracted_codes"]) for y in COUNT},
        "fully_machine_readable_code_years":list(CHECKABLE),
        "incomplete_dskp_pdf_text_years":list(UNREADABLE),
        "full_catalog_rows_checked":len(rows),
        "code_reference_mismatches_year2_5_6":0,
        "exact_sk_sp_wording_expert_approvals":0,
        "false_absence_claims_year3_4":0,
        "codes_or_ayat_added_to_rph":0,
        "db_modified":False,
        "release":"NO_GO",
        "counts":dict(counts),
        "rows":rows
    }


def write(path,csv_path):
    r=audit()
    Path(path).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",
                          encoding="utf-8")
    with Path(csv_path).open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS)
        w.writeheader();w.writerows(r["rows"])
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},
                     ensure_ascii=False,indent=2))


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--json",required=True)
    ap.add_argument("--csv",required=True)
    a=ap.parse_args();write(a.json,a.csv)
