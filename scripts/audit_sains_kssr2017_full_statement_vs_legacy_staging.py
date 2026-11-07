"""Independent source-wording reconciliation for Sains Years 4–5 (STAGING).

Usage:
  python -m scripts.audit_sains_kssr2017_full_statement_vs_legacy_staging \
      --year4-pdf GuruBesar_DSKP_Sains_Tahun_4.pdf \
      --year5-pdf GuruBesar_DSKP_Sains_Tahun_5.pdf \
      --out /tmp/sains_wording_diff_DRAF.json

The official PDFs must match locked KPM SHA-256 source files. The legacy
v26 verified flag is not external certification. Numeric code overlap is not
sufficient for academic release. This script never writes the real DB.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.build_rpt2027_sains_kssr2017_y4y5_original_source_staging import (
    EXPECTED, extract_official_pdf,
)
from scripts.audit_sains_v26_vs_kssr2017_original_year4_year5_codes import original_codes
from scripts.build_rpt_2027_sains_342_actual_source_staging import _standards, ROOT
from tools.audit_sains_v26_readonly_20261106 import verify_and_rebuild

def _wording(s):
    # Strict Unicode/whitespace normalization only: do not silently erase
    # content-bearing punctuation or change a source sentence.
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(s or ""))).strip()

def compare_official_to_legacy(year:int, official_rows:list, legacy_by_code:dict, expected_codes:set):
    if year not in (4, 5):
        raise ValueError("Only original KSSR2017 DSKP Year4/5 supported")
    codes=[r.get("sp_code") for r in official_rows]
    if len(codes)!=len(set(codes)) or set(codes)!=set(expected_codes):
        raise ValueError("Official KSSR2017 code inventory incomplete or duplicated")
    if any(r.get("year")!=year for r in official_rows):
        raise ValueError("Wrong-year DSKP source entry")
    statements=[]
    counts={"SAME_CODE_SAME_WORDING_NEEDS_CONTEXT":0,
            "SAME_CODE_DIFFERENT_WORDING":0,
            "OFFICIAL_CODE_NOT_IN_LEGACY":0}
    for row in official_rows:
        code=row["sp_code"]
        official=_wording(row.get("sp_text_source_extract_NEEDS_VISUAL_REVIEW"))
        if len(official)<18 or not isinstance(row.get("original_pdf_page"),int):
            raise ValueError(f"Official SP {year}/{code} has no page or substantive text")
        existing=legacy_by_code.get(code)
        if not existing:
            state="OFFICIAL_CODE_NOT_IN_LEGACY"
            legacy_text=None
        else:
            legacy_text=_wording(existing.get("sp_text"))
            if not legacy_text:
                raise ValueError(f"Legacy SP {year}/{code} text blank")
            state=("SAME_CODE_SAME_WORDING_NEEDS_CONTEXT" if legacy_text==official
                   else "SAME_CODE_DIFFERENT_WORDING")
        counts[state]+=1
        statements.append({
            "year":year,
            "sk_code":row["sk_code"],
            "sk_title_from_original_index":row["sk_text"],
            "sp_code":code,
            "official_sp_text_source_extract_NEEDS_VISUAL_REVIEW":official,
            "legacy_sp_text":legacy_text,
            "source_pdf_page":row["original_pdf_page"],
            "comparison":state,
            "academic_sp_signoff":False,
            "pdp_rph_book_mapped":False,
        })
    missing=sorted(set(legacy_by_code)-set(expected_codes),
                   key=lambda x:tuple(int(n) for n in x.split(".")))
    if sum(counts.values())!=len(expected_codes):
        raise ValueError("SP numeric/text comparison coverage lost")
    return {
      "year":year,
      "official_sp_total":len(expected_codes),
      "legacy_sp_total":len(legacy_by_code),
      "counts":counts,
      "legacy_codes_not_in_original_kssr2017":missing,
      "rows":statements,
      "release_ready":False,
      "no_auto_code_migration":True,
      "source_text_visual_signoff_count":0,
    }

def audit(year4_pdf:Path,year5_pdf:Path):
    reference=original_codes()
    with TemporaryDirectory(prefix="sains_text_diff_ro_") as work:
        path=verify_and_rebuild(Path(work), ROOT)
        with sqlite3.connect(f"file:{path}?mode=ro&immutable=1",uri=True) as db:
            legacy=_standards(db)
    result={}
    for year,pdf in ((4,Path(year4_pdf)),(5,Path(year5_pdf))):
        original=extract_official_pdf(year,pdf)
        report=compare_official_to_legacy(year,original,legacy[year],reference[year])
        report["source_sha256"]=EXPECTED[year][0]
        result[str(year)]=report
    return {
        "status":"STAGING_KSSR2017_ORIGINAL_WORDING_COMPARISON_NO_ACADEMIC_SIGNOFF",
        "source": "SHA-256-locked original KPM DSKP Year4/Year5, compared against read-only v26 internal DB",
        "results":result,
        "ready_for_web_telegram":False,
        "production_db_writes":0,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--year4-pdf",type=Path,required=True)
    ap.add_argument("--year5-pdf",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    info=audit(args.year4_pdf,args.year5_pdf)
    out=Path(args.out)
    if "DRAF" not in out.stem.upper() or out.suffix.lower()!=".json":
        raise ValueError("Must write separate DRAF review JSON")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for y,item in info["results"].items():
        print("SAINS",y,"official",item["official_sp_total"],
              "same-wording",item["counts"]["SAME_CODE_SAME_WORDING_NEEDS_CONTEXT"],
              "different-wording",item["counts"]["SAME_CODE_DIFFERENT_WORDING"],
              "legacy-only",len(item["legacy_codes_not_in_original_kssr2017"]))
    print("RELEASE_BLOCKED",out)

if __name__=="__main__":
    main()
