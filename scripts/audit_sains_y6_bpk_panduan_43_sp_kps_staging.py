"""Map 2020 BPK Sains Year6 Panduan activities to each historical 84 PdP.

Evidence tells teachers which published activity/KPS examples are nearby,
not whether the historical RPH includes a correct scientific investigation.
No RPH data or runtime database is changed.
"""
import json
from pathlib import Path
from rpt_2027.common.sains_y6_bpk_2020_panduan_43_sp_source import (
    source_index, SOURCE, SHA
)
from scripts.build_rpt_2027_sains_342_actual_source_staging import ROOT,source_records,EXPECTED
from scripts.audit_sains_y6_2021_secondary_mirror_codes_staging import source_code_index

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_y6_2020_BPK_guide_43_sp_84_pdp_kps_DRAF.json"

def audit():
    guide=source_index()
    official=source_code_index()
    records=source_records()[6]
    if len(records)!=84 or len(records)!=EXPECTED[6]:
        raise ValueError("Historical Sains Year6 count changed")
    rows=[]
    found=set()
    missing=set()
    appearances=0
    edition_conflicts=set()
    for r in records:
        sp=r["sp"]
        if sp not in official or r.get("academic_release_approved") is not False:
            raise ValueError("2021 code membership or release status invalid")
        refs=guide.get(sp,[])
        pages=[x["pdf_page"] for x in refs]
        kps=sorted({name for x in refs for name in x["kps_terms"]})
        if refs:
            found.add(sp)
            appearances+=len(refs)
            if r["panduan_y6_2020_pdf_pages"]!=pages or r["panduan_y6_2020_kps_terms"]!=kps:
                raise ValueError("Sains Year6 RPT BPK source reference not propagated")
            if "Panduan PdP BPK (2020) PDF hlm " not in r["note"]:
                raise ValueError("Source page not visible in staged RPT notes")
        else:
            missing.add(sp)
            if r["panduan_y6_2020_pdf_pages"] or r["panduan_y6_2020_kps_terms"]:
                raise ValueError("Sains Year6 note falsely claims a 2020 exemplar")
        shift=sp in {"7.1.1","7.1.2","7.1.3"}
        if r.get("panduan_y6_2020_to_2021_sp_focus_changed") is not shift:
            raise ValueError("2020 guide and 2021 DSKP edition conflict flag not propagated")
        if shift:
            edition_conflicts.add(sp)
        if r.get("curriculum_text_matched") is not False or r["panduan_y6_2020_is_approved_rph"] is not False:
            raise ValueError("BPK Panduan 2020 cannot approve 2027 RPH")
        rows.append({
            "pdp_id":r["display_id"],"original_year6_sp":sp,
            "pdp_topic":r["topic"],"bpk_panduan_2020_has_example":bool(refs),
            "source_pdf_pages":pages,"suggested_kps_terms_from_guide":kps,
            "historical_rph_kps_implementation_verified":False,
            "2020_guide_sp_focus_differs_from_2021_dskp":shift,
            "official_2021_sp_text_verified":False,
            "approved_for_user_download":False,
        })
    if (len(found)!=43 or found!=set(guide) or len(missing)!=41 or
        len(set(found)|set(missing))!=84 or appearances!=46 or
        edition_conflicts!={"7.1.1","7.1.2","7.1.3"}):
        raise ValueError("BPK Year6 exemplar mapping changed: 43/84 / 46 pages expected")
    return {
        "status":"SAINS_Y6_2020_BPK_PANDUAN_KPS_SOURCE_PDP_CROSSWALK_DRAF_NOT_RPH_SIGNOFF",
        "source_file_sha256":SHA,
        "source_url":SOURCE,
        "source_title":"Panduan Pengajaran dan Pembelajaran Sains Tahun 6 (BPK, 2020)",
        "year":6,
        "historical_pdp_count":84,
        "historical_pdp_with_bpk_2020_example":len(found),
        "historical_pdp_without_specific_2020_example":len(missing),
        "source_page_to_pdp_references":appearances,
        "unique_2020_exemplar_source_sections":16,
        "guide2020_year6_sp_edition_conflict_codes":sorted(edition_conflicts),
        "guide2020_sp_codes_without_known_edition_conflict_NOT_APPROVED":len(found-edition_conflicts),
        "kps_not_separately_timetabled_but_integrated_into_rph_verified":0,
        "original_2021_dskp_source_sp_wording_signoffs":0,
        "approved_rph_count":0,
        "ready_for_web_telegram":False,
        "database_writes":0,
        "rows":rows
    }

def write_report(path=OUT):
    target=Path(path)
    if target.suffix!=".json" or "DRAF" not in target.stem.upper():
        raise ValueError("BPK source audit must remain named DRAF")
    data=audit()
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return target

if __name__=="__main__":
    file=write_report()
    data=json.loads(file.read_text("utf-8"))
    print("SAINS Y6 BPK 2020 source",data["historical_pdp_with_bpk_2020_example"],
          "/84 lesson sources, remaining",data["historical_pdp_without_specific_2020_example"],
          "uncovered in guide. RPH SIGNOFF 0. STAGING",file)
