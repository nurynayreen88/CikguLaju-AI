"""Opt-in RBT Y4-6 Telegram-native draft reviewer.

Does not write to DB/users, bypass quota, or mark any RPH approved.
Disabled by default; expose only when CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED=1.
The exact RPH source is shared with the authenticated Web API, with the same
Telegram native row generator and class/date flow.
"""
from __future__ import annotations

from web.rph_source_criterion_reflection_20261124 import source_reflection

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from web.rbt_2027_staging_source import (
    RBTSourceUnavailable, internal_review, menu_pdp, menu_units, source_fingerprint,
)

ROOT = Path(__file__).resolve().parents[1]
FLAG = "CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED"
SUBJECT = "Reka Bentuk dan Teknologi"
YEARS = (4, 5, 6)
SELECTION = "_rbt_2027_selected_pdp"
STANDARD_DESCRIPTIONS = "rph_standalone/rbt/kssr_standard_descriptions.json"
WORD_OVERFLOW = {
    4: {1, 3, 4, 5, 6, 9, 13, 14, 16, 17, 18, 19, 20, 22, 23, 27, 30, 31},
    5: {1, 7, 10, 13, 14},
}
WORD_TIGHT_OVERFLOW = {(4, 3), (4, 14), (4, 23)}


def year_number(value):
    m = re.fullmatch(r"(?i)(?:Tahun\s*)?([4-6])", str(value or "").strip())
    return int(m[1]) if m else None


@lru_cache(maxsize=4)
def _standard_descriptions(root):
    return json.loads((Path(root) / STANDARD_DESCRIPTIONS).read_text(encoding="utf-8"))


def _lesson(year, pdp, *, root=ROOT):
    if type(year) is not int or year not in YEARS or type(pdp) is not int or not 1 <= pdp <= 32:
        return None
    try:
        row = internal_review(year, pdp, root=root)
        source_fingerprint(year, pdp, root=root)
        if (row["review"]["release_ready"] is not False
                or len(row["sp_codes"]) < 1 or not row["unit_label"].startswith("Unit ")):
            return None
        standards = _standard_descriptions(str(Path(root).resolve()))[str(year)]
        for kind, codes in (("sk", row["sk"]), ("sp", row["sp_codes"])):
            descriptions = [standards[kind][code] for code in codes]
            if any(not text.strip() for text in descriptions):
                return None
            row[f"{kind}_description"] = " · ".join(
                f"{code} {text}" for code, text in zip(codes, descriptions, strict=True)
            )
        return row
    except (RBTSourceUnavailable, ValueError, TypeError, KeyError, OSError, AttributeError):
        return None


def _selected(state, *, root=ROOT):
    if not isinstance(state, dict) or state.get("subject") != SUBJECT:
        return None
    y = year_number(state.get("year") or state.get("year_label"))
    sel = state.get(SELECTION)
    if not y or type(sel) is not dict or sel.get("year") != y:
        return None
    row = _lesson(y, sel.get("pdp"), root=root)
    if not row or str(state.get("lesson_no") or "") != str(row["pdp"]):
        return None
    if (str(state.get("sk_code") or "") not in row["sk"]
            or str(state.get("sp_code") or "") not in row["sp_codes"]):
        return None
    return row


def adapt_rows(state, previous, *, root=ROOT):
    """Add source-specific RBT fields only to a validated selected PdP."""
    row = _selected(state, root=root)
    if row is None or not isinstance(previous, dict):
        return previous
    l = row["langkah"]
    refs = row["rujukan_buku_teks"]
    pages = refs.get("calon_muka_surat_mengikut_sp") or []
    page_str = "; ".join(
        f'{x["sp"]}: hlm. {"–".join(map(str, x["muka_surat_bercetak_calon"]))}'
        for x in pages
    )
    if not page_str:
        page_str = ", ".join(map(str, refs.get("calon_muka_surat_teks_digital", [])))
    title = re.sub(r"^PdP\s+\d+\s*[:—–-]\s*", "", row["tajuk"], flags=re.I)
    out = dict(previous)
    out.update({
        "MATA PELAJARAN": SUBJECT,
        "TAHUN/TINGKATAN": f'Tahun {row["tahun"]}',
        "TAJUK": f'{row["unit_label"]} — {title} (DRAF UNTUK SEMAKAN)',
        "STANDARD KANDUNGAN": row["sk_description"],
        "STANDARD PEMBELAJARAN": row["sp_description"],
        "OBJEKTIF PEMBELAJARAN": row["objektif"],
        "KRITERIA KEJAYAAN": row["kriteria_kejayaan"],
        "PENGETAHUAN SEDIA ADA": f'Pengalaman murid berkaitan {row["unit_label"]}.',
        "BAHAN BANTU MENGAJAR": (row["bbm"] + ". Buku Teks RBT Tahun " +
                                  str(row["tahun"]) + ": " + page_str +
                                  " (cadangan halaman, perlu semak visual)."),
        "EMK / NILAI": "Kreativiti dan inovasi; kerjasama; keselamatan.",
        "KBAT / PAK21": "Penyelesaian masalah reka bentuk; menilai fungsi; komunikasi.",
        "SET INDUKSI": l["set_induksi"]["aktiviti"],
        "AKTIVITI UTAMA": (
            "Aktiviti 1\n" + l["aktiviti_1"]["aktiviti"] + "\n"
            "Aktiviti 2\n" + l["aktiviti_2"]["aktiviti"] + "\n"
            "PBD / Pengukuhan\n" + l["pengukuhan_penilaian"]["aktiviti"]
        ),
        "PENTAKSIRAN": row["pbd_evidens"],
        "PENUTUP": l["penutup"]["aktiviti"],
        "PEMULIHAN / PENGAYAAN": "Bimbing murid memurnikan hasil SP pada sesi ini.",
        "REFLEKSI": source_reflection(state, row["kriteria_kejayaan"], "___ / ___ murid mencapai objektif. Tindakan susulan: ________."),
    })
    return out


def install(ns, *, enabled=None, root=ROOT):
    """Reversible wrappers around the original Telegram callbacks and renderer.

    Inherits existing quota, payment checks, class picker and output generation.
    No installation if source incomplete or opt-in is absent.
    """
    if enabled is None:
        enabled = os.environ.get(FLAG) == "1"
    if not enabled:
        return False
    if ns.get("RBT_2027_DRAFT_USER_BRIDGE_ACTIVE"):
        return True
    required = ("callback", "send", "_rph_rows", "_lesson_to_class_v2439")
    if any(not callable(ns.get(key)) for key in required):
        return False
    subjects = ns.get("SUBJECTS_BY_GRADE")
    state = ns.get("state")
    if not isinstance(subjects, dict) or not isinstance(state, dict):
        return False
    for y in YEARS:
        if not isinstance(subjects.get(f"Tahun {y}"), list):
            return False
        try:
            units = menu_units(y, root=root)
            pdps = [p for u,_ in units for p,_ in menu_pdp(y,u,root=root)]
            if sorted(pdps) != list(range(1,33)):
                return False
            if any(_lesson(y,p,root=root) is None for p in range(1,33)):
                return False
        except RBTSourceUnavailable:
            return False

    previous_callback=ns["callback"]
    previous_rows=ns["_rph_rows"]
    send=ns["send"]
    for y in YEARS:
        opts=subjects[f"Tahun {y}"]
        if SUBJECT not in opts:
            opts.append(SUBJECT)

    def units_menu(cid):
        st=state.setdefault(cid,{})
        y=year_number(st.get("year"))
        if y not in YEARS:
            return send(cid,"Sila pilih Tahun 4, 5 atau 6.")
        try:
            units=menu_units(y,root=root)
        except RBTSourceUnavailable:
            return send(cid,"Bahan RBT belum tersedia.")
        keyboard=[[{"text":label[:62],"callback_data":f"rbt27u|{u:02d}"}]
                  for u,label in units]
        keyboard.append([{"text":"📅 RPT RBT 2027 (PDF • DRAF)",
                          "callback_data":f"rbt27rpt|{y}"}])
        keyboard.append([{"text":"⬅️ Tukar subjek","callback_data":"back_subjects"}])
        return send(cid,f"🛠 <b>RBT Tahun {y} (2027)</b>\nPilih Unit dan PdP. Bahan masih DRAF untuk semakan.",keyboard)

    def callback(cid, data):
        val=str(data or "")
        st=state.setdefault(cid,{})
        y=year_number(st.get("year"))
        if val=="sub_"+SUBJECT and y in YEARS:
            st["subject"]=SUBJECT
            st.pop(SELECTION,None)
            st.pop("_rbt_2027_unit",None)
            return units_menu(cid)
        if val.startswith(("rbt27u|","rbt27p|")):
            if y not in YEARS or st.get("subject")!=SUBJECT:
                return send(cid,"Sesi RBT tamat. Pilih subjek semula.")
            m=re.fullmatch(r"rbt27u\|(\d{2})",val)
            if m:
                u=int(m[1])
                try:
                    rows=menu_pdp(y,u,root=root)
                    unit_label=dict(menu_units(y,root=root)).get(u)
                except RBTSourceUnavailable:
                    return units_menu(cid)
                if not rows or not unit_label:
                    return units_menu(cid)
                st["_rbt_2027_unit"]=u
                st.pop(SELECTION,None)
                keyboard=[[{"text":label[:62],"callback_data":f"rbt27p|{pdp:03d}"}]
                          for pdp,label in rows]
                keyboard.append([{"text":"⬅️ Unit lain","callback_data":"sub_"+SUBJECT}])
                return send(cid,f"📘 {unit_label}\nPilih PdP:",keyboard)
            m=re.fullmatch(r"rbt27p\|(\d{3})",val)
            if not m:
                return units_menu(cid)
            pdp=int(m[1])
            row=_lesson(y,pdp,root=root)
            if not row or row["unit"]!=st.get("_rbt_2027_unit"):
                return units_menu(cid)
            for key in ("selected_sk","sk_code","selected_sp","sp_code",
                        "selected_sk_codes","selected_sp_codes","grouped_sk_codes",
                        "grouped_sp_codes","topic","unit","lesson_no","pdp_no"):
                st.pop(key,None)
            st.update({
                "task":"quick_material","quick_material_flow":True,
                "assessment_mode":"formative","rph_mode":"fast_rpt",
                "lesson_no":str(pdp),"pdp_no":pdp,"lesson":str(pdp),
                "topic":row["tajuk"],"unit":row["unit_label"],
                "unit_title":row["unit_label"].split(": ",1)[-1],
                "sk_code":row["sk"][0],"selected_sk":row["sk"][0],
                "selected_sk_codes":list(row["sk"]),
                "grouped_sk_codes":list(row["sk"]),
                "sp_code":row["sp_codes"][0],"selected_sp":row["sp_codes"][0],
                "selected_sp_codes":list(row["sp_codes"]),
                "grouped_sp_codes":list(row["sp_codes"]),
                "quick_content_v2391":row["tajuk"],
                SELECTION:{"year":y,"pdp":pdp},
            })
            return ns["_lesson_to_class_v2439"](cid)
        return previous_callback(cid,data)

    def rows(st,*args,**kwargs):
        return adapt_rows(st,previous_rows(st,*args,**kwargs),root=root)

    ns["callback"]=callback
    ns["_rph_rows"]=rows
    previous_word = ns.get("create_word_file")
    if callable(previous_word):
        def word(state_value, *args, **kwargs):
            path = previous_word(state_value, *args, **kwargs)
            if isinstance(state_value, dict) and state_value.get("task") == "rph":
                row = _selected(state_value, root=root)
                if row and row["pdp"] in WORD_OVERFLOW.get(row["tahun"], ()):
                    from web.english_y6_word_a4_runtime import compact_word_file

                    key = (row["tahun"], row["pdp"])
                    compact_word_file(path, point_size=8.0 if key in WORD_TIGHT_OVERFLOW else 8.5)
            return path

        ns["create_word_file"] = word
    ns["RBT_2027_DRAFT_USER_BRIDGE_ACTIVE"]=True
    return True
