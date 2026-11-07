"""Staging-only KSSR2017 Year5 content code reconciliation and KPS planning.

Grounded in a separately verified original-owner DSKP index. It does NOT
certify full SP statement semantics, pedagogical PBD quality, or release.
No user DB writes and no automatic curriculum edits.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from tools.audit_sains_342_pdp_release_gate_20261106 import ROOT
from tools.render_sains_y5_83_rph_draf_20261107 import (
    KPS, get_y5_records, kps_for, SECONDARY_KPS,
)
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import checked_book_pages
from web.sains_y5_83_activity_bank_draf_20261107 import BANK

INDEX=ROOT/"audits/sains_y5_kssr2017_content_kps_scope_20261107.json"
OUT=ROOT/"build/sains_y5_kssr2017_scope_20261107"
SP_RE=re.compile(r"\b1\.1\.\d{1,2}\b")


def checked():
    source=json.loads(INDEX.read_text(encoding="utf-8"))
    meta=source["source"]
    if (source["year"]!=5 or source["subject"]!="Sains"
        or source["official_sp_total"]!=95
        or source["official_kps_count"]!=12
        or source["official_content_sp_total"]!=83
        or source["staged_content_pdp_count"]!=83
        or meta["file_id"]!="1YkiK-pVo4UUzyOUvv_Vrico58eQyddCz"
        or meta["pdf_sha256"]!="e90744b28e6cc3943e8707475a911238ffc8b6a9dffb812bf742d35bcaa61ef6"
        or meta["pdf_pages"]!=88
        or source["semantic_dskp_full_statement_verified"] is not False
        or source["release_ready"] is not False
        or source["no_database_write"] is not True):
        raise ValueError("Year5 official KSSR2017 provenance/release guard invalid")

    groups=source["official_sp_groups_max_suffix"]
    if len(groups)!=19 or groups.get("1.1")!=12 or "6.2" in groups or "10.2" in groups:
        raise ValueError("Year5 official grade-edition SK code set changed")
    official=set()
    for group,limit in groups.items():
        if not isinstance(limit,int) or not 1<=limit<=12:
            raise ValueError("Year5 official SP suffix invalid")
        official.update(f"{group}.{n}" for n in range(1,limit+1))
    process={x for x in official if x.startswith("1.1.")}
    content=official-process
    if len(official)!=95 or len(process)!=12 or len(content)!=83:
        raise ValueError("Year5 official 95/12/83 SP scope mismatch")
    if process!=set(KPS):
        raise ValueError("KPS standard codes differ from official index")

    books=checked_book_pages()  # source parts/SHA/83 page-SP labels
    records=get_y5_records()
    staged=[r["sp"] for r in records]
    if (len(staged)!=83 or len(set(staged))!=83
        or set(staged)!=set(books) or set(staged)!=set(BANK)):
        raise ValueError("Year5 staged 83-SP roster diverges from source")
    if set(staged)!=content:
        missing=sorted(content-set(staged))
        extra=sorted(set(staged)-content)
        raise ValueError(f"KSSR2017 grade-year content SP mismatch missing={missing} extra={extra}")
    if any(code.startswith(("6.2.","10.2.")) for code in staged):
        raise ValueError("Legacy year5 standards in official content roster")
    if any(r["status"]!="DRAF_HOLD" for r in records):
        raise ValueError("Year5 academic release state must remain HOLD")

    kps_sources={key:[] for key in sorted(process)}
    for r in records:
        sp=r["sp"]
        assigned=set(SP_RE.findall(kps_for(sp)))
        if not assigned or not assigned<=process:
            raise ValueError("Invalid science process skills for "+sp)
        for code in assigned:
            kps_sources[code].append(r["pdp_code"])
    if any(not entries for entries in kps_sources.values()):
        missing=[k for k,rows in kps_sources.items() if not rows]
        raise ValueError("Year5 KPS absent from all authored draft RPH: "+str(missing))
    if set(SECONDARY_KPS)!={"5.2.4","7.1.3","9.1.2"}:
        raise ValueError("KPS changes need new SP-specific evidence review")
    if ("hipotesis" not in BANK["5.2.4"]["pupil1"].lower()
        or "lapisan perang" not in BANK["7.1.3"]["pupil2"].lower()
        or "meramal" not in BANK["7.1.3"]["pupil1"].lower()
        or "putaran" not in BANK["9.1.2"]["teacher1"].lower()):
        raise ValueError("Added KPS codes lack explicit evidence in pupil/teacher draft activities")

    return {
        "subject":"Sains","year":5,
        "official_dskp_edition":"KSSR Semakan 2017, Tahun 5",
        "official_unique_sp_total":95,
        "official_content_sp_total":83,
        "official_science_process_sp_total":12,
        "stage_content_sp_exact_numeric_membership":83,
        "stage_extra_or_missing_content_sp":0,
        "kps_codes_referenced_in_staged_rph":len(kps_sources),
        "kps_to_proposed_pdp":kps_sources,
        "all_kps_assigned_at_least_once_in_draft":True,
        "full_sp_statement_semantic_validation":"PENDING",
        "kps_implementation_teacher_validation":"PENDING",
        "pedagogical_and_pbd_teacher_approval_count":0,
        "web_telegram_authenticated_e2e":False,
        "academic_quality_percent":None,
        "ready_for_runtime":False,
        "release_status":"STAGING_HOLD",
        "db_modified":False,
        "original_drive_source_modified":False,
    }


def main():
    report=checked()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"SAINS_Y5_OFFICIAL_83_CONTENT_12_KPS_HOLD.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_Y5_KSSR2017: 83/83 content SP exact official year5 numeric set; "
          "12/12 KPS referred in draft activities; semantic/PBD approval HOLD")


if __name__=="__main__":
    main()
