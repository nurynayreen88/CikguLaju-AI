"""Audit KPM KSSR2017 original code-set membership against legacy v26 DB.

Matching numeric SP codes alone cannot prove same curriculum statements;
a mismatch makes release BLOCKED. Never updates original DB or RPT.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from tools.audit_sains_v26_readonly_20261106 import verify_and_rebuild
from scripts.build_rpt_2027_sains_342_actual_source_staging import _standards,ROOT
from rpt_2027.common.sains_kssr2017_edition_release_guard import edition_conflict

INDEX=ROOT/"rpt_2027/sains/kssr2017_t4_t5_official_sp_code_ranges_20261107.json"
OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_v26_vs_kssr2017_official_y4_y5_code_diff_20261107.json"

def original_codes():
    doc=json.loads(INDEX.read_text(encoding="utf-8"))
    if doc.get("status")!="OFFICIAL_KSSR2017_YEAR4_YEAR5_PDF_CODE_SET_EVIDENCE_ONLY" or doc.get("release_approved") is not False:
        raise ValueError("Original KSSR2017 code index missing source hold")
    result={}
    for row in doc["years"]:
        y=row["year"]
        if y not in (4,5) or y in result:
            raise ValueError("Wrong year/duplicate original code source")
        codes=set()
        for sk,last in row["sk_sp_max_suffix"].items():
            if not (1<=last<=20):
                raise ValueError("Unexpected KSSR official SP suffix bound")
            for i in range(1,last+1):
                code=f"{sk}.{i}"
                if code in codes:
                    raise ValueError("Duplicate official code")
                codes.add(code)
        if len(codes)!=row["official_unique_sp"] or len(codes)!={4:91,5:95}[y]:
            raise ValueError("KSSR year-specific code counts differ from original source")
        result[y]=codes
    if set(result)!={4,5}:
        raise ValueError("Original DSKP code inventory incomplete")
    return result

def audit_codes():
    edition_conflict() # release gate remains held
    official=original_codes()
    with TemporaryDirectory(prefix="sains_kssr_spdiff_readonly_") as td:
        dbpath=verify_and_rebuild(Path(td),ROOT)
        with sqlite3.connect(f"file:{dbpath}?mode=ro&immutable=1",uri=True) as db:
            source=_standards(db)
    results={}
    for year in (4,5):
        canonical=set(source[year]); newer=official[year]
        legacy_only=sorted(canonical-newer,key=lambda x:tuple(map(int,x.split("."))))
        official_only=sorted(newer-canonical,key=lambda x:tuple(map(int,x.split("."))))
        overlap=sorted(canonical&newer,key=lambda x:tuple(map(int,x.split("."))))
        if not legacy_only and not official_only:
            raise ValueError("Expected cross-edition numeric code mismatch not detected")
        results[str(year)]={
            "legacy_v26_db_verified_sp_count":len(canonical),
            "kssr2017_original_pdf_sp_count":len(newer),
            "same_numeric_code_not_equivalent_text_verified":len(overlap),
            "legacy_code_not_in_official":len(legacy_only),
            "official_code_not_in_legacy":len(official_only),
            "legacy_only_codes":legacy_only,"official_only_codes":official_only,
            "numeric_overlap_codes":overlap,
            "same_numbers_mean_same_standard":False,
        }
    return {"status":"STAGING_SAINS_KSSR2017_OFFICIAL_MISMATCH_RELEASE_BLOCKED",
            "year4_5_original_source_evidence":str(INDEX.relative_to(ROOT)),
            "release_ready":False,"production_changes":0,"years":results}

def write_report(path=OUT):
    info=audit_codes();dst=Path(path);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return dst

if __name__=="__main__":
    f=write_report();j=json.loads(f.read_text(encoding="utf-8"))
    for y,scope in j["years"].items():
        print("SAINS KSSR2017",y,"legacy",scope["legacy_v26_db_verified_sp_count"],
              "official",scope["kssr2017_original_pdf_sp_count"],
              "legacy-only",scope["legacy_code_not_in_official"],
              "official-only",scope["official_code_not_in_legacy"])
