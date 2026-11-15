"""Three supplementary five-column Sains RPT PDFs: 10 candidate PdP for 21 source SP.

Five missing topic units only; previous 342 PdP keep canonical IDs unchanged.
No 2027 class weeks, official book pages or academic approvals invented.
"""
from __future__ import annotations
from pathlib import Path
import json
from rpt_2027.common.format_2026_layout_preview import build_preview,validate_rows
from scripts.audit_sains_rpt2027_uncovered_verified_sp_staging import audit_coverage,ROOT

SOURCE=ROOT/"audits/sains_5_missing_topic_units_10_candidate_pdp_21_sp_20261107_DRAF.json"
OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_5_missing_units_10_candidate_pdp_DRAF"

def candidate_rows_by_year():
    doc=json.loads(SOURCE.read_text(encoding="utf-8"))
    if (doc.get("status")!="STAGING_TEACHER_REVIEW_10_CANDIDATE_PDP_NOT_APPROVED_RPH"
        or doc.get("official_new_lesson_ids_assigned") is not False
        or doc.get("ready_for_web_telegram") is not False):
        raise ValueError("Unapproved Sains content supplement status changed")
    audit=audit_coverage()
    missing={}
    for year in (4,5,6):
        missing[year]={r["sp_code"]:r for r in audit["years"][str(year)]["subject_content_requires_textbook_rph_reconciliation"]}
    existing_clusters={(4,"3.3"),(4,"3.4"),(5,"6.2"),(5,"10.2"),(6,"3.2")}
    if {(u["year"],u["sk"]) for u in doc["units"]}!=existing_clusters:
        raise ValueError("Source's five missing curriculum topics are not stable")
    result={4:[],5:[],6:[]};used=set()
    for unit in doc["units"]:
        year=unit["year"];sk=unit["sk"]
        for block in unit["blocks"]:
            n=len(result[year])+1
            sp_codes=block["sp"]
            statements=[]
            for code in sp_codes:
                key=(year,code)
                if key in used or code not in missing[year] or missing[year][code]["sk_code"]!=sk:
                    raise ValueError("Sains suggested candidate SP not a unique missing DSKP content standard")
                used.add(key)
                statements.append(code+" — "+missing[year][code]["sp_text"])
            sk_text=missing[year][sp_codes[0]]["sk_text"]
            detail=("Objektif: "+block["goal"]+" | Aktiviti guru: "+block["teacher"]+
                    " | Aktiviti murid: "+block["students"]+
                    " | PBD: "+block["assessment"])
            result[year].append({
                "id":f"{n:03d}","unit":f"SK {sk}: {sk_text}",
                "topic":f"PdP CADANGAN {n:02d}: {unit['title']}",
                "sk":sk,"sp":" / ".join(sp_codes),
                "sk_display":sk+" — "+sk_text,
                "sp_display":"\n".join(statements),
                "note":detail+" | LEGACY/KOD BELUM SAH KSSR2017: draf aktiviti penyelidikan, BUKAN RPT semasa; buku teks m/s, minggu dan kelulusan belum sah.",
                "week":"","a_start":"","a_end":"","b_start":"","b_end":"",
                "proposal_id":block["proposal_id"],"teacher_signoff":False,
                "proposed_not_official_pdp":True,
            })
    if len(used)!=21 or {y:len(rows) for y,rows in result.items()}!={4:4,5:4,6:2}:
        raise ValueError("Expected 21 previously uncovered SP in 10 draft blocks")
    for y,rows in result.items():
        validate_rows("sains",y,rows)
    return result

def build_all(dest=OUT):
    base=Path(dest);built=[]
    for year,rows in candidate_rows_by_year().items():
        path=base/f"RPT_SAINS_TAHUN_{year}_2027_{len(rows)}_PDP_5_TAJUK_HILANG_CADANGAN_DRAF.pdf"
        build_preview("sains",year,rows,path)
        built.append((year,len(rows),path))
    return built

if __name__=="__main__":
    for year,count,path in build_all():
        print(f"Sains Tahun {year}: {count} source-SP-aligned teaching BLOCKS, NOT OFFICIAL LESSONS -> {path}")
