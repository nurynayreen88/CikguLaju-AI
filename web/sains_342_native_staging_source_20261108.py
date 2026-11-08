"""Build-free, staging-only Telegram/Web reviewer for 342 Sains PdP, T2–T6.

IMPORTANT: This is NOT a public release or teacher/panitia approval. The
authoring activity banks and DSKP source ledger are committed to Git; runtime
does not require the ephemeral CI-generated build/sains_2027 indices.
Live Telegram/Web is unchanged unless both opt-in flags are provided on an
isolated staging Render service; known production Render IDs are forbidden.
"""
from __future__ import annotations

from functools import lru_cache
import os
import re

FLAG="CIKGULAJU_SAINS_342_INTERNAL_REVIEW"
CONTEXT="CIKGULAJU_CURRICULUM_DEPLOYMENT"
PRODUCTION_SERVICE_IDS={
    "srv-dah3b8lbedkc738ugqt0",  # Telegram
    "srv-dbm5go8u01pc738f40cg",  # Web
}
EXPECTED={2:51,3:45,4:79,5:83,6:84}
UNIT_TITLES={
    2:{3:"Manusia",4:"Haiwan",5:"Tumbuhan",6:"Terang dan Gelap",
       7:"Elektrik",8:"Campuran",9:"Bumi",10:"Teknologi"},
    3:{3:"Manusia",4:"Haiwan",5:"Tumbuhan",6:"Pengukuran",
       7:"Ketumpatan",8:"Asid dan Alkali",9:"Sistem Suria",10:"Mesin"},
    4:{2:"Manusia",3:"Haiwan",4:"Tumbuhan",5:"Sifat Cahaya",
       6:"Bunyi",7:"Tenaga",8:"Bahan",9:"Bumi",10:"Mesin"},
    5:{2:"Manusia",3:"Haiwan",4:"Tumbuhan",5:"Elektrik",
       6:"Haba",7:"Pengaratan",8:"Jirim",9:"Fasa Bulan dan Buruj",10:"Mesin"},
    6:{2:"Manusia",3:"Mikroorganisma",4:"Interaksi Antara Hidupan",
       5:"Pemeliharaan dan Pemuliharaan",6:"Daya",7:"Kelajuan",
       8:"Pengawetan Makanan",9:"Bahan Buangan",10:"Gerhana",
       11:"Bumi dan Angkasa",12:"Kestabilan dan Kekuatan",13:"Teknologi"},
}
SOURCE_STATE="STAGING_DRAF_HOLD_NOT_APPROVED"


def _year(value):
    if type(value) is int:
        return value
    matched=re.fullmatch(r"(?:Tahun\s*)?([2-6])",str(value or "").strip(),re.I)
    return int(matched.group(1)) if matched else None


def _is_review_sains(year,subject):
    return _year(year) in EXPECTED and re.sub(
        r"\s+","",str(subject or "").casefold()) in ("sains","science")


def _sp_sort(sp):
    return tuple(int(x) for x in sp.split("."))


@lru_cache(maxsize=1)
def _catalog():
    """Read committed academic source files only: absolutely no build/ IO."""
    from web.sains_y2_51_activities_draf_20261107 import BANK as y2
    from web.sains_y3_rph_activity_preview_20261106 import (
        BANK as y3,source_ledgers,checked_book_pages as year3_book,
    )
    from web.sains_y4_79_activity_bank_draf_20261107 import BANK as y4
    from web.sains_y5_83_activity_bank_draf_20261107 import BANK as y5
    from web.sains_y6_84_activity_bank_draf_20261107 import BANK as y6
    from tools.sains_y4_79_official_sp_statements_20261108 import (
        checked_statements as y4_dskp,
    )
    from tools.sains_y5_kssr2017_official_sp_statements_20261107 import (
        checked_statements as y5_dskp,
    )
    from tools.sains_y5_83_textbook_original_sp_pages_20261107 import (
        checked_book_pages as y5_book,
    )
    from tools.render_sains_y2_51_rph_draf_20261107 import (
        verified_original_textbook_pages as y2_book,
    )
    banks={2:y2,3:y3,4:y4,5:y5,6:y6}
    official={4:y4_dskp(),5:y5_dskp()}
    pages={2:y2_book(),3:year3_book(),5:y5_book()}
    year3,fixes=source_ledgers()
    if (len(year3)!=45 or len(fixes)!=12 or set(EXPECTED)!=set(banks)
        or len(official[4])!=79 or len(official[5])!=83):
        raise ValueError("Sains original source and DSKP coverage changed")
    lessons={}
    for year,bank in banks.items():
        if len(bank)!=EXPECTED[year]:
            raise ValueError("Sains bank year count changed "+str(year))
        sp_codes=sorted(bank,key=_sp_sort)
        if len(sp_codes)!=len(set(sp_codes)):
            raise ValueError("Duplicate Science SP")
        for no,sp in enumerate(sp_codes,1):
            if not re.fullmatch(r"(?:[2-9]|1[0-3])\.\d+\.\d+",sp):
                raise ValueError("Invalid source SP "+sp)
            sk=sp.rsplit(".",1)[0]
            unit_number=int(sp.split(".")[0])
            unit_title=UNIT_TITLES[year].get(unit_number)
            if not unit_title:
                raise ValueError(f"Unmapped original Science unit {year}: {sp}")
            code=f"SCI-Y{year}-PDP-{no:03d}"
            raw=bank[sp]
            if year==3:
                if not isinstance(raw,tuple) or len(raw)!=7:
                    raise ValueError("Unexpected Year3 activity source "+sp)
                source=year3.get(code)
                if source is None or source["sp_code"]!=sp or source["release"]!="HOLD":
                    raise ValueError("Year3 historical PdP/SP identity changed "+code)
                title=source["source_pdp_title_unverified"]
                if code in fixes:
                    fix=fixes[code]
                    if fix["sp_code"]!=sp or fix["original_title"]!=title:
                        raise ValueError("Year3 official DSKP title fix source changed")
                    title=fix["ds_kpm_official_sp_text"]
                activities=dict(zip(("hook","teacher1","pupil1","teacher2","pupil2",
                                     "pbd","materials"),raw))
                activities["safety"]=(
                    "Guru menyelia pengendalian bahan/alat mengikut panduan "
                    "keselamatan sains dan kesesuaian umur; panitia perlu mengesahkan"
                )
                book=pages[3].get(code)
                if book is None or book["sp"]!=sp:
                    raise ValueError("Year3 original book evidence missing "+code)
                printed=book["printed_page_candidates"]
            else:
                if not isinstance(raw,dict) or not all(
                    isinstance(raw.get(k),str) and len(raw[k])>8
                    for k in ("hook","teacher1","pupil1","teacher2","pupil2",
                              "pbd","materials","safety")):
                    raise ValueError("Incomplete source-specific Science bank "+code)
                activities={k:raw[k] for k in ("hook","teacher1","pupil1",
                             "teacher2","pupil2","pbd","materials","safety")}
                title=str(official.get(year,{}).get(sp,{}).get("sp_text")
                          or activities["hook"]).strip()
                if year==2:
                    evidence=pages[2].get(sp)
                    if evidence is None:
                        raise ValueError("Year2 original book SP reference unavailable "+code)
                    printed=[evidence["printed_page"]]
                elif year==5:
                    evidence=pages[5].get(sp)
                    if evidence is None:
                        raise ValueError("Year5 original book SP reference unavailable "+code)
                    printed=evidence["printed_pages"]
                else:
                    printed=[]
            verified=official.get(year,{}).get(sp)
            if verified is not None and verified["sk"]!=sk:
                raise ValueError("Year4/5 exact official SK/SP mismatch "+sp)
            lessons[code]={
                "year":year,"pdp_code":code,"pdp_number":no,"sp":sp,"sk":sk,
                "unit":f"Unit {unit_number}: {unit_title}",
                "title":title,
                "official_sp_text":verified["sp_text"] if verified else "",
                "textbook_pages":list(printed),
                "academic_approval":False,"source_status":"DRAF_HOLD",
                **activities,
            }
    if (len(lessons)!=342
        or {year:sum(r["year"]==year for r in lessons.values())
             for year in EXPECTED}!=EXPECTED):
        raise ValueError("Sains T2–T6 342 source identities incomplete")
    return lessons


def preview_rows(year):
    year=_year(year)
    if year not in EXPECTED:
        raise ValueError("Review supports Sains Tahun 2–6 only")
    source=_catalog()
    output=[]
    for item in source.values():
        if item["year"]!=year:
            continue
        # No guessed "SP page": book labels are marked as cues, not approved.
        page_text=", ".join(map(str,item["textbook_pages"]))
        output.append({
            "year_label":f"Tahun {year}","subject":"Sains",
            "unit_code":"","unit_title":item["unit"],"theme":item["unit"],
            "pdp_sequence_code":item["pdp_code"],
            "source_sequence_no":item["pdp_number"],
            "pdp_title":item["title"],
            "sk_code":item["sk"],"sk_text":"",
            "sp_code":item["sp"],"sp_text":item["official_sp_text"],
            "textbook_ref":(
                f"Buku Teks T{year} m/s {page_text} (label SP semakan)"
                if page_text else ""),
            "activitybook_ref":"",
            "verification_status":SOURCE_STATE,
            "source_kind":"SCIENCE_ORIGINAL_AUTHORED_STAGING_REVIEW",
            "skill_metadata":"",
        })
    if (len(output)!=EXPECTED[year]
        or len({row["pdp_sequence_code"] for row in output})!=EXPECTED[year]):
        raise ValueError("Science native staging source missing PdP")
    return output


def _selected(state):
    if not isinstance(state,dict) or not _is_review_sains(
        state.get("year") or state.get("year_label"),state.get("subject")):
        return None
    year=_year(state.get("year") or state.get("year_label"))
    code=str(state.get("pdp_sequence_code") or "").strip()
    item=_catalog().get(code)
    if item is None or item["year"]!=year:
        raise ValueError("Sains staging selected PdP code not found")
    wanted=str(state.get("sp_code") or "").strip()
    selected=state.get("selected_sp_codes") or state.get("grouped_sp_codes") or []
    if isinstance(selected,str):
        selected=[selected]
    if (not isinstance(selected,(tuple,list)) or len(selected)!=1
        or selected[0]!=item["sp"] or wanted!=item["sp"]
        or str(state.get("sk_code") or "").strip()!=item["sk"]
        or str(state.get("unit_title") or state.get("unit") or "")!=item["unit"]):
        raise ValueError("Sains SP/SK/unit binding inconsistent with authored PdP")
    return item


def _review_text(item):
    year,sp=item["year"],item["sp"]
    body=(
        f"# Sains Tahun {year} · PdP {item['pdp_number']:03d} — SEMAKAN DALAMAN / DRAF HOLD\n"
        f"Kod PdP: {item['pdp_code']}\n"
        f"Unit: {item['unit']}\n"
        f"Tajuk/fokus: {item['title']}\n"
        f"SK: {item['sk']}\n"
        f"SP {sp}: {item['official_sp_text'] or 'Pernyataan penuh belum disahkan daripada sumber asal'}\n"
        f"Rujukan Buku Teks (label kod SP sahaja, bukan kelulusan aktiviti): {', '.join(map(str,item['textbook_pages'])) or 'halaman belum disahkan'}\n"
        f"Objektif/Kriteria kejayaan: {item['pbd']}\n"
        f"Set induksi: Guru menunjukkan {item['hook'].lower()}; murid berkongsi pemerhatian awal.\n"
        f"Aktiviti 1 — Penerokaan\n"
        f"1. Guru {item['teacher1']}.\n"
        f"2. Murid {item['pupil1']}.\n"
        f"Aktiviti 2 — Aplikasi\n"
        f"1. Guru {item['teacher2']}.\n"
        f"2. Murid {item['pupil2']}.\n"
        f"PBD individu: {item['pbd']}.\n"
        f"Penutup: Murid menyampaikan dapatan; guru merumus hubungan dengan SP {sp}.\n"
        f"BBM: {item['materials']}.\n"
        f"Keselamatan: {item['safety']}.\n"
        "Status: DRAF/HOLD — belum disahkan guru/panitia; hanya untuk staging."
    )
    if len(body)<500 or item["academic_approval"] is not False:
        raise ValueError("Sains reviewer has insufficient lesson text or invalid academic status")
    return body


def _review_rows(state,source):
    item=_selected(state)
    if item is None:
        return source
    if not isinstance(source,dict):
        raise ValueError("Telegram native Word/PDF rows unavailable")
    out=dict(source)
    official=item["official_sp_text"]
    out.update({
        "TAJUK":item["title"],
        "STANDARD KANDUNGAN":item["sk"],
        "STANDARD PEMBELAJARAN":(
            item["sp"]+(" — "+official if official else
                " — Pernyataan penuh DSKP belum disahkan")),
        "OBJEKTIF PEMBELAJARAN":item["pbd"],
        "KRITERIA KEJAYAAN":item["pbd"],
        "SET INDUKSI":"Guru menunjukkan "+item["hook"].lower()+
                       ". Murid mencatat satu pemerhatian.",
        "AKTIVITI UTAMA":(
            "Aktiviti 1 — Penerokaan\n"
            "1. Guru "+item["teacher1"]+".\n"
            "2. Murid "+item["pupil1"]+".\n\n"
            "Aktiviti 2 — Aplikasi\n"
            "1. Guru "+item["teacher2"]+".\n"
            "2. Murid "+item["pupil2"]+"."),
        "PENTAKSIRAN":"Bukti individu: "+item["pbd"]+".",
        "PENUTUP":"Murid menyatakan dapatan; guru merumus SP "+item["sp"]+".",
        "BAHAN BANTU MENGAJAR":item["materials"],
        "KESELAMATAN":item["safety"],
        "STATUS SEMAKAN":"DRAF/HOLD — belum lulus panitia; staging sahaja",
    })
    return out


def install(runtime):
    """Opt-in staging adapter. Does not touch DB, payments, quota or live sources."""
    if os.environ.get(FLAG)!="1":
        return False
    if (os.environ.get(CONTEXT)!="staging"
        or os.environ.get("RENDER_SERVICE_ID") in PRODUCTION_SERVICE_IDS
        or os.environ.get("CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW")=="1"):
        raise RuntimeError("342 reviewer may not be installed on production/alongside Year5 reviewer")
    if getattr(runtime,"CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE",False):
        return True
    needed=("_sm2542_rows","_local_rph_text","_rph_rows")
    if not all(callable(getattr(runtime,name,None)) for name in needed):
        raise ValueError("Telegram native RPH source hooks unavailable")
    _catalog()  # Verify all 342 sources BEFORE any mutation.
    original_menu=runtime._sm2542_rows
    original_text=runtime._local_rph_text
    original_rows=runtime._rph_rows

    def row_reader(year_label,subject):
        if _is_review_sains(year_label,subject):
            return preview_rows(year_label)
        return original_menu(year_label,subject)

    def content_reader(state,*args,**kwargs):
        item=_selected(state)
        if item is not None:
            return _review_text(item)
        return original_text(state,*args,**kwargs)

    def word_rows(state,*args,**kwargs):
        item=_selected(state)
        original=original_rows(state,*args,**kwargs)
        return _review_rows(state,original) if item is not None else original

    runtime._sm2542_rows=row_reader
    runtime._local_rph_text=content_reader
    runtime._rph_rows=word_rows
    runtime.CIKGULAJU_SAINS_342_INTERNAL_REVIEW_ACTIVE=True
    return True
