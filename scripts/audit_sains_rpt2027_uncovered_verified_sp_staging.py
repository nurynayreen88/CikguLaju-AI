"""Read-only Sains RPT2027 verified SP coverage gap versus 342 historical PdP.

Never manufacture a lesson, infer textbook pages, or mark production READY.
Uncovered records are verified source SK/SP *standards*, not approved PdP.
"""
from __future__ import annotations
import json
import sqlite3
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    ROOT, EXPECTED, source_records, _missing_35_from_official_dskp,
    _standards,
)
from tools.audit_sains_v26_readonly_20261106 import verify_and_rebuild

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_verified_sp_coverage_gap_20261107_DRAF.json"

def audit_coverage():
    sources=source_records()
    supplement=_missing_35_from_official_dskp()
    with TemporaryDirectory(prefix="sains_2027_sp_cover_ro_") as tmp:
        source_db=verify_and_rebuild(Path(tmp),ROOT)
        with sqlite3.connect(f"file:{source_db}?mode=ro&immutable=1",uri=True) as db:
            verified=_standards(db)
    years={}
    for year, pdp_rows in sorted(sources.items()):
        standards={}
        for code,entry in verified[year].items():
            standards[code]={
                "sk_code":entry["sk"],"sp_code":code,
                "sk_text":entry["sk_text"],"sp_text":entry["sp_text"],
                "source":"VERIFIED_V26_00_CURRICULUM_STANDARDS"
            }
        for (cyear,code),entry in supplement.items():
            if cyear!=year:
                continue
            if code in standards:
                raise ValueError(f"Y{year} SP {code} supplemental text overlaps v26")
            sk=entry.get("sk_code")
            if not sk:
                # Supplemental source stores only SP text; SK text is supplied
                # through another verified SP with this exact SK in source.
                sk=next((r["sk"] for r in pdp_rows if r["sp"]==code),None)
            matches={v["sk_text"] for v in verified[year].values()
                     if v["sk"]==sk}
            if sk is None or len(matches)!=1:
                raise ValueError(f"Year{year} {code}: no unambiguous verified SK")
            standards[code]={
                "sk_code":sk,"sp_code":code,
                "sk_text":next(iter(matches)),"sp_text":entry["sp_text"],
                "source":"KPM_DSKP_ORIGINAL_SUPPLEMENTAL_PDF",
                "pdf_page":entry["pdf_page"],
            }
        existing_codes=[r["sp"] for r in pdp_rows]
        if len(existing_codes)!=EXPECTED[year]:
            raise ValueError(f"Year{year}: sourced PdP count changed")
        unsupported=set(existing_codes)-set(standards)
        if unsupported:
            raise ValueError(f"Year{year}: source PdP has unknown DSKP codes: {sorted(unsupported)}")
        missing_codes=sorted(set(standards)-set(existing_codes),
                             key=lambda s:tuple(int(x) for x in s.split(".")))
        duplicate_count=sum(c-1 for c in Counter(existing_codes).values() if c>1)
        skills_codes=[]
        content_codes=[]
        for code in missing_codes:
            item=standards[code]
            if item["sk_code"] in ("1.1","1.2"):
                expected_title={"1.1":"Kemahiran Proses Sains",
                                "1.2":"Kemahiran Manipulatif"}[item["sk_code"]]
                if item["sk_text"]!=expected_title:
                    raise ValueError("Science cross-cutting skill classification is not source-verified")
                skills_codes.append(code)
            else:
                content_codes.append(code)
        years[str(year)]={
            "sourced_pdp_count":len(pdp_rows),
            "available_distinct_sp":len(standards),
            "pdp_distinct_sp_covered":len(set(existing_codes)),
            "repeated_sp_slots_in_pdp":duplicate_count,
            "distinct_sp_not_seen_in_pdp":len(missing_codes),
            "unmapped_crosscutting_kps_sp":len(skills_codes),
            "unmapped_subject_content_sp":len(content_codes),
            "crosscutting_kps_need_per_lesson_activity_evidence": [standards[code] for code in skills_codes],
            "subject_content_requires_textbook_rph_reconciliation": [standards[code] for code in content_codes],
            "missing_verified_standards_NOT_PDP": [standards[code] for code in missing_codes]
        }
    total_pdp=sum(v["sourced_pdp_count"] for v in years.values())
    total_available_sp=sum(v["available_distinct_sp"] for v in years.values())
    uncovered=sum(v["distinct_sp_not_seen_in_pdp"] for v in years.values())
    crosscutting=sum(v["unmapped_crosscutting_kps_sp"] for v in years.values())
    content_gap=sum(v["unmapped_subject_content_sp"] for v in years.values())
    if crosscutting!=51 or content_gap!=29 or crosscutting+content_gap!=uncovered:
        raise ValueError(f"Science skill/content classification unexpected: {crosscutting}/{content_gap}")
    if total_pdp!=342 or total_available_sp!=422 or uncovered < 80:
        raise ValueError(f"Sains sourced counts unexpected: pdp {total_pdp} standards {total_available_sp} missing {uncovered}")
    return {
        "date":"2026-11-07",
        "status":"STAGING_ONLY_UNCOVERED_STANDARDS_NOT_PLANNED_LESSONS",
        "read_only":True,
        "full_2027_rpt_ready":False,
        "note":"Uncovered SP codes are verified DSKP contents for planning review, not invented lessons or new official lesson sequence.",
        "counts":{"historical_source_pdp":total_pdp,
                  "verified_unique_dskp_sp_year2to6":total_available_sp,
                  "uncovered_unique_sp_in_historical_pdp":uncovered,
                  "unmapped_crosscutting_kps_sk_1_1_1_2":crosscutting,
                  "unmapped_subject_content_sp":content_gap,
                  "uncovered_is_a_pdp_count":False,
                  "crosscutting_skills_automatically_approved":False},
        "years":years,
        "no_runtime_changes":True,
    }

def write_audit(path=OUT):
    data=audit_coverage()
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return target

if __name__=="__main__":
    p=write_audit()
    d=json.loads(p.read_text("utf-8"))
    print("SAINS_2027_SOURCE_SP_GAPS:",d["counts"])
    for y,v in d["years"].items():
        print(f"Y{y}: PdP={v['sourced_pdp_count']} DSKP_SP={v['available_distinct_sp']} COVERED={v['pdp_distinct_sp_covered']} UNCOVERED={v['distinct_sp_not_seen_in_pdp']}")
