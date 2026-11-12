"""Sains T6 DSKP 2021 secondary-mirror SP-code-only reconciliation.

This is NOT the original SHA-locked PDF and cannot independently verify
statement wording, activities, textbook pages or release. Uses only the
published KPM DSKP text mirrored at FlipHTML5 and the read-only historical
source from v26 DB. The original PDF audit remains a separate requirement.
"""
import json
import re
from pathlib import Path
from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    ROOT, EXPECTED, source_records
)

LEDGER=ROOT/"rpt_2027/sains/kssr2017_t6_2021_secondary_mirror_sp_code_ranges_20261107_DRAF.json"
OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_y6_2021_secondary_mirror_code_pdp_diff_DRAF.json"

def source_code_index():
    src=json.loads(LEDGER.read_text(encoding="utf-8"))
    if (src.get("status")!="STAGING_SAINS_T6_2021_SECONDARY_MIRROR_PUBLISHED_TEXT_CODE_INDEX_NOT_PRIMARY_PDF_SIGNOFF"
        or src.get("year")!=6
        or src.get("source_mirror_url")!="https://fliphtml5.com/oreta/ewne/006_DSKP_KSSR_Tahun_6_-_SAINS/"
        or src.get("source_official_original_pdf_sha256") is not None
        or src.get("official_sp_count")!=96
        or src.get("original_pdf_statement_visual_signoffs")!=0
        or src.get("pdp_mapping_signoffs")!=0
        or src.get("academic_release_approved") is not False
        or src.get("ready_for_web_telegram") is not False
        or src.get("production_changes")!=0):
        raise ValueError("Sains Year6 secondary source inventory or release gate changed")
    ranges=src["official_sp_codes_by_sk_max_suffix"]
    expected_sks={"1.1","2.1","2.2","3.1","4.1","4.2","5.1",
                  "6.1","6.2","6.3","7.1","8.1","8.2","9.1",
                  "10.1","11.1","12.1","13.1"}
    if set(ranges)!=expected_sks or set(src["printed_pdf_page_ranges_by_sk"])!=expected_sks:
        raise ValueError("KSSR2017 Year6 official SK inventory missing")
    result=set()
    for sk,n in ranges.items():
        if not re.fullmatch(r"\d{1,2}\.\d",sk) or type(n) is not int or not 1<=n<=15:
            raise ValueError("Invalid KPM SK/SP numbering")
        pages=src["printed_pdf_page_ranges_by_sk"][sk]
        if len(pages)!=2 or any(type(p) is not int or not 54<=p<=86 for p in pages) or pages[0]>pages[1]:
            raise ValueError(f"Sains T6 original source page for {sk} invalid")
        result|={f"{sk}.{i}" for i in range(1,n+1)}
    if len(result)!=96 or "2.2.6" not in result or "3.2.1" in result:
        raise ValueError("Year6 source range set conflicts with KSSR2017 2021")
    return result

def audit():
    canonical=source_code_index()
    rows=source_records()[6]
    if len(rows)!=EXPECTED[6] or len(rows)!=84:
        raise ValueError("Sains Year6 historical PdP count changed")
    unmatched=[]
    used=set()
    for row in rows:
        if row.get("curriculum_text_matched") is not False or row.get("academic_release_approved") is not False:
            raise ValueError("Historical code membership is NOT a full academic signoff")
        sp=row["sp"]
        used.add(sp)
        if sp not in canonical:
            unmatched.append({
                "source_pdp_id":row["display_id"],
                "source_topic":row["topic"],
                "legacy_sp_code":sp,
                "action":"RECONCILE_TO_OFFICIAL_T6_DSKP_2021_STATEMENT_AND_BOOK_NOT_AUTO_MIGRATE",
                "academic_release_approved":False
            })
    not_in_separate_pdp=canonical-used
    kps_code_set={f"1.1.{i}" for i in range(1,13)}
    sort_code=lambda code: tuple(int(x) for x in code.split("."))
    kps_not_separately_indexed=sorted(not_in_separate_pdp & kps_code_set,key=sort_code)
    content_sp_not_indexed=sorted(not_in_separate_pdp-kps_code_set,key=sort_code)
    if len(kps_not_separately_indexed)+len(content_sp_not_indexed)!=len(not_in_separate_pdp):
        raise ValueError("Sains Year6 missing SP classification incomplete")
    return {
      "status":"SAINS_Y6_2021_SECONDARY_MIRROR_NUMERIC_CODE_ONLY_DRAF",
      "year":6,
      "historical_pdp_count":84,
      "source_official_sp_count":96,
      "historical_pdp_with_official_sp_code":84-len(unmatched),
      "historical_pdp_with_invalid_sp_code":len(unmatched),
      "invalid_sp_details":unmatched,
      "official_sp_not_represented_in_historical_84":sorted(not_in_separate_pdp,key=sort_code),
      "kps_1_1_not_separately_indexed":kps_not_separately_indexed,
      "non_kps_content_sp_not_separately_indexed":content_sp_not_indexed,
      "kps_sk_1_1_1_to_12_may_be_embedded_in_other_lessons_not_missing_12_new_pdp":True,
      "rph_kps_integration_signoffs":0,
      "original_kpm_pdf_sha_verified":False,
      "official_sp_text_visual_signoffs":0,
      "original_pdp_rph_book_sequence_signoffs":0,
      "ready_for_web_telegram":False,
      "production_changes":0
    }

def write_report(dest=OUT):
    out=Path(dest)
    if out.suffix!=".json" or "DRAF" not in out.stem.upper():
        raise ValueError("Source audit must remain a DRAF report")
    data=audit()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return out

if __name__=="__main__":
    p=write_report()
    d=json.loads(p.read_text("utf-8"))
    print("SAINS T6 original Year6 secondary source SP-code audit",
          d["historical_pdp_with_official_sp_code"],"/84 present,",
          d["historical_pdp_with_invalid_sp_code"],"need remap",
          "NOT FINAL",p)
