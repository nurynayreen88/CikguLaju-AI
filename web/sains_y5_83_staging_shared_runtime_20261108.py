"""Staging-only shared Science Y5 PdP source for Telegram and native Web.

The author's 83 DRAF/HOLD lessons are available for *internal review*
using the same native Telegram _sm2542_rows / _local_rph_text / _rph_rows
methods that Web calls. Never auto-enabled, never writes to a DB, never
changes payments, user accounts, or production quotas. Fail closed when
selection cannot be proven to be an exact 1:1 SP and PdP match.
"""
from __future__ import annotations

from functools import lru_cache
import os
import re

STAGING_FLAG = "CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW"
STAGING_CONTEXT = "CIKGULAJU_CURRICULUM_DEPLOYMENT"
ALLOWED_CONTEXT = "staging"
PRODUCTION_RENDER_SERVICES = {
    "srv-dbm5go8u01pc738f40cg",  # dedicated public Web
    "srv-dah3b8lbedkc738ugqt0",  # Telegram/primary curriculum service
}


def _is_y5_sains(year, subject):
    subject_name = re.sub(r"\s+", "", str(subject or "").casefold())
    year_name = re.sub(r"\s+", "", str(year or "").casefold())
    return subject_name in {"sains", "science"} and year_name in {"5", "tahun5"}


@lru_cache(maxsize=1)
def _roster():
    from tools.render_sains_y5_83_rph_draf_20261107 import get_y5_records
    from tools.sains_y5_kssr2017_official_sp_statements_20261107 import checked_statements
    source=get_y5_records()
    official=checked_statements()
    if len(source)!=83 or len(official)!=83:
        raise ValueError("Year5 staging canonical roster incomplete")
    by_code={}
    by_sp={}
    units=[]
    for number,lesson in enumerate(source,1):
        sp=lesson["sp"]
        code=lesson["pdp_code"]
        if (int(lesson["pdp_number"])!=number
            or code!=f"SCI-Y5-PDP-{number:03d}"
            or sp in by_sp or code in by_code
            or sp not in official
            or lesson["sk"]!=official[sp]["sk"]
            or lesson["sp_full_text"]!=official[sp]["sp_text"]
            or lesson["status"]!="DRAF_HOLD"):
            raise ValueError("Year5 staging content and PdP identity mismatch")
        unit=str(lesson["unit"]).strip()
        if not re.fullmatch(r"Unit [2-9][0-9]?: .+",unit):
            raise ValueError("Noncanonical Sains Y5 unit: "+code)
        if unit not in units:
            units.append(unit)
        by_code[code]=lesson
        by_sp[sp]=lesson
    if set(by_sp)!=set(official):
        raise ValueError("Year5 official DSKP SP coverage incomplete")
    return tuple(source),by_code,by_sp,tuple(units)


def preview_rows():
    source,by_code,by_sp,units=_roster()
    output=[]
    for lesson in source:
        # A single unit label prevents "Unit 2" from being shown twice.
        # Blank unit_code is supported by native unit token/catalog logic.
        title=str(lesson["unit"])
        output.append({
            "year_label":"Tahun 5",
            "subject":"Sains",
            "unit_code":"",
            "unit_title":title,
            "theme":title,
            "pdp_sequence_code":lesson["pdp_code"],
            "source_sequence_no":int(lesson["pdp_number"]),
            "pdp_title":lesson["tajuk"],
            "sk_code":lesson["sk"],
            "sk_text":lesson["sk_title"],
            "sp_code":lesson["sp"],
            "sp_text":lesson["sp_full_text"],
            "textbook_ref":"Buku Teks Sains T5 m/s "+",".join(
                map(str,lesson["textbook_pages"])),
            "activitybook_ref":"",
            "verification_status":"STAGING_DRAF_HOLD_NOT_FOR_PUBLICATION",
            "skill_metadata":lesson["kps"],
            "source_kind":"KSSR2017_83_FULL_SP_SOURCE_REVIEW",
        })
    if len(output)!=83 or len(set(r["pdp_sequence_code"] for r in output))!=83:
        raise ValueError("Invalid Science 5 preview PdP menu")
    return output


def _resolve_lesson(state):
    if not isinstance(state,dict) or not _is_y5_sains(
        state.get("year") or state.get("year_label"),state.get("subject")):
        return None
    _,by_code,by_sp,_=_roster()
    code=str(state.get("pdp_sequence_code") or "").strip()
    selected=state.get("selected_sp_codes") or state.get("grouped_sp_codes") or []
    if isinstance(selected,str):
        selected=[selected]
    if not isinstance(selected,(list,tuple)) or len(set(map(str,selected)))>1:
        raise ValueError("Multi-SP Year5 selection cannot map to one authored PdP")
    sp=str(state.get("sp_code") or (selected[0] if selected else "")).strip()
    # Never map guessed legacy row numbers or return unrelated old material.
    lesson=by_code.get(code) if code else by_sp.get(sp)
    if lesson is None or (sp and sp!=lesson["sp"]):
        raise ValueError("Unrecognized Year5 source PdP/SP")
    if selected and any(str(x)!=lesson["sp"] for x in selected):
        raise ValueError("Selected Year5 SP differs from authored source")
    if not sp and not code:
        raise ValueError("Year5 selection lacks verified PdP/SP identity")
    return lesson


def _adapt_rows(state, source_rows):
    lesson=_resolve_lesson(state)
    if lesson is None:
        return source_rows
    if not isinstance(source_rows,dict):
        raise ValueError("Native RPH word/pdf fields unavailable")
    out=dict(source_rows)
    out.update({
        "TAJUK":lesson["tajuk"],
        "STANDARD KANDUNGAN":lesson["sk"]+" — "+lesson["sk_title"],
        "STANDARD PEMBELAJARAN":lesson["sp"]+" — "+lesson["sp_full_text"],
        "OBJEKTIF PEMBELAJARAN":lesson["pbd"],
        "KRITERIA KEJAYAAN":lesson["pbd"],
        "BAHAN BANTU MENGAJAR":lesson["materials"],
        "PENTAKSIRAN":lesson["pbd"],
        "SET INDUKSI":"Guru menunjukkan "+lesson["hook"].lower()+
                       ". Murid berkongsi idea dan ramalan.",
        "AKTIVITI UTAMA":(
            "Aktiviti 1 — Penerokaan\n"
            "1. Guru "+lesson["teacher1"]+".\n"
            "2. Murid "+lesson["pupil1"]+".\n\n"
            "Aktiviti 2 — Aplikasi\n"
            "1. Guru "+lesson["teacher2"]+".\n"
            "2. Murid "+lesson["pupil2"]+".\n\n"
            "Pengukuhan/PBD — "+lesson["pbd"]+"."
        ),
        "PENUTUP":"Murid menyatakan satu dapatan. Guru merumus "+lesson["sp"]+".",
        "RUJUKAN BUKU TEKS":"Sains Tahun 5 m/s "+", ".join(
            map(str,lesson["textbook_pages"])),
        "KESELAMATAN":lesson["safety"],
        "STATUS SEMAKAN":"DRAF/HOLD — sumber SP disahkan; PBD/pedagogi belum diluluskan.",
    })
    return out


def install(runtime):
    """Install only on an explicitly isolated staging service.

    If validation fails nothing is replaced. Does not import or touch
    runtime's DB, payment service or registration routines.
    """
    if os.getenv(STAGING_FLAG)!="1":
        return False
    if (os.getenv(STAGING_CONTEXT)!=ALLOWED_CONTEXT
        or os.getenv("RENDER_SERVICE_ID") in PRODUCTION_RENDER_SERVICES):
        raise RuntimeError("Sains Y5 review bridge forbidden outside staging")
    if getattr(runtime,"CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW_ACTIVE",False):
        return True
    required=("_sm2542_rows","_local_rph_text","_rph_rows")
    if not all(callable(getattr(runtime,name,None)) for name in required):
        raise ValueError("Telegram native RPH hooks unavailable for staging")
    _roster()  # Fail before touching runtime when source or DB has changed.
    previous_reader=runtime._sm2542_rows
    previous_text=runtime._local_rph_text
    previous_rows=runtime._rph_rows

    def rows_reader(year_label,subject):
        if _is_y5_sains(year_label,subject):
            return preview_rows()
        return previous_reader(year_label,subject)

    def lesson_text(state,*args,**kwargs):
        lesson=_resolve_lesson(state)
        if lesson is None:
            return previous_text(state,*args,**kwargs)
        from tools.render_sains_y5_83_rph_draf_20261107 import markdown
        return markdown(lesson)

    def doc_rows(state,*args,**kwargs):
        lesson=_resolve_lesson(state)
        previous=previous_rows(state,*args,**kwargs)
        if lesson is None:
            return previous
        return _adapt_rows(state,previous)

    runtime._sm2542_rows=rows_reader
    runtime._local_rph_text=lesson_text
    runtime._rph_rows=doc_rows
    runtime.CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW_ACTIVE=True
    return True
