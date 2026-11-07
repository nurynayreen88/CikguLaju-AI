"""Report historical Sains RPT Year4–5 PdP that require curricular remapping.

This is an evidence-first work queue, NOT an automatic SK/SP migration and
NOT an endorsement of the legacy Year2/3/6 curriculum. Read-only source.
"""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    source_records, ROOT, EXPECTED, _kssr2017_official_code_sets_y4_y5
)
from scripts.audit_sains_kssr2017_full_statement_vs_legacy_staging import _wording

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_legacy_pdp_kssr2017_conflicts_DRAF.json"

def audit():
    years=source_records()
    official=_kssr2017_official_code_sets_y4_y5()
    ledger=json.loads((ROOT/"rpt_2027/sains/"
                       "kssr2017_y4_y5_186_official_sp_source_extraction_20261107_DRAF.json")
                      .read_text("utf-8"))
    official_statements={}
    for r in ledger["rows"]:
        key=(r["year"],r["sp_code"])
        if key in official_statements:
            raise ValueError(f"Duplicate official source statement {key}")
        official_statements[key]=r
    if len(official_statements)!=186 or ledger.get("academic_release_ready") is not False:
        raise ValueError("Official Sains reference data was tampered with")
    if {y:len(rows) for y,rows in years.items()}!=EXPECTED:
        raise ValueError("Historical Sains PdP source counts changed")
    out={}
    for year, rows in years.items():
        flagged=[]
        exact_sp=0
        sp_mismatches=[]
        exact_sk=0
        sk_title_mismatches=[]
        for row in rows:
            if row.get("academic_release_approved") is not False:
                raise ValueError("Source-only Sains PdP was incorrectly approved")
            if row.get("curriculum_text_matched") is not False:
                raise ValueError("Legacy DB source falsely became independent DSKP match")
            state=row.get("official_kssr2017_code_membership")
            if year in (4,5):
                if state is not (row["sp"] in official[year]):
                    raise ValueError(f"Sains Year {year}: official code membership inconsistent")
                if state:
                    original=official_statements.get((year,row["sp"]))
                    if original is None:
                        raise ValueError("Indexed source statement absent for official SP")
                    old_sp=row["sp_display"].split(" — ",1)
                    old_sk=row["sk_display"].split(" — ",1)
                    if len(old_sp)!=2 or len(old_sk)!=2:
                        raise ValueError("Legacy display SP/SK missing textual statement")
                    if _wording(old_sp[1])==_wording(original["sp_text_source_extract_UNVERIFIED"]):
                        exact_sp+=1
                    else:
                        sp_mismatches.append({"pdp_id":row["display_id"],
                                              "sp_code":row["sp"],
                                              "legacy_text":old_sp[1],
                                              "source_text_UNVERIFIED":original["sp_text_source_extract_UNVERIFIED"],
                                              "source_pdf_page":original["original_pdf_page"]})
                    if _wording(old_sk[1])==_wording(original["sk_title_source"]):
                        exact_sk+=1
                    else:
                        sk_title_mismatches.append({"pdp_id":row["display_id"],
                                                    "sk_code":row["sk"],
                                                    "legacy_sk_title":old_sk[1],
                                                    "original_sk_title":original["sk_title_source"]})
                if not state:
                    flagged.append({
                      "year":year,
                      "pdp_id":row["id"],
                      "source_pdp_code":row["display_id"],
                      "legacy_sk_code":row["sk"],
                      "legacy_sp_code":row["sp"],
                      "raw_pdp_title":row["raw_pdp_title"],
                      "reason":"LEGACY_SP_CODE_ABSENT_FROM_KSSR2017_ORIGINAL_YEAR_SOURCE",
                      "action":"REMAP_BY_ACTUAL_KPM_SK_SP_STATEMENT_AND_TEXTBOOK_NO_GUESSED_CODE",
                      "academic_release_approved":False,
                    })
            elif state is not None:
                raise ValueError("Unverified grade-year code membership must be null")
        out[str(year)]={
            "historical_pdp_count":len(rows),
            "official_code_membership_checked":year in (4,5),
            "pdp_with_officially_absent_code":len(flagged) if year in (4,5) else None,
            "pdp_with_official_sp_text_match":exact_sp if year in (4,5) else None,
            "pdp_with_official_sp_text_mismatch":sp_mismatches if year in (4,5) else None,
            "pdp_with_official_sk_title_match":exact_sk if year in (4,5) else None,
            "pdp_with_official_sk_title_mismatch":sk_title_mismatches if year in (4,5) else None,
            "source_text_visual_signoff_count":0,
            "pdp_with_code_present_but_full_pdp_signoff_missing":
               len(rows)-len(flagged) if year in (4,5) else None,
            "unresolved_pdp":len(rows),
            "requires_reconciliation":flagged,
            "release_ready":False,
        }
    return {
      "status":"STAGING_SOURCE_ONLY_SAINS_PDP_RECONCILIATION_QUEUE",
      "scope":"Historical 342 PdP across Years2–6; official source membership only independently checked for Year4/5",
      "years":out,
      "all_legacy_sains_pdp_academic_signoffs":0,
      "ready_for_web_telegram":False,
      "production_db_writes":0,
    }

def write_report(destination=OUT):
    report=audit()
    target=Path(destination)
    if "DRAF" not in target.stem.upper() or target.suffix!=".json":
        raise ValueError("Audit report must stay DRAF")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return target

if __name__=="__main__":
    path=write_report()
    results=json.loads(path.read_text("utf-8"))
    for year,row in results["years"].items():
        print("SAINS",year,"historical",row["historical_pdp_count"],
              "missing_official_code",row["pdp_with_officially_absent_code"],
              "unresolved",row["unresolved_pdp"])
    print("SOURCE_ONLY_DRAF",path)
