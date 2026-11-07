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

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_342_pdp_SEPARA_DRAF"
EXPECTED={2:51,3:45,4:79,5:83,6:84}
DECLARED_SOURCE_NAME=SOURCES["v25.82"]
HOLD="DRAF, bukan RPT lengkap atau kandungan LIVE; agihan minggu hanya CADANGAN."

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

def _proposed_week_slots(master):
    # NO fiction of exact lesson dates or teacher timetable. Skip first
    # transition week, the all-state disruption week M06, and M44 closing.
    # All slots refer to master Kumpulan A/B week *windows*, not PdP days.
    numbers=[i for i in range(2,44) if i!=6]
    week_ids=[f"M{i:02d}" for i in numbers]
    if len(week_ids)!=41 or any(w not in master["A"] or w not in master["B"] for w in week_ids):
        raise ValueError("KPM proposed week windows incomplete")
    return week_ids

def source_records():
    master=load_calendar_weeks()
    fix,book=_year3_ledgers()
    dskp_missing=_missing_35_from_official_dskp()
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
                    curriculum_provenance="V26_VERIFIED_DSKP"
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
                week=weeks[index*len(weeks)//expected]
                a=master["A"][week];b=master["B"][week]
                rows.append(dict(
                    id=f"{number:03d}",display_id=pdp_code,
                    unit=unit,topic=focus,sk=sk,sp=sp,
                    sk_display=sk_display,sp_display=sp_display,
                    note=note[:700],week=week,
                    a_start=a[0],a_end=a[1],b_start=b[0],b_end=b[1],
                    curriculum_text_matched=True,
                    curriculum_provenance=curriculum_provenance,
                    source_status=_normalize(raw.get("verification_status")),
                    raw_pdp_title=_normalize(raw.get("pdp_title")),
                    week_allocation="PROPOSED_2027_WEEK_NOT_TIMETABLE"
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
        print(f"SAINS_RPT_SEPARA_DRAF Y{year} {n} PdP, matched_full_SP={matched}, output={filename}")
