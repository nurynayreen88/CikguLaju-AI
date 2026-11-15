"""Teacher-adjustable RBT 2027 annual planning PDF (STAGING, not class timetable).

A generic 32-hour/32-PdP planning rhythm using the exact verified central
2027 Kumpulan A/B week windows, starting M03. Original RBT CSV/RPH and the
56 baseline PDF set are unchanged. This is an editable *proposal*, not a
claim of school-specific teaching dates or KPM-required PdP/week identity.
"""
from pathlib import Path
from scripts.build_rpt_2027_rbt_32_week_illustration import rbt_32_week_scenario
from rpt_2027.common.format_2026_layout_preview import build_preview,validate_rows
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"staging/rpt_2027_seragam_2026/rbt_32week_CADANGAN_RPT_GURU_DRAF"

def rbt_teacher_adjustable_plan(year:int):
    sample=rbt_32_week_scenario(year,start_week=3)
    master=load_calendar_weeks()
    for row in sample:
        label=row["week"].replace(" (SIMULASI)","")
        if label not in master["A"] or label not in master["B"]:
            raise ValueError("Proposed RBT week outside KPM 2027 calendar")
        row["week"]=label+" (CADANGAN RPT)"
        row["schedule_status"]="DEFAULT_2027_TEACHER_ADJUSTABLE_CANDIDATE_NOT_APPROVED"
        row["schedule_basis"]="32 recommended 60-minute PdP slots, M03–M34; amend to actual school frequency"
        row["note"]=row["note"].replace(
            "SIMULASI SAHAJA: 1 PdP/minggu, hanya JULAT MINGGU; bukan tarikh kelas sebenar.",
            "CADANGAN RPT: 1 PdP/minggu, hanya JULAT MINGGU; bukan tarikh kelas sebenar.")
        if "CADANGAN RPT:" not in row["note"]:
            raise ValueError("No caveat visible for RBT default plan")
        if (row["a_start"],row["a_end"])!=master["A"][label] or (
                row["b_start"],row["b_end"])!=master["B"][label]:
            raise ValueError("RBT proposed week date mismatch")
    validate_rows("rbt",year,sample)
    return sample

def build_all(destination=OUT):
    out=Path(destination)
    result=[]
    for year in (4,5,6):
        rows=rbt_teacher_adjustable_plan(year)
        dest=out/f"CIKGULAJU_RPT_RBT_TAHUN_{year}_2027_32_PDP_CADANGAN_RPT_GURU_DRAF.pdf"
        build_preview("rbt",year,rows,dest,max_span_rows=2)
        result.append((year,len(rows),dest))
    return result

if __name__=="__main__":
    for y,n,dest in build_all():
        print("RBT TEACHER-ADJUSTABLE 2027 DRAF",y,n,dest)
