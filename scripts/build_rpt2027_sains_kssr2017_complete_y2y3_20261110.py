"""Complete *coverage* candidate for Sains Year2/3 2027, original DSKP.

Uses all 64+60 original KSSR source SP with precise PDF page provenance.
Distributes owner's target 92/103 sessions across KPM A/B week windows.
Extra lessons are SP-linked teacher PBD/practice proposals, NOT KPM-authored
PdP identifiers or a claim that the existing RPH database is ready.
Keeps source text and source academic signoff flags untouched. Staging only.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows
from rpt_2027.common.week1_owner_plan_20261110 import CANDIDATE_WEEKS
from rpt_2027.sains.sains_y2_y3_original_dskp_124_sp_20261110 import (
    source_records, SOURCE_SP_COUNTS, SOURCE_SHA256
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_kssr2017_y2_y3_92_103_dskp_source_candidate"
PDP_TARGET={2:92,3:103}


def _candidate_sessions(year):
    source=source_records(year)
    extra=PDP_TARGET[year]-len(source)
    if extra<0 or extra>=len(source):
        raise ValueError("Year-specific target must produce a reasonable extra PBD allocation")
    # Preserve exactly one original-source lesson per SP; add extra practice
    # immediately after evenly chosen source SPs.
    selected={(i*(len(source)-1))//(extra-1) for i in range(extra)}
    if len(selected)!=extra:
        raise ValueError("Practice lesson positions collided")
    output=[]
    for i,row in enumerate(source):
        output.append((row,False))
        if i in selected:
            output.append((row,True))
    if len(output)!=PDP_TARGET[year]:
        raise ValueError("Annual owner target not met")
    return output


def _weeks(n):
    weeks=CANDIDATE_WEEKS
    if weeks[0]!="M01" or len(weeks)!=42 or "M06" in weeks:
        raise ValueError("KPM candidate calendar week source changed")
    quota=[2]*len(weeks)
    extras=n-2*len(weeks)
    if not 0 <= extras <= len(weeks)-1:
        raise ValueError("Cannot distribute 2-3 periods per week")
    later=len(weeks)-1
    for i in range(1,len(weeks)):
        quota[i] += i*extras//later - (i-1)*extras//later
    if sum(quota)!=n or quota[0]!=2 or max(quota)>3:
        raise ValueError("Invalid weekly allocation")
    return [week for week,c in zip(weeks,quota) for _ in range(c)]


def annual_source_plan(year):
    if type(year) is not int or year not in PDP_TARGET:
        raise ValueError("Year1 KP2027 and Y4-6 belong to separate, grounded curriculum sources")
    sessions=_candidate_sessions(year)
    weeks=_weeks(len(sessions))
    dates=load_calendar_weeks()
    result=[]
    for i,((r,is_practice),week) in enumerate(zip(sessions,weeks),1):
        a=dates["A"][week];b=dates["B"][week]
        sp=r["sp_code"]
        sk=r["sk_code"]
        major=int(sk.split(".")[0])
        explanation=r["sp_text"]
        topic=("Pengukuhan / PBD: " if is_practice else "")+explanation
        # NOTE is pedagogical only, never editor review notes.
        note=("PBD: rekod evidens melalui pemerhatian, respons murid "
              "atau hasil tugasan berasaskan SP "+sp+".")
        result.append(dict(
            id=f"{i:03d}",week=week,
            a_start=a[0],a_end=a[1],b_start=b[0],b_end=b[1],
            unit=f"Unit {major}: {r['sk_text']}",
            topic=topic,
            sk=sk,sp=sp,sk_display=sk+" — "+r["sk_text"],
            sp_display=sp+" — "+explanation,
            note=note,
            source_official_sp_codes=[sp],
            source_original_pdf_page=r["original_pdf_page"],
            source_pdf_sha256=SOURCE_SHA256[year],
            is_sourced_sp_practice=is_practice,
            curriculum_source="KSSR_ORIGINAL_DSKP_YEAR_"+str(year),
            official_sp_source_visual_signoff=False,
            rph_pdp_crosswalk_verified=False,
            class_day_period_confirmed=False,
            academic_release_approved=False,
        ))
    if len(result)!=PDP_TARGET[year] or result[0]["week"]!="M01" or not result[0]["unit"].startswith("Unit 1:"):
        raise ValueError("Year2/3 source-complete unit/week 01 failed")
    counts=Counter(row["sp"] for row in result)
    if set(counts)!={row["sp_code"] for row in source_records(year)}:
        raise ValueError("Lost an original DSKP SP in annual projection")
    if sum(x-1 for x in counts.values()) != PDP_TARGET[year]-SOURCE_SP_COUNTS[year]:
        raise ValueError("SP practice quota mismatch")
    validate_rows("sains",year,result)
    return result


def build_all(out=OUT):
    base=Path(out)
    built=[]
    for year in (2,3):
        rows=annual_source_plan(year)
        pdf=base/f"RPT_SAINS_TAHUN_{year}_2027_{len(rows)}_PDP_DSKP_2027_SUMBER_ASAL_SEMAKAN.pdf"
        build_preview("sains",year,rows,pdf,max_span_rows=2)
        built.append((year,len(rows),pdf))
    return built


if __name__=="__main__":
    for year,n,path in build_all():
        print("RPT_SAINS_KSSR_SOURCE_COMPLETE_SP",year,n,path,
              "academic_final=false",flush=True)
