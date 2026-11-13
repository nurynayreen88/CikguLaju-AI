"""Private RBT 2027 Web -> active Telegram native RPH API.

Only a narrow, explicit DRAF preview opt-in; source is the same one used by
Telegram callback bridge. NEVER use Web's own RPH copy or bypass entitlements.
The public Web route is responsible for Telegram Login and free/paid gates.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
import uuid
from datetime import date
from pathlib import Path
from zipfile import ZipFile

from flask import Blueprint, Response, jsonify, request

from web.native_rph_telegram_api import MIMES, compact_web_word_notes
from web.rph_teacher_reflection import clean_reflection
from web.rbt_2027_staging_source import RBTSourceUnavailable, menu_pdp, menu_units, source_fingerprint
from web.rbt_2027_user_runtime import (
    SUBJECT, SELECTION, _lesson, adapt_rows,
)
from web.telegram_verified_rpt_rph_bridge import _authorization, _teacher_metadata

MAX_FILE=15*1024*1024
FLAG="CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED"


def resolve(year,unit=None,pdp=None):
    if type(year) is not int or year not in (4,5,6):
        raise ValueError("RBT year invalid")
    if unit is None:
        return menu_units(year)
    if type(unit) is not str or not re.fullmatch(r"u0[1-6]",unit):
        raise ValueError("Invalid RBT Unit")
    num=int(unit[1:])
    units=dict(menu_units(year))
    if num not in units:
        raise ValueError("Unit not found")
    rows=menu_pdp(year,num)
    if pdp is None:
        return rows
    if type(pdp) is not str or not re.fullmatch(r"0(?:0[1-9]|[12][0-9]|3[0-2])",pdp):
        raise ValueError("Invalid RBT PdP")
    n=int(pdp)
    row=_lesson(year,n)
    if row is None or row["unit"]!=num:
        raise ValueError("PdP not in selected unit")
    return row


def _state(year,unit,lesson,teacher):
    row=resolve(year,unit,lesson)
    cls,dt,tm,pupils,day=_teacher_metadata(teacher,"RBT")
    n=row["pdp"]
    return {
        "task":"rph", "quick_material_flow":True, "rph_mode":"fast_rpt",
        "assessment_mode":"formative",
        "year":f"Tahun {year}", "year_label":f"Tahun {year}",
        "subject":SUBJECT,
        "unit":row["unit_label"], "unit_title":row["unit_label"].split(": ",1)[-1],
        "topic":row["tajuk"],"lesson_no":str(n),"pdp_no":n,"lesson":str(n),
        "sk_code":row["sk"][0],"sp_code":row["sp_codes"][0],
        "selected_sk":row["sk"][0],"selected_sp":row["sp_codes"][0],
        "selected_sk_codes":list(row["sk"]),"grouped_sk_codes":list(row["sk"]),
        "selected_sp_codes":list(row["sp_codes"]),"grouped_sp_codes":list(row["sp_codes"]),
        "rph_class":cls,"rph_date":date.fromisoformat(dt).strftime("%d/%m/%Y") if dt else "",
        "rph_day":day,"rph_time":tm,"rph_students":pupils,
        "rph_teacher_reflection": clean_reflection(teacher.get("reflection", "")),
        SELECTION:{"year":year,"pdp":n},
    }


def create_rbt_2027_native_blueprint(runtime):
    if (not callable(getattr(runtime,"create_word_file",None))
            or not callable(getattr(runtime,"create_pdf_file",None))):
        raise TypeError("Telegram native RPH generators missing")
    bp=Blueprint("telegram_rbt_2027_native",__name__)

    @bp.after_request
    def headers(resp):
        resp.headers["Cache-Control"]="no-store, private"
        resp.headers["Vary"]="Authorization"
        resp.headers["X-Content-Type-Options"]="nosniff"
        return resp

    @bp.before_request
    def gate():
        if not _authorization():
            return jsonify({"error":"Unauthorized RBT source"}),401
        if (os.environ.get(FLAG)!="1"
                or not getattr(runtime,"RBT_2027_DRAFT_USER_BRIDGE_ACTIVE",False)):
            return jsonify({"error":"RBT has not been approved for release"}),503

    def year_query(required):
        if set(request.args)!=required or any(len(request.args.getlist(x))!=1 for x in request.args):
            raise ValueError("Unexpected query")
        y=request.args["year"]
        if not re.fullmatch(r"[4-6]",y):
            raise ValueError("Invalid RBT year")
        return int(y)

    @bp.get("/internal/rph/v1/rbt/units")
    def units():
        try:
            year=year_query({"year"})
            source=resolve(year)
            values=[{"value":f"u{u:02d}","label":label} for u,label in source]
        except (ValueError,RBTSourceUnavailable):
            return jsonify({"error":"RBT Units unavailable"}),503
        return jsonify({"source":"telegram-rbt-2027-v1","status":"DRAF","items":values})

    @bp.get("/internal/rph/v1/rbt/lessons")
    def lessons():
        try:
            year=year_query({"year","unit"})
            unit=request.args["unit"]
            values=[]
            for n,label in resolve(year,unit):
                row=resolve(year,unit,f"{n:03d}")
                ref=row["rujukan_buku_teks"].get("calon_muka_surat_teks_digital") or []
                values.append({
                    "value":f"{n:03d}", "label":label,
                    "textbook_ref":("Buku Teks calon m/s: "+", ".join(map(str,ref))
                                    +" (belum sah visual)") if ref else "",
                    "status":"DRAF"
                })
        except (ValueError,RBTSourceUnavailable):
            return jsonify({"error":"RBT PdP unavailable"}),503
        return jsonify({"source":"telegram-rbt-2027-v1","status":"DRAF","items":values})

    @bp.get("/internal/rph/v1/rbt/availability")
    def availability():
        try:
            year=year_query({"year","unit","lesson"})
            resolve(year,request.args["unit"],request.args["lesson"])
        except (ValueError,RBTSourceUnavailable):
            return jsonify({"available":False}),404
        return jsonify({"available":True,"status":"DRAF","generator":"telegram-native"})

    @bp.post("/internal/rph/v1/rbt/render")
    def render():
        if not request.is_json or request.content_length is None or request.content_length>7000:
            return jsonify({"error":"Invalid RBT render request"}),400
        payload=request.get_json(silent=True)
        if not isinstance(payload,dict) or set(payload)!={"selection","teacher","format"}:
            return jsonify({"error":"Invalid source-backed request"}),400
        selection=payload["selection"]; teacher=payload["teacher"];fmt=payload["format"]
        if not isinstance(selection,dict) or set(selection)!={"year","unit","lesson"} or fmt not in MIMES:
            return jsonify({"error":"Invalid RBT selection"}),400
        try:
            y=selection["year"];u=selection["unit"];lesson=selection["lesson"]
            state=_state(y,u,lesson,teacher)
            row=resolve(y,u,lesson)
            digest=source_fingerprint(y,row["pdp"])
            if len(digest)!=64:
                raise ValueError("RBT source identity invalid")
            if not callable(getattr(runtime,"_rph_rows",None)):
                raise ValueError("Telegram RPH row generator missing")
            steps=row["langkah"]
            text=("RPH RBT "+row["id"]+"\n"+row["tajuk"]+"\n"+
                  "\n".join(steps[x]["aktiviti"] for x in
                    ("set_induksi","aktiviti_1","aktiviti_2","pengukuhan_penilaian","penutup")))
            expected=adapt_rows(state,{})
            actual=runtime._rph_rows(state,text)
            for key in ("AKTIVITI UTAMA","STANDARD PEMBELAJARAN","OBJEKTIF PEMBELAJARAN"):
                if expected.get(key)!=actual.get(key):
                    raise ValueError("Telegram RPH output is not RBT source-matched")
            if "DRAF" not in actual.get("TAJUK",""):
                raise ValueError("RBT draft label not preserved")
        except (ValueError,RBTSourceUnavailable,LookupError,TypeError,KeyError):
            return jsonify({"error":"RBT selection/source not available"}),404
        unique="rbt"+uuid.uuid4().hex
        output=None
        try:
            output=(runtime.create_word_file(state,text,unique) if fmt=="word"
                    else runtime.create_pdf_file(state,text,unique))
            p=Path(output).resolve(strict=True)
            if (p.parent!=Path(tempfile.gettempdir()).resolve() or
                    not p.name.startswith(unique+"_") or
                    not 1000<=p.stat().st_size<=MAX_FILE):
                raise ValueError("Invalid Telegram native render path")
            data=p.read_bytes()
            if fmt=="word":
                data=compact_web_word_notes(data)
                if not data.startswith(b"PK\x03\x04"):
                    raise ValueError("Invalid DOCX")
                with ZipFile(io.BytesIO(data)) as archive:
                    if archive.testzip() or "word/document.xml" not in archive.namelist():
                        raise ValueError("Invalid Word")
            elif not data.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF")
            resp=Response(data,mimetype=MIMES[fmt])
            ext="docx" if fmt=="word" else "pdf"
            resp.headers["Content-Disposition"]=(
                f'attachment; filename="CikguLaju_RPH_RBT_{y}_PdP_{row["pdp"]:03d}_DRAF.{ext}"')
            return resp
        except Exception as exc:
            print("RBT Telegram-native render failed:",type(exc).__name__,flush=True)
            return jsonify({"error":"Native RBT renderer unavailable"}),503
        finally:
            if isinstance(output,(str,os.PathLike)):
                try:
                    p=Path(output).resolve()
                    if p.parent==Path(tempfile.gettempdir()).resolve() and p.name.startswith(unique+"_"):
                        p.unlink(missing_ok=True)
                except (OSError,ValueError):
                    pass
    return bp
