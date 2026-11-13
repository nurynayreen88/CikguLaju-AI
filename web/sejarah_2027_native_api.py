"""Authenticated shared Telegram source for Sejarah 2027 Web navigation and RPH.

Same 108 draft candidate RPH as Telegram's user menu, same native document
generator and existing quota/license checks on Web. Never changes DB or approvals.
"""
from __future__ import annotations

import io
import os
from pathlib import Path
import re
import tempfile
import uuid
from datetime import date
from zipfile import ZipFile

from flask import Blueprint, Response, jsonify, request

from web.native_rph_telegram_api import MIMES, compact_web_word_notes
from web.rph_teacher_reflection import clean_reflection
from web.sejarah_2027_user_runtime import (
    _catalog, _lesson, adapt_rows, SELECTION,
)
from web.sejarah_2027_word_compact import compact_sejarah_native_word
from web.telegram_verified_rpt_rph_bridge import _authorization, _teacher_metadata

MAX_FILE = 15 * 1024 * 1024


def _resolve(year, unit=None, pdp=None):
    if type(year) is not int or year not in (4, 5, 6):
        raise ValueError("Unsupported Sejarah year")
    if unit is not None and not re.fullmatch(r"u(?:0[1-9]|1[0-2])", unit):
        raise ValueError("Invalid Sejarah unit")
    number = int(unit[1:]) if unit is not None else None
    if pdp is not None and (not isinstance(pdp, str)
                            or not re.fullmatch(r"0(?:0[1-9]|[12][0-9]|3[0-6])", pdp)):
        raise ValueError("Invalid Sejarah PdP")
    entries = _catalog(year, str(Path(__file__).resolve().parents[1]))
    if len(entries) != 36:
        raise LookupError("Sejarah source incomplete")
    if number is None:
        return entries
    chosen = tuple(row for row in entries if row["unit"] == number)
    if not chosen:
        raise LookupError("Sejarah unit not found")
    if pdp is None:
        return chosen
    result = [row for row in chosen if row["pdp"] == int(pdp)]
    if len(result) != 1:
        raise LookupError("PdP not mapped to chosen unit")
    return result[0]


def _state(year, unit, pdp, teacher):
    row = _resolve(year, unit, pdp)
    cls, dt, tm, pupils, day = _teacher_metadata(teacher, "SEJARAH")
    r = row["rph"]
    return {
        "task": "rph", "quick_material_flow": True, "rph_mode": "fast_rpt",
        "assessment_mode": "formative", "year": f"Tahun {year}",
        "year_label": f"Tahun {year}", "subject": "Sejarah",
        "unit": f"Unit {row['unit']}: {row['unit_title']}",
        "unit_title": row["unit_title"], "topic": r["title"],
        "lesson_no": str(row["pdp"]), "pdp_no": row["pdp"],
        "lesson": str(row["pdp"]), "sk_code": r["sk"],
        "sp_code": r["sp_codes"][0], "selected_sk": r["sk"],
        "selected_sp": r["sp_codes"][0],
        "selected_sk_codes": [r["sk"]],
        "grouped_sk_codes": [r["sk"]],
        "selected_sp_codes": list(r["sp_codes"]),
        "grouped_sp_codes": list(r["sp_codes"]),
        "rph_class": cls, "rph_date": date.fromisoformat(dt).strftime("%d/%m/%Y") if dt else "",
        "rph_day": day, "rph_time": tm, "rph_students": pupils,
        "rph_teacher_reflection": clean_reflection(teacher.get("reflection", "")),
        SELECTION: {"year": year, "pdp": row["pdp"]},
    }


def create_sejarah_2027_native_blueprint(runtime):
    if not callable(getattr(runtime, "create_word_file", None)) or not callable(getattr(runtime, "create_pdf_file", None)):
        raise TypeError("Telegram native Word/PDF renderer unavailable")
    bp = Blueprint("telegram_sejarah_2027_native", __name__)

    @bp.after_request
    def private_headers(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Vary"] = "Authorization"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @bp.before_request
    def authorized():
        if not _authorization():
            return jsonify({"error": "Unauthorized Sejarah source"}), 401
        if not getattr(runtime, "SEJARAH_2027_USER_BRIDGE_ACTIVE", False):
            return jsonify({"error": "Sejarah source is not active"}), 503

    def _query(keys):
        if set(request.args) != keys or any(len(request.args.getlist(k)) != 1 for k in request.args):
            raise ValueError("Unexpected query keys")
        y = request.args["year"]
        if not re.fullmatch(r"[4-6]", y):
            raise ValueError("Invalid year")
        return int(y)

    @bp.get("/internal/rph/v1/sejarah/units")
    def units():
        try:
            y = _query({"year"})
            entries = _resolve(y)
            pairs = dict.fromkeys((r["unit"], r["unit_title"]) for r in entries)
            items = [{"value": f"u{number:02d}", "label": f"Unit {number}: {title}"}
                     for number, title in pairs]
        except (ValueError, LookupError):
            return jsonify({"error": "Sejarah units unavailable"}), 503
        return jsonify({"source": "telegram-sejarah-2027-v1", "items": items})

    @bp.get("/internal/rph/v1/sejarah/lessons")
    def lessons():
        try:
            y = _query({"year", "unit"})
            rows = _resolve(y, request.args["unit"])
            items = [{
                "value": f"{r['pdp']:03d}",
                "label": f"PdP {r['pdp']:03d} — {r['rph']['title']}",
                "textbook_ref": "Buku Teks m/s " +
                    r["rph"]["textbook_reference"]["checked_focus_pages"]["printed_page_range"],
            } for r in rows]
        except (ValueError, LookupError):
            return jsonify({"error": "Sejarah PdP unavailable"}), 503
        return jsonify({"source": "telegram-sejarah-2027-v1", "items": items})

    @bp.get("/internal/rph/v1/sejarah/availability")
    def availability():
        try:
            y = _query({"year", "unit", "lesson"})
            _resolve(y, request.args["unit"], request.args["lesson"])
        except (ValueError, LookupError):
            return jsonify({"available": False}), 404
        return jsonify({"available": True, "generator": "telegram-native"})

    @bp.post("/internal/rph/v1/sejarah/render")
    def render():
        if not request.is_json or request.content_length is None or request.content_length > 7000:
            return jsonify({"error": "Invalid source request"}), 400
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or set(payload) != {"selection", "teacher", "format"}:
            return jsonify({"error": "Invalid request"}), 400
        selection, teacher, fmt = payload["selection"], payload["teacher"], payload["format"]
        if (not isinstance(selection, dict) or set(selection) != {"year", "unit", "lesson"}
                or fmt not in MIMES):
            return jsonify({"error": "Invalid Sejarah selection"}), 400
        try:
            state = _state(selection["year"], selection["unit"], selection["lesson"], teacher)
            row = _lesson(selection["year"], int(selection["lesson"]))
            if row is None:
                raise ValueError("Missing PdP")
            if not callable(getattr(runtime, "_rph_rows", None)):
                raise ValueError("Native RPH adapter missing")
            text = "RPH SEJARAH " + row["id"] + "\n" + row["rph"]["title"] + "\n" + "\n".join(
                row["rph"][key]["activity"] for key in (
                    "set_induksi", "aktiviti_1", "aktiviti_2", "pengukuhan_pbd", "penutup"))
            if len(text) < 400:
                raise ValueError("Empty RPH source")
            parsed = runtime._rph_rows(state, text)
            check = adapt_rows(state, {})
            if (parsed.get("AKTIVITI UTAMA") != check.get("AKTIVITI UTAMA")
                    or parsed.get("STANDARD PEMBELAJARAN") != check.get("STANDARD PEMBELAJARAN")
                    or "DRAF" not in parsed.get("TAJUK", "")):
                raise ValueError("Telegram native RPH lost exact Sejarah source")
        except (ValueError, LookupError, TypeError, KeyError):
            return jsonify({"error": "Sejarah source selection unavailable"}), 404
        unique = "web" + uuid.uuid4().hex
        output = None
        try:
            output = (runtime.create_word_file(state, text, unique) if fmt == "word"
                      else runtime.create_pdf_file(state, text, unique))
            path = Path(output).resolve(strict=True)
            if (path.parent != Path(tempfile.gettempdir()).resolve()
                    or not path.name.startswith(unique+"_")
                    or not 1000 <= path.stat().st_size <= MAX_FILE):
                raise ValueError("Invalid renderer output")
            doc = path.read_bytes()
            if fmt == "word":
                doc = compact_sejarah_native_word(compact_web_word_notes(doc))
                if not doc.startswith(b"PK\x03\x04"):
                    raise ValueError("Invalid Word")
                with ZipFile(io.BytesIO(doc)) as archive:
                    if archive.testzip() or "word/document.xml" not in archive.namelist():
                        raise ValueError("Word package invalid")
            elif not doc.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF")
            response = Response(doc, mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = (
                'attachment; filename="CikguLaju_RPH_Sejarah_2027.' +
                ("docx" if fmt == "word" else "pdf") + '"')
            return response
        except Exception as exc:
            print("Sejarah native source render failed:", type(exc).__name__, flush=True)
            return jsonify({"error": "Telegram Sejarah rendering unavailable"}), 503
        finally:
            if isinstance(output, (str, os.PathLike)):
                try:
                    target = Path(output).resolve()
                    if (target.parent == Path(tempfile.gettempdir()).resolve()
                            and target.name.startswith(unique+"_")):
                        target.unlink(missing_ok=True)
                except (OSError, ValueError):
                    pass

    return bp
