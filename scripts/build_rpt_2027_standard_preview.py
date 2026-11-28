"""Staging-only build of source-faithful RPT 2027 in a unified 2026 layout.

PSV, RBT and Moral can be reflowed *without guessing* because their year-level
source manifests still exist. No changes to Telegram/Web download paths.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from rpt_2027.common.format_2026_layout_preview import build_preview, validate_rows
from rpt_2027.common.standard_text_enrichment import enrich_moral, enrich_psv, enrich_rbt
from rpt_2027.common.calendar_week_mapping_staging import reconcile_psv_weeks
from rpt_2027.common.rbt_truncated_title_guard_staging import expand_rbt_display_titles
from rpt_2027.common.rbt_2026_week_source_annotation_staging import annotate_rbt_2026_week_reference
from rpt_2027.common.week1_owner_plan_20261110 import allocate_rbt_weeks

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "staging" / "rpt_2027_seragam_2026" / "pdf"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def psv_records(year):
    from rpt_2027.psv.telegram_downloads import source_rows
    rows = source_rows(year)  # original 42-PdP SK/SP checks, not rewritten
    calendar = read_csv(ROOT / "rpt_2027/psv/PSV_2027_minggu_PdP_kumpulan_A_B_CADANGAN.csv")
    if len(rows) != 42 or len(calendar) != 42:
        raise ValueError("PSV source/calendar incomplete")
    output=[]
    for n,(r,week) in enumerate(zip(rows,calendar),1):
        ident=f"{n:03d}"
        if r.get("PdP")!=ident or week.get("PdP")!=ident:
            raise ValueError("PSV calendar source PdP order mismatch")
        raw_week=r.get("Minggu PdP (cadangan)") or r.get("Turutan PdP cadangan")
        raw_unit=(r.get("Unit") or r.get("Unit 2026") or "").strip()
        unit_name=(r.get("Bidang") or r.get("Tajuk unit") or "").strip()
        if not raw_week or not raw_unit or not unit_name:
            raise ValueError("PSV source missing year-specific week/unit fields")
        unit=raw_unit if raw_unit.lower().startswith("unit ") else "Unit "+raw_unit
        if unit_name.casefold() not in unit.casefold():
            unit+=": "+unit_name
        focus=(r.get("Fokus") or r.get("Modul") or "").strip()
        topic=(r.get("Tajuk karya cadangan") or r.get("Tajuk/aktiviti PdP") or "").strip()
        book=(r.get("BT muka surat") or r.get("Rujukan BT ms (RPT 2026)") or "").strip()
        technique=r.get("Teknik","").strip()
        output.append({
            "id":ident,
            "week":"M"+str(raw_week).zfill(2),
            "a_start":week["Minggu_A_mulai"],"a_end":week["Minggu_A_hingga"],
            "b_start":week["Minggu_B_mulai"],"b_end":week["Minggu_B_hingga"],
            "unit":unit,
            "topic":topic+(" | Fokus: "+focus if focus else ""),
            "sk":r["SK"],"sp":r["SP"],
            "note":(("Teknik: "+technique+". ") if technique else "")+
                    "Objektif: "+r["Objektif"]+
                    ". PBD: "+r["Evidens PBD"].strip().rstrip(" .")+
                    (". Buku teks: "+book if book else "")+
                    ". Tarikh dan halaman BT: cadangan, perlu disemak."
        })
    enrich_psv(year,output)
    reconcile_psv_weeks(output)
    validate_rows("psv",year,output)
    return output


def rbt_records(year):
    from rpt_2027.rbt.pdf_runtime import source_rows
    rows = source_rows(year)  # original JSON RPH crosswalk validation
    if len(rows)!=32:
        raise ValueError("RBT source/RPH crosswalk incomplete")
    output=[]
    for n,r in enumerate(rows,1):
        ident=f"{n:03d}"
        if int(r["PdP"])!=n or not r["Unit"].startswith("Unit "):
            raise ValueError("RBT PdP/unit source mismatch")
        output.append({
            "id":ident,"week":"",  # NEVER invent official lesson weeks
            "a_start":"","a_end":"","b_start":"","b_end":"",
            "unit":r["Unit"],
            "topic":re.sub(r"^PdP\s+0*"+str(n)+r"\s*[:：—–-]\s*", "",
                           r["Tajuk PdP"], flags=re.IGNORECASE),
            "sk":r["SK"],"sp":r["SP"],
            "note":("Masa: "+r["Masa minit"]+" minit. Buku teks m/s: "+
                    (r.get("Rujukan Buku Teks m/s") or "belum disahkan")+
                    ". Tarikh A/B belum dinyatakan dalam sumber; tidak diandaikan.")
        })
    enrich_rbt(year,output)
    expand_rbt_display_titles(year,rows,output)
    annotate_rbt_2026_week_reference(year,output)
    validate_rows("rbt",year,output)
    return output


def moral_records(year):
    path = ROOT / "rpt_2027/pendidikan_moral"
    a=read_csv(path / f"year{year}_sequence_96_2027_groupA_STAGING.csv")
    b=read_csv(path / f"year{year}_sequence_96_2027_groupB_STAGING.csv")
    if len(a)!=96 or len(b)!=96:
        raise ValueError("Moral source must have 96 sessions per group")
    output=[]
    for n,(left,right) in enumerate(zip(a,b),1):
        ident=f"{n:03d}"
        for field in ("Tahun","Sesi","Unit","Tajuk_Unit","SK","SP","Nilai"):
            if left.get(field)!=right.get(field):
                raise ValueError("Moral A/B source content differs at "+field)
        if (left["Sesi"]!=ident or left["Tahun"]!=str(year) or
            left["Kumpulan"]!="A" or right["Kumpulan"]!="B"):
            raise ValueError("Moral group/sequence source mismatch")
        output.append({
            "id":ident,"week":left["Minggu_RPT"],
            "a_start":left["Tarikh_Minggu_Mula"],"a_end":left["Tarikh_Minggu_Tamat"],
            "b_start":right["Tarikh_Minggu_Mula"],"b_end":right["Tarikh_Minggu_Tamat"],
            "unit":f"Unit {left['Unit']}: {left['Tajuk_Unit']}",
            "topic":"Nilai: "+left["Nilai"]+" | "+left["Fokus"],
            "sk":left["SK"],"sp":left["SP"],
            "note":("Modul: "+left["Modul"]+". Aktiviti guru: "+left["Aktiviti_Guru"]+
                    " Aktiviti murid: "+left["Aktiviti_Murid"]+
                    " PBD: "+left["Evidens_PBD"].strip().rstrip(" .")+".")
        })
    enrich_moral(year,output)
    validate_rows("moral",year,output)
    return output


def build_all(destination=OUT):
    destination=Path(destination)
    built=[]
    for subject,years,loader in (
        ("psv",range(2,7),psv_records),
        ("rbt",range(4,7),rbt_records),
        ("moral",range(2,7),moral_records)
    ):
        for year in years:
            rows=loader(year)
            if subject=="rbt":
                # Keep rbt_records() source-faithful for teacher override paths.
                # Only staging PDF uses the owner-requested provisional plan.
                rows=allocate_rbt_weeks(rows, year=year)
            if any(not row.get("sk_display") or not row.get("sp_display") for row in rows):
                raise ValueError("All staged RPT rows must have full sourced SK/SP statements")
            target=destination / f"CIKGULAJU_RPT_{subject.upper()}_TAHUN_{year}_2027_FORMAT_SERAGAM_DRAF.pdf"
            build_preview(subject,year,rows,target)
            built.append((subject,year,len(rows),target))
    return built


if __name__=="__main__":
    for subject,year,count,path in build_all():
        print(f"{subject.upper()} Tahun {year}: {count} PdP -> {path}")
