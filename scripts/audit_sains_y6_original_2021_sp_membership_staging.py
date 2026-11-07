"""Independent Sains T6 KSSR Semakan 2017 DSKP 2021 numeric SP-code audit.

CLI requires externally obtained, original readable PDF bytes:
 python -m scripts.audit_sains_y6_original_2021_sp_membership_staging \
  --pdf /tmp/DSKP_T6_KPM_2021.pdf --out /tmp/SAINS_T6_DRAF.json

Downloaded PDF is KPM-authored and may be mirrored by a school/third party.
Code membership is not independent proof of identical statements, activity
quality, textbook match, or approval to expose users. Source DB read-only.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    ROOT, source_records, EXPECTED
)

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_y6_kssr2017_2021_official_code_membership_DRAF.json"
URL="https://beebeeclassroom.com/wp-content/uploads/2022/04/DSKP-KSSR-Semakan-2017-Sains-Tahun-6_ISBN_.pdf"
SP_CODE=re.compile(r"^(?:\d{1,2}\.){2}\d{1,2}$")

def parse_official_y6(pdf_path:Path):
    import fitz
    src=Path(pdf_path)
    if not src.is_file() or src.stat().st_size<200_000:
        raise ValueError("Original Sains T6 official DSKP source PDF unavailable")
    sha=hashlib.sha256(src.read_bytes()).hexdigest()
    codes={}
    with fitz.open(src) as doc:
        if not 70<=doc.page_count<=140:
            raise ValueError("Unrecognized DSKP Sains Year6 PDF page count")
        # The syllabus section begins after the organization/intro pages.
        for pn,page in enumerate(doc,1):
            if pn<45: continue
            for word in page.get_text("words"):
                token=word[4].strip("(),:;")
                if SP_CODE.fullmatch(token):
                    codes.setdefault(token,[]).append(pn)
        sample="\n".join(doc[i].get_text() for i in (0,1,2) if i<doc.page_count)
        if "Sains" not in sample and "SAINS" not in sample:
            raise ValueError("Provided PDF does not identify Sains")
    if len(codes)<75 or len(codes)>180:
        raise ValueError(f"Official Sains Year6 code extraction suspicious: {len(codes)}")
    if "2.2.6" not in codes or "2.2.1" not in codes:
        raise ValueError("Original Year6 SK 2.2 Sistem Saraf expected SP codes missing")
    return {"source_sha256":sha,"pdf_bytes":src.stat().st_size,"codes":codes,
            "unique_sp_count":len(codes)}

def reconcile(official:dict,historical_rows:list):
    if not historical_rows or len(historical_rows)!=EXPECTED[6]:
        raise ValueError("Sains 84 historical PdP input count changed")
    code_set=set(official["codes"])
    missing=[]
    represented=set()
    for row in historical_rows:
        code=row["sp"]
        represented.add(code)
        if row.get("curriculum_text_matched") is not False:
            raise ValueError("Cannot claim academic match from numeric code")
        if code not in code_set:
            missing.append({"pdp":row["display_id"],"legacy_sp":code,
                            "topic":row["topic"]})
    return {
      "historical_pdp_count":len(historical_rows),
      "official_unique_sp":official["unique_sp_count"],
      "official_codes_used_in_historical_pdp":len(represented & code_set),
      "historical_pdp_with_missing_official_sp_code":missing,
      "official_unique_codes_not_in_historical_pdp":sorted(code_set-represented),
      "pdp_sp_statements_visual_signoff":0,
      "full_rpt_ready":False,
    }

def audit(pdf_path:Path):
    official=parse_official_y6(pdf_path)
    rows=source_records()[6]
    result=reconcile(official,rows)
    return {
      "status":"STAGING_SAINS_Y6_ORIGINAL2021_KPM_PDF_SP_CODE_MEMBERSHIP_ONLY",
      "pdf_source_url":URL,"pdf_sha256":official["source_sha256"],
      "pdf_bytes":official["pdf_bytes"],"year":6,"result":result,
      "academic_ready":False,"ready_for_web_telegram":False,
      "production_changes":0,
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--pdf",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    result=audit(args.pdf)
    out=Path(args.out)
    if out.suffix!=".json" or "DRAF" not in out.stem.upper():
        raise ValueError("Sains T6 original audit must have a DRAF filename")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS YEAR6 OFFICIAL SOURCE CODE CHECK",result["result"]["historical_pdp_count"],
          "missing-code PdP",len(result["result"]["historical_pdp_with_missing_official_sp_code"]),
          "source SP",result["result"]["official_unique_sp"],"RELEASE_BLOCKED")

if __name__=="__main__":
    main()
