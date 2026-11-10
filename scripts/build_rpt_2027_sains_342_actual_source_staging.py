"""Sains T2–T6 2027: 5 five-column PARTIAL RPT proposals from distinct sourced PdP.

Read-only reconciliation:
- Actual numbered Sains PdP in historical v25.82 (NOT proven active on Web).
- Full SK/SP texts in current shipped v26.00 verified curriculum_standards.
- 2027 master A/B calendar week pairs (week window, not class timetable).
- 12 Year 3 DSKP text-correction candidates and 45 printed-page candidates
  remain marked proposals; originals never changed.

Nothing here certifies all Sains RPH, or updates Telegram, Web, users or DB.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date
import json
import re
import sqlite3

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.format_2026_layout_preview import build_preview,validate_rows
from tools.audit_sains_25_82_delta_20261106 import load,SOURCES,ROOT
from tools.audit_sains_v26_readonly_20261106 import verify_and_rebuild
from web.sains_canonical_unit_preview_20261106 import canonical_science_year
from rpt_2027.common.sains_y6_bpk_2020_panduan_43_sp_source import source_index as panduan_y6_source_index

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_342_pdp_SEPARA_DRAF"
EXPECTED={2:51,3:45,4:79,5:83,6:84}
DECLARED_SOURCE_NAME=SOURCES["v25.82"]
HOLD="DRAF LEGACY: SK/SP, RPH, buku teks dan KPS belum lulus audit akhir. BUKAN untuk digunakan guru. Minggu hanya CADANGAN."

def _normalize(value):
    return re.sub(r"\s+"," ",str(value or "")).strip()

def _standards(db):
    result={}
    for year in EXPECTED:
        cur=db.execute(
            "SELECT sk_code,sk_text,sp_code,sp_text,verified FROM curriculum_standards "
            "WHERE subject='Sains' AND year_label=?",(f"Tahun {year}",))
        d={}
        for sk,sk_text,sp,sp_text,verified in cur:
            if not sp or not _normalize(sp_text) or not _normalize(sk_text) or verified!=1:
                raise ValueError(f"Sains Y{year}: unverified full SK/SP in canonical source")
            if sp in d:
                raise ValueError(f"Sains Y{year}: duplicated DSKP SP code {sp}")
            d[sp]=dict(sk=_normalize(sk),sk_text=_normalize(sk_text),sp_text=_normalize(sp_text))
        result[year]=d
    return result

def _year3_ledgers():
    fixes=json.loads((ROOT/"audits/sains_y3_v2582_12_dskp_title_corrections_20261106.json").read_text("utf-8"))
    refs=json.loads((ROOT/"audits/sains_y3_v2582_45_textbook_page_candidates_20261106.json").read_text("utf-8"))
    if len(fixes["changes"])!=12 or len(refs["items"])!=45:
        raise ValueError("Sains Year3 historical candidate ledgers altered")
    return {a["pdp_code"]:a for a in fixes["changes"]},{a["pdp_code"]:a for a in refs["items"]}

def _year6_source_2021_sp_text_conflicts():
    """16 code-identical but differently worded SP in the 2021 Y6 DSKP.

    This corrects STAGED DISPLAY only, not the legacy DB or lesson title.
    Published 2021 DSKP has not yet been hashed as an original PDF.
    """
    p=ROOT/"rpt_2027/sains/sains_y6_kssr2017_2021_sistem_saraf_2_sp_text_corrections_20261108_DRAF.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    if (d.get("status")!="STAGING_SAINS_T6_2021_KPM_DSKP_TWO_NUMERIC_MATCH_BUT_TEXT_CONFLICTS_NOT_RELEASE"
        or d.get("year")!=6 or len(d.get("entries",[]))!=2
        or d.get("corrected_sp_display_count")!=2
        or d.get("year6_remaining_original_pdf_sp_wording_signoff_count")!=0
        or d.get("academic_2027_rph_approved") is not False
        or d.get("ready_for_web_telegram") is not False
        or d.get("production_db_writes")!=0):
        raise ValueError("Official Sains Year6 2.2.2/2.2.3 crosswalk gate changed")
    out={}
    for row in d["entries"]:
        code=row["sp_code"]
        if (code not in ("2.2.2","2.2.3") or code in out
            or row["original_2021_flip_pdf_page"]!=59
            or row["bpk_2020_guide_pdf_page"]!=23
            or not row["official_2021_dskp_text"]
            or row["official_2021_dskp_text"]==row["legacy_v26_text"]):
            raise ValueError("Unsafe official Year6 2.2.2/2.2.3 source mapping")
        out[code]=row
    if set(out)!={"2.2.2","2.2.3"}:
        raise ValueError("Missing official Sains Year6 nervous system statements")
    add=ROOT/"rpt_2027/sains/sains_y6_kssr2017_2021_14_additional_sp_text_conflicts_20261108_DRAF.json"
    extra=json.loads(add.read_text("utf-8"))
    if (extra.get("status")!="STAGING_SAINS_T6_2021_KPM_DSKP_FOURTEEN_MORE_SOURCE_TEXT_CONFLICTS_NOT_RELEASE"
        or extra.get("year")!=6
        or extra.get("additional_sp_wording_conflicts")!=14
        or len(extra.get("entries",[]))!=14
        or extra.get("original_source_binary_sha_verified") is not False
        or extra.get("academic_release_approved") is not False
        or extra.get("no_database_edit") is not True
        or extra.get("production_db_writes")!=0):
        raise ValueError("Additional KPM 2021 Sains Year6 source correction gate changed")
    expected_add={"3.1.2","3.1.3","3.1.4","3.1.5","5.1.5","5.1.6",
                  "6.2.2","6.2.3","6.3.2","6.3.3",
                  "7.1.1","7.1.2","7.1.3","7.1.4"}
    for item in extra["entries"]:
        sp=item["sp_code"]
        if (sp in out or sp not in expected_add
            or not item.get("legacy_v26_text") or not item.get("official_2021_dskp_text")
            or item["legacy_v26_text"]==item["official_2021_dskp_text"]
            or not 60<=item.get("source_flip_pdf_page",0)<=72
            or item.get("display_only") is not True
            or item.get("academic_rph_textbook_approved") is not False):
            raise ValueError("Unsafe extra Year6 original DSKP text correction")
        out[sp]=item
    if len(out)!=16 or set(out)!=expected_add|{"2.2.2","2.2.3"}:
        raise ValueError("Source-backed Year6 16-SP correction inventory missing")
    return out

def _missing_35_from_official_dskp():
    """35 Year2/3 printed SP statements directly from KPM PDF (not DB)."""
    p=ROOT/"rpt_2027/sains/dskp_sains_y2_y3_35_missing_sp_text_20261107_DRAF.json"
    src=json.loads(p.read_text("utf-8"))
    if src.get("status")!="STAGING_SOURCE_TEXT_ONLY_NOT_RELEASE_APPROVAL":
        raise ValueError("Unexpected Science official crosswalk release gate")
    records=src.get("records")
    if not isinstance(records,list) or len(records)!=35:
        raise ValueError("Sains official missing 35 source extraction incomplete")
    mapping={}
    for item in records:
        k=(item["year"],item["sp_code"])
        if k in mapping or item["year"] not in (2,3):
            raise ValueError("Sains duplicated or wrong-year DSKP crosswalk")
        if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{1,2}",item["sp_code"]):
            raise ValueError("Sains official SP code malformed")
        if not item.get("sp_text") or not (10<len(item["sp_text"])<300):
            raise ValueError("Sains official SP text missing")
        if not isinstance(item.get("pdf_page"),int) or not 40<=item["pdf_page"]<=85:
            raise ValueError("Sains official SP PDF page provenance missing")
        mapping[k]=item
    if sum(y==2 for y,code in mapping)!=20 or sum(y==3 for y,code in mapping)!=15:
        raise ValueError("Sains year breakdown of source crosswalk is wrong")
    return mapping

def _kssr2017_official_code_sets_y4_y5():
    """Original-PDF code membership only; not an academic PdP signoff."""
    raw=json.loads((ROOT/"rpt_2027/sains/"
                    "kssr2017_y4_y5_186_official_sp_source_extraction_20261107_DRAF.json")
                   .read_text("utf-8"))
    index=json.loads((ROOT/"rpt_2027/sains/"
                      "kssr2017_t4_t5_official_sp_code_ranges_20261107.json")
                     .read_text("utf-8"))
    if (raw.get("total_official_sp")!=186 or raw.get("academic_release_ready") is not False
        or raw.get("ready_for_web_telegram") is not False
        or raw.get("status")!="STAGING_KSSR2017_SOURCE_STATEMENTS_FROM_ORIGINAL_PDF_EXTRACT_PENDING_VISUAL_SIGNOFF"):
        raise ValueError("KSSR2017 official Year4/5 source index is missing/approved")
    result={}
    for entry in index["years"]:
        year=entry["year"]
        if year not in (4,5) or year in result:
            raise ValueError("Unknown/duplicated original source year")
        expected={f"{sk}.{i}" for sk,last in entry["sk_sp_max_suffix"].items()
                  for i in range(1,last+1)}
        records=[r for r in raw["rows"] if r.get("year")==year]
        codes={r.get("sp_code") for r in records}
        if (codes!=expected or len(records)!=len(expected)
            or raw["source"][str(year)]["official_pdf_sha256"]!=entry["sha256"]
            or raw["source"][str(year)]["visual_signoff_count"]!=0
            or any(r["visual_signoff"] is not False for r in records)):
            raise ValueError(f"Sains T{year} original code ledger failed integrity check")
        result[year]=codes
    if {y:len(v) for y,v in result.items()}!={4:91,5:95}:
        raise ValueError("Original KSSR2017 Year4/5 source inventory incomplete")
    return result

def _proposed_week_slots(master):
    # Year 2-6 must not lose M01: the transition-week assumption belongs
    # only to an explicitly sourced school Year 1 programme. KPM opens
    # *both* 2027 school groups on 4 January. This remains a provisional
    # week-window projection and does not create or reorder any Sains PdP.
    # M06 is the February CNY school closure window; M44 is still reserved
    # for end-of-year school arrangements. Never infer exact PdP days.
    numbers=[i for i in range(1,44) if i!=6]
    week_ids=[f"M{i:02d}" for i in numbers]
    if len(week_ids)!=42 or any(w not in master["A"] or w not in master["B"] for w in week_ids):
        raise ValueError("KPM proposed week windows incomplete")
    return week_ids

def source_records():
    master=load_calendar_weeks()
    fix,book=_year3_ledgers()
    dskp_missing=_missing_35_from_official_dskp()
    official_2017=_kssr2017_official_code_sets_y4_y5()
    panduan_2020=panduan_y6_source_index()
    y6_text_fixes=_year6_source_2021_sp_text_conflicts()
    seen_dskp_missing=set()
    years={}
    with TemporaryDirectory(prefix="cikgulaju_sains_rpt_ro_") as tmp:
        base=Path(tmp)
        original=load(DECLARED_SOURCE_NAME,ROOT,base)
        if len(original)!=385:
            raise ValueError("Sains v25.82 did not contain exact 385 historical PdP")
        manifest=verify_and_rebuild(base,ROOT)
        with sqlite3.connect(f"file:{manifest}?mode=ro&immutable=1",uri=True) as db:
            standards=_standards(db)

        weeks=_proposed_week_slots(master)
        for year,expected in EXPECTED.items():
            src=sorted(
                (r for r in original if r.get("subject")=="Sains"
                 and r.get("year_label")==f"Tahun {year}"),
                key=lambda r:int(r.get("source_sequence_no") or 0)
            )
            if len(src)!=expected:
                raise ValueError(f"Year{year} source incomplete: {len(src)}/{expected}")
            ids=[int(r["source_sequence_no"]) for r in src]
            codes=[str(r.get("pdp_sequence_code") or "").strip() for r in src]
            if ids!=list(range(1,expected+1)) or len(set(codes))!=expected:
                raise ValueError(f"Year{year}: noncontiguous/duplicate canonical PdP")
            # This existing adapter only fixes DISPLAY UNIT identity. It
            # retains original source code, SP, PdP identity and raw titles.
            indexed,_=canonical_science_year(src,year,2027)
            rows=[]
            for index,raw in enumerate(indexed):
                number=index+1
                sp=_normalize(raw.get("sp_code"))
                sk=_normalize(raw.get("sk_code"))
                pdp_code=_normalize(raw.get("pdp_sequence_code"))
                if not re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{1,3}",sp):
                    raise ValueError("Invalid source Sains SP")
                if not sk or not pdp_code:
                    raise ValueError("Source Sains SK/PdP empty")
                verified=standards[year].get(sp)
                extract=dskp_missing.get((year,sp))
                if verified and extract:
                    raise ValueError("Sains official DSKP supplemental text overlaps verified v26 row")
                if verified and verified["sk"]!=sk:
                    raise ValueError(f"Year{year} {pdp_code}: DSKP SK conflict {sk}/{verified['sk']}")
                if verified:
                    sk_display=sk+" — "+verified["sk_text"]
                    sp_display=sp+" — "+verified["sp_text"]
                    curriculum_provenance="V26_DB_VERIFIED_FLAG_NOT_EXTERNAL_DSKP_SIGNOFF"
                elif extract:
                    # Derive the SK statement from another verified SP sharing
                    # that same SK in *the same year*, not from lesson titles.
                    matches={v["sk_text"] for v in standards[year].values() if v["sk"]==sk}
                    if len(matches)!=1:
                        raise ValueError(f"Sains Y{year} {sp}: verified SK statement unavailable")
                    sk_display=sk+" — "+matches.pop()
                    sp_display=sp+" — "+extract["sp_text"]
                    curriculum_provenance="KPM_DSKP_ORIGINAL_PDF_TEXT_SP_COLUMN"
                    seen_dskp_missing.add((year,sp))
                else:
                    raise ValueError(f"Sains Y{year} {sp}: no official DSKP statement for source PdP")
                unit=_normalize(raw.get("unit_title"))
                focus=_normalize(raw.get("pdp_title"))
                if not unit or not focus:
                    raise ValueError(f"Year{year} {pdp_code}: original PdP title/unit blank")
                note=f"{pdp_code} | v25.82: {_normalize(raw.get('verification_status'))}. {HOLD}"
                y6_text_fix=y6_text_fixes.get(sp) if year==6 else None
                if y6_text_fix:
                    # A shared numeric SP code hides distinct teaching targets.
                    if (verified is None
                        or _normalize(verified["sp_text"])!=_normalize(y6_text_fix["legacy_v26_text"])
                        or pdp_code!=y6_text_fix["historical_pdp_code"]):
                        raise ValueError("Sains T6 original text no longer matches conflict evidence")
                    sp_display=sp+" — "+y6_text_fix["official_2021_dskp_text"]
                    curriculum_provenance="KPM2021_PUBLISHED_DSKP_EXACT_SP_DISPLAY_ONLY_NOT_ACADEMIC_SIGNOFF"
                    note+=(" AMARAN: Teks SP v26 berbeza daripada DSKP 2021 (SP "+
                           sp+"). Teks rasmi dicadang hanya pada RPT staging;"+
                           " RPH sebenar WAJIB disemak sebelum pengguna.")
                official_membership=(sp in official_2017[year] if year in (4,5) else None)
                if official_membership is False:
                    note+=f" AMARAN: kod SP {sp} TIADA dalam DSKP KSSR2017 Tahun {year} asal; wajib petakan semula sebelum RPT pengguna."
                if extract:
                    note+=f" SP KPM DSKP asli PDF hlm {extract['pdf_page']} (teks lajur SP)."
                if year==3:
                    if pdp_code not in book:
                        raise ValueError("Year3 page ledger missing candidate PdP")
                    cue=book[pdp_code]
                    if cue.get("sp_code")!=sp:
                        raise ValueError("Year3 printed-page candidate mismatches SP")
                    pages=cue["printed_book_page_candidates"]
                    note+=f" BT m/s cadangan: {', '.join(map(str,pages))} (belum sah visual)."
                    if pdp_code in fix:
                        item=fix[pdp_code]
                        if item.get("sp_code")!=sp:
                            raise ValueError("Year3 title correction SP changed")
                        # Use known source-confirmed DSKP text as *display*
                        # only, retain raw historical title separately.
                        focus=item["ds_kpm_official_sp_text"]
                        note+=" Tajuk paparan ikut calon pembetulan DSKP."
                # 2020 BPK activity guide is supplementary KPS evidence,
                # NOT the official 2021 DSKP statement and NOT proof that
                # the historical RPH embeds the skill. Add source trace only.
                panduan_refs=panduan_2020.get(sp,[]) if year==6 else []
                panduan_pages=[r["pdf_page"] for r in panduan_refs]
                panduan_kps=sorted({term for r in panduan_refs for term in r["kps_terms"]})
                if panduan_refs:
                    note+=(" Panduan PdP BPK (2020) PDF hlm "+
                           ", ".join(map(str,panduan_pages))+
                           " — contoh KPS: "+", ".join(panduan_kps)+
                           " (BUKAN semakan RPH/DSKP 2021).")
                guide_year6_edition_mismatch=year==6 and sp in {"7.1.1","7.1.2","7.1.3"}
                if guide_year6_edition_mismatch:
                    note+=(" AWAS: Panduan PdP 2020 SP "+sp+
                           " berbeza fokus daripada DSKP 2021; jangan guna aktiviti sebagai padanan terus.")
                week=weeks[index*len(weeks)//expected]
                a=master["A"][week];b=master["B"][week]
                rows.append(dict(
                    id=f"{number:03d}",display_id=pdp_code,
                    unit=unit,topic=focus,sk=sk,sp=sp,
                    sk_display=sk_display,sp_display=sp_display,
                    note=note[:700],week=week,
                    a_start=a[0],a_end=a[1],b_start=b[0],b_end=b[1],
                    # DB verified=1 proves a populated internal record only.
                    # A source statement, including an original PDF extract,
                    # is NOT an independently signed-off SK/SP-to-PdP match.
                    curriculum_text_matched=False,
                    source_statement_available=True,
                    official_kssr2017_code_membership=official_membership,
                    academic_release_approved=False,
                    live_download_verified=False,
                    curriculum_provenance=curriculum_provenance,
                    source_status=_normalize(raw.get("verification_status")),
                    raw_pdp_title=_normalize(raw.get("pdp_title")),
                    week_allocation="PROPOSED_2027_WEEK_NOT_TIMETABLE",
                    panduan_y6_2020_pdf_pages=panduan_pages,
                    panduan_y6_2020_kps_terms=panduan_kps,
                    panduan_y6_2020_sp_code_source_found=bool(panduan_refs),
                    panduan_y6_2020_is_approved_rph=False,
                    year6_official_2021_sp_display_reconciled=bool(y6_text_fix),
                    year6_legacy_original_sp_text=(y6_text_fix["legacy_v26_text"]
                                                   if y6_text_fix else ""),
                    year6_official_2021_original_pdf_sha_verified=False,
                    panduan_y6_2020_to_2021_sp_focus_changed=bool(guide_year6_edition_mismatch)
                ))
            validate_rows("sains",year,rows)
            years[year]=rows
    if seen_dskp_missing!=set(dskp_missing):
        raise ValueError("Sains 35 official supplemental SP records not consumed exactly once")
    return years

def build_all(destination=OUT):
    dest=Path(destination)
    source=source_records()
    result=[]
    for year,rows in source.items():
        filename=f"CIKGULAJU_RPT_SAINS_TAHUN_{year}_2027_5_LAJUR_{len(rows)}_PDP_SEPARA_DRAF.pdf"
        path=dest/filename
        build_preview("sains",year,rows,path,max_span_rows=2)
        result.append((year,len(rows),sum(r["curriculum_text_matched"] for r in rows),path))
    if len(result)!=5 or sum(x[1] for x in result)!=342:
        raise ValueError("Source Sains five-year PdP count incomplete")
    return result


if __name__=="__main__":
    for year,n,matched,filename in build_all():
        print(f"SAINS_RPT_SEPARA_DRAF Y{year} {n} PdP, academic_SP_signoffs={matched}, output={filename}")
