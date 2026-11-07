"""Fail-closed read-only compatibility audit for Sains Year5 v26 Telegram DB.

Exact curriculum SP code overlap is not evidence the live Telegram row has
the same academic statement or PdP identity as the 83 reviewed Year5 drafts.
This script reconstructs a temporary hash-verified *copy* of v26.00 only.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import json
import re
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.audit_sains_v26_readonly_20261106 import verify_and_rebuild,ROOT
from tools.sains_y5_kssr2017_official_sp_statements_20261107 import checked_statements

OUT=ROOT/"build/sains_y5_v26_native_official_20261107"
EXCLUDED={"REJECT_NON_SK","SOURCE_NONCORE","REJECTED"}

def normalize(s):
    return re.sub(r"\s+"," ",str(s or "")).casefold().strip().rstrip(".")

def audit():
    official=checked_statements()
    with TemporaryDirectory(prefix="cikgulaju_sains_y5_ro_") as td:
        path=verify_and_rebuild(Path(td),ROOT)
        with sqlite3.connect(f"file:{path}?mode=ro&immutable=1",uri=True) as db:
            db.row_factory=sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":
                raise ValueError("Temporary v26 DB integrity failed")
            standard_rows=[dict(r) for r in db.execute(
                """SELECT sk_code,sk_text,sp_code,sp_text,verified
                   FROM curriculum_standards
                   WHERE lower(trim(subject))='sains' AND year_label='Tahun 5'"""
            )]
            native_rows=[dict(r) for r in db.execute(
                """SELECT pdp_sequence_code,source_sequence_no,unit_code,unit_title,
                          pdp_title,sk_code,sk_text,sp_code,sp_text,
                          verification_status,textbook_ref
                   FROM verified_pdp_sequence
                   WHERE lower(trim(subject)) IN ('sains','science')
                     AND year_label='Tahun 5'"""
            )]
    standards=defaultdict(list)
    for r in standard_rows:
        standards[str(r.get("sp_code") or "").strip()].append(r)
    native=defaultdict(list)
    for r in native_rows:
        if str(r.get("verification_status") or "").strip().upper() in EXCLUDED:
            continue
        native[str(r.get("sp_code") or "").strip()].append(r)
    matched_std=0;matched_native=0;missing_std=[];different_std=[];missing_native=[];different_native=[]
    for sp,source in official.items():
        refs=standards.get(sp,[])
        correct=[r for r in refs
                 if str(r.get("sk_code") or "").strip()==source["sk"]
                 and normalize(r.get("sp_text"))==normalize(source["sp_text"])]
        if len(refs)==1 and len(correct)==1:
            matched_std+=1
        elif not refs:missing_std.append(sp)
        else:different_std.append(sp)
        nrefs=native.get(sp,[])
        correct_n=[r for r in nrefs
                   if str(r.get("sk_code") or "").strip()==source["sk"]
                   and normalize(r.get("sp_text"))==normalize(source["sp_text"])]
        # Multiple native rows can legitimately teach a SP in separate PdPs,
        # but none may silently carry a different statement under same code.
        if nrefs and len(correct_n)==len(nrefs):
            matched_native+=1
        elif not nrefs:missing_native.append(sp)
        else:different_native.append(sp)
    official_codes=set(official)
    legacy_std=sorted(set(standards)-official_codes)
    legacy_native=sorted(set(native)-official_codes)
    groups=defaultdict(list)
    for row in native_rows:
        if str(row.get("verification_status") or "").strip().upper() in EXCLUDED:
            continue
        k=str(row.get("pdp_sequence_code") or "").strip()
        if k:groups[k].append(row)
    native_safe_groups={}
    for code,items in groups.items():
        sps={str(x.get("sp_code") or "").strip() for x in items}
        if (sps and sps<=official_codes and
            all(str(r.get("sk_code") or "").strip()==official[r["sp_code"]]["sk"]
                and normalize(r.get("sp_text"))==normalize(official[r["sp_code"]]["sp_text"])
                for r in items)):
            native_safe_groups[code]=sorted(sps)
    # No auto-approval or runtime remapping even if a subset happens to match.
    decision="HOLD_NATIVE_RUNTIME_RECONCILIATION"
    return {
        "subject":"Sains","year":5,
        "official_sp_content_total":83,
        "source_version":"v26.00_HASH_VERIFIED_TEMPORARY_READ_ONLY",
        "curriculum_standards_db_rows":len(standard_rows),
        "native_verified_sequence_raw_rows":len(native_rows),
        "native_distinct_pdp_code_groups":len(groups),
        "official_full_statement_matches_curriculum_standards":matched_std,
        "official_full_statement_matches_all_native_rows_for_code":matched_native,
        "official_sp_absent_in_curriculum_standards":missing_std,
        "official_sp_text_or_sk_differs_in_curriculum_standards":different_std,
        "official_sp_absent_in_native_sequence":missing_native,
        "official_sp_text_or_sk_differs_in_native_sequence":different_native,
        "legacy_db_standards_outside_year5_official_content_sp":legacy_std,
        "native_sp_codes_outside_year5_official_content_sp":legacy_native,
        "native_groups_wholly_exact_official_statement_matching":len(native_safe_groups),
        "native_group_codes_review_only":native_safe_groups,
        "production_mapped_to_83_staging_rph":False,
        "automated_runtime_remapping_performed":False,
        "academic_approval":False,"authenticated_e2e":False,
        "release_status":decision,
        "db_modified":False,"live_web_telegram_modified":False,
    }

def main():
    result=audit()
    OUT.mkdir(parents=True,exist_ok=True)
    dest=OUT/"SAINS_T5_NATIVE_V26_VS_OFFICIAL_83_READONLY_HOLD.json"
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_Y5_NATIVE_COMPARE: official 83; v26 standard exact",
          result["official_full_statement_matches_curriculum_standards"],
          "native row SP exact",result["official_full_statement_matches_all_native_rows_for_code"],
          "native groups",result["native_distinct_pdp_code_groups"],
          "decision HOLD until reviewed identity reconciliation")

if __name__=="__main__":
    main()
