"""Source-code membership audit for Sains Year 2/3 against original KPM PDFs.

Evidence is a SHA-locked original PDF code-range index. This verifies every
historical PdP SP *number*, not statement text, teaching quality, or DPK Edisi3.
No migration or writes to the original database.
"""
import json
from pathlib import Path
from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    ROOT,source_records,EXPECTED
)

INDEX=ROOT/"rpt_2027/sains/kssr2017_t2_t3_official_sp_code_ranges_20261107.json"
OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_y2_y3_original_dskp_code_membership_DRAF.json"

def official_codes():
    data=json.loads(INDEX.read_text(encoding="utf-8"))
    if (data.get("status")!="STAGING_KSSR2017_YEAR2_YEAR3_ORIGINAL_KPM_PDF_CODE_SET_ONLY"
        or data.get("release_ready") is not False or data.get("production_changes")!=0):
        raise ValueError("Missing source-only KSSR2017 2/3 release hold")
    result={}
    hashes={
        2:"55af6dad33970f6e32aea17d1bb750ce59af24872a97661374a5ecd3bee94985",
        3:"83711fabd4ddb70423f51a24dac62b1754c50719613a1bfd0cfb9127e0893ce1",
    }
    for d in data["pdfs"]:
        y=d["year"]
        if y not in (2,3) or y in result or d["sha256"]!=hashes[y]:
            raise ValueError("Unexpected original KPM source revision")
        codes=set()
        for sk,max_suffix in d["sk_sp_max_suffix"].items():
            if not (isinstance(max_suffix,int) and 1<=max_suffix<=15):
                raise ValueError("Bad source SP code range")
            for n in range(1,max_suffix+1):
                code=f"{sk}.{n}"
                if code in codes:raise ValueError("Duplicate KSSR SP code")
                codes.add(code)
        if len(codes)!={2:64,3:60}[y] or len(codes)!=d["sp_count"]:
            raise ValueError("Official KSSR code index not complete")
        result[y]=codes
    if set(result)!={2,3}:raise ValueError("Missing Sains original DSKP years")
    return result

def audit():
    official=official_codes()
    yearly=source_records()
    result={}
    for year in (2,3):
        rows=yearly[year]
        if len(rows)!=EXPECTED[year]:
            raise ValueError("Sains historical source count changed")
        missing=[]
        for row in rows:
            if row.get("curriculum_text_matched") is not False:
                raise ValueError("Source membership cannot be treated as academic signoff")
            if row["sp"] not in official[year]:
                missing.append(dict(source_pdp=row["display_id"],sp=row["sp"],topic=row["topic"]))
        result[str(year)]={
            "historical_pdp_count":len(rows),
            "original_dskp_unique_sp_count":len(official[year]),
            "historical_pdp_with_official_sp_code":len(rows)-len(missing),
            "missing_official_code":missing,
            "all_sp_statements_verified":False,
            "dp_kssr_edition3_alignment_signed_off":False,
            "academic_ready":False,
        }
    return {
      "status":"KSSR2017_SAINS_YEAR2_YEAR3_SOURCE_CODE_MEMBERSHIP_ONLY_DRAF",
      "years":result,
      "all_96_old_pdp_code_membership":all(not r["missing_official_code"] for r in result.values()),
      "production_writes":0,
      "ready_for_web_telegram":False,
    }

def write_report(path=OUT):
    r=audit()
    dst=Path(path)
    if dst.suffix!=".json" or "DRAF" not in dst.stem:
        raise ValueError("Sains audit must remain a DRAF")
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return dst

if __name__=="__main__":
    r=write_report()
    print("SAINS 2,3 source code membership",r,"NOT FINAL")
