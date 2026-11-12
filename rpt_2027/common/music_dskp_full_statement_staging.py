"""DSKP-sourced Music SK/SP statements for the unified 2027 RPT previews.

Strictly a display enrichment from KPM Year2-6 source PDFs. Does not claim
authentic performance notation was converted, approve the DSKP Year4 numeric
inconsistencies, change CSV/RPH, or alter production curriculum sources.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EXPECTED={2:20,3:22,4:19,5:20,6:18}
SOURCE_STATUS="DSKP_SOURCE_TEXT_STAGING_NOT_OFFICIAL_RELEASE"

def _catalog(year):
    if year not in EXPECTED:
        raise ValueError("Music DSKP year unsupported")
    path=ROOT/"staging/pendidikan_muzik/rpt_rph_2027"/f"DSKP_MUSIC_FULL_TEXT_Y{year}_20261107_DRAF.json"
    source=json.loads(path.read_text("utf-8"))
    if (source.get("year")!=year or source.get("status")!=SOURCE_STATUS or
        len(source.get("sp",[]))!=EXPECTED[year] or
        len(source.get("source_pdf",{}).get("sha256",""))!=64):
        raise ValueError("Music source DSKP fingerprint or catalog changed")
    codes={}
    for sp in source["sp"]:
        code=sp["code"]
        if code in codes or not re.fullmatch(r"\d+\.\d+\.\d+",code):
            raise ValueError(f"Music Year {year} duplicate or malformed DSKP code")
        sk=sp["sk"]
        title=source["sk_titles"].get(sk)
        if not title or title!=sp["sk_title"]:
            raise ValueError("Music official SK title mismatch")
        if not sp["text"] or "Pernyataan penuh" in sp["text"]:
            raise ValueError("Music source SP statement missing")
        if not (30<=sp["pdf_page"]<=45):
            raise ValueError("Music source PDF page outside DSKP tables")
        codes[code]=sp
    return codes

def music_full_standard_display(year, original_codes):
    """Return SK, SK statement, SP statement, note. Fail on any unknown SP."""
    catalog=_catalog(year)
    codes=[x.strip() for x in re.split(r"\s*[/;,]\s*",original_codes) if x.strip()]
    if not codes or len(set(codes))!=len(codes):
        raise ValueError("Music RPT invalid or duplicated SP codes")
    entries=[]
    for code in codes:
        if code not in catalog:
            raise ValueError(f"Music Year {year} source SP {code} not in DSKP")
        entries.append(catalog[code])
    parents=[]
    for row in entries:
        sk=row["sk"]
        if sk not in parents:
            parents.append(sk)
    sk_display="\n".join(f"{sk} — {next(x for x in entries if x['sk']==sk)['sk_title']}"
                         for sk in parents)
    sp_display="\n".join(f"{x['code']} — {x['text']}" for x in entries)
    notes=[]
    graphics=[x for x in entries if x.get("figure_or_score_required")]
    if graphics:
        page_str=", ".join(sorted(set(str(x["pdf_page"]) for x in graphics)))
        notes.append(f"Simbol/skor tidak penuh dalam teks; rujuk rajah DSKP PDF hlm {page_str}")
    if year==4 and any(x["code"].startswith("3.2.") or x["code"]=="4.2.1"
                       for x in entries):
        notes.append("DSKP T4 bercetak: SK 3.1/4.1 dengan kod SP 3.2.x/4.2.1; kekalkan konflik sumber")
    if year==2 and any(x["code"].startswith("1.1.") for x in entries):
        notes.append("DSKP T2 cetak SK Elemen Muzik sebagai 1.1.1; label asas 1.1 untuk susun RPT")
    return {
        "sk":" / ".join(parents),
        "sk_display":sk_display,
        "sp":" / ".join(codes),
        "sp_display":sp_display,
        "source_note":"; ".join(notes),
        "catalog_count":len(catalog),
    }
