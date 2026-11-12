"""RBT Year4-6: opt-in 2027 week assignment from explicit teacher input only.

Never synthesize a timetable; week windows are KPM central master dates, not
a guarantee of the teaching day or state public holiday. This is staging only.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.format_2026_layout_preview import validate_rows
from scripts.build_rpt_2027_standard_preview import rbt_records

VALID_STATUS = "EXPLICIT_TEACHER_SUGGESTION_NOT_RELEASE_SIGNOFF"

def assign_rbt_weeks_from_teacher_manifest(year:int,manifest:dict):
    if type(year) is not int or year not in (4,5,6):
        raise ValueError("Only RBT Years 4,5,6 are supported")
    if not isinstance(manifest,dict) or manifest.get("academic_year")!=2027:
        raise ValueError("RBT school proposal must explicitly target year 2027")
    if manifest.get("year")!=year or manifest.get("status")!=VALID_STATUS:
        raise ValueError("RBT teacher plan absent, wrong cohort, or incorrectly approved")
    if not isinstance(manifest.get("school_calendar_verified"),bool) or manifest["school_calendar_verified"]:
        raise ValueError("Approved school calendar requires separate human holiday signoff")
    if not isinstance(manifest.get("source_reference"),str) or len(manifest["source_reference"].strip())<6:
        raise ValueError("No teacher/source reference for the proposed timetable")
    entries=manifest.get("pdp_to_week")
    if not isinstance(entries,list) or len(entries)!=32:
        raise ValueError("Must explicitly supply all 32 PdP week assignments")
    weeks=load_calendar_weeks()
    originals=rbt_records(year)
    if len(originals)!=32 or any(
        r.get("week") or r.get("a_start") or r.get("b_start") for r in originals
    ):
        raise ValueError("Source 2027 RBT already has a week: refuse replacement")
    rows=deepcopy(originals)
    last_num=0
    for n,(entry,row) in enumerate(zip(entries,rows),1):
        if not isinstance(entry,dict) or set(entry)!={"pdp","week"}:
            raise ValueError("Only explicit pdp and week fields allowed")
        if type(entry["pdp"]) is not int or entry["pdp"]!=n:
            raise ValueError("RBT lesson IDs must remain sequential 001..032")
        label=entry["week"]
        if not isinstance(label,str) or not re.fullmatch(r"M(?:0[1-9]|[1-3][0-9]|4[0-4])",label):
            raise ValueError(f"RBT PdP{n:03d} has unsupported week")
        week_n=int(label[1:])
        if week_n<last_num:
            raise ValueError("Teaching week sequence cannot move backwards")
        if label not in weeks["A"] or label not in weeks["B"]:
            raise ValueError("Missing central KPM A/B week")
        a_start,a_end=weeks["A"][label]
        b_start,b_end=weeks["B"][label]
        row.update(week=label+" (CADANGAN GURU)",a_start=a_start,a_end=a_end,
                   b_start=b_start,b_end=b_end,
                   source_proposed_week=label,
                   schedule_status=VALID_STATUS,
                   school_calendar_verified=False,
                   teacher_plan_reference=manifest["source_reference"],
                   note=row["note"]+
                   " AGIHAN GURU DRAF: "+label+
                   " (julat kalendar A/B, bukan tarikh PdP sebenar; cuti negeri dan jadual guru belum disahkan).")
        last_num=week_n
    validate_rows("rbt",year,rows)
    return rows


def load_and_assign(year:int,path:Path):
    src=Path(path)
    if not src.is_file():
        raise FileNotFoundError("Teacher RBT week plan JSON not provided")
    return assign_rbt_weeks_from_teacher_manifest(year,json.loads(src.read_text(encoding="utf-8")))


def build_teacher_rbt_preview(year:int,manifest_path:Path,output_pdf:Path):
    """Opt-in reviewer PDF; does not modify the 56 baseline RPT PDFs."""
    from rpt_2027.common.format_2026_layout_preview import build_preview
    rows=load_and_assign(year,manifest_path)
    output=Path(output_pdf)
    if output.suffix.lower()!=".pdf" or "STAGING" not in output.name.upper():
        raise ValueError("Explicit output must be a named STAGING PDF")
    build_preview("rbt",year,rows,output)
    return output

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description="Generate provisional RBT 2027 from explicit school week JSON, never live")
    parser.add_argument("--year",type=int,choices=(4,5,6),required=True)
    parser.add_argument("--teacher-manifest",type=Path,required=True)
    parser.add_argument("--out-staging-pdf",type=Path,required=True)
    args=parser.parse_args()
    pdf=build_teacher_rbt_preview(args.year,args.teacher_manifest,args.out_staging_pdf)
    print("RBT SCHOOL WEEK PREVIEW / NOT FINAL READY:",pdf)
