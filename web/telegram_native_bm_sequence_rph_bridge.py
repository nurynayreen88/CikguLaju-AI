"""Private Telegram-native BM RPH bridge using the SAME verified_pdp_sequence
as the live Telegram BM Tema -> Unit -> PdP flow.

Read-only master DB. The Web sends a signed opaque selection token and teacher
metadata; Telegram resolves the real grouped SK/SP rows, composes its ordinary
RPH, and generates Word/PDF. Never reinterpret this as a rpt_entries ID.
"""
import hmac
import io
import os
import re
import tempfile
import uuid
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from flask import Blueprint, Response, jsonify, request

from web_v1_dropdown_catalog import (
    _bm_verified_structured_rows, bm_sequence_token,
)
from web.native_rph_telegram_api import MIMES, compact_web_word_notes
from web.rph_teacher_reflection import clean_reflection
from web.telegram_verified_rpt_rph_bridge import (
    _authorization, _teacher_metadata, SourceUnavailable,
)

MAX_BODY = 7000
MAX_FILE = 15 * 1024 * 1024
TOKEN = re.compile(r"b[a-f0-9]{24}")



def _correct_one_verified_bm_mapping(path, year, key, sk, sp):
    """Correct a known v26.00 BM T2 SK mismatch at the Web read boundary.

    The source sequence for 'Majlis Pengikat Kemesraan' labels SP 2.2.1 as
    SK 2.1. The same v26.00 curriculum_standards table has verified SK 2.2
    with complete SP wording, matching DSKP BM SK Tahun 2 (2017), p.31.
    Only this exact selection is eligible; never mutate the SQLite master.
    """
    if not (
        year == 2 and key[2] == "Hidup Berjiran"
        and key[3] == "Majlis Pengikat Kemesraan"
        and sk == "2.1" and sp == "2.2.1"
    ):
        return sk, None
    import sqlite3
    try:
        with sqlite3.connect(
            Path(path).resolve().as_uri() + "?mode=ro", uri=True
        ) as conn:
            conn.execute("PRAGMA query_only=ON")
            values = conn.execute(
                """SELECT DISTINCT sk_code, sk_text, sp_text
                   FROM curriculum_standards
                   WHERE year_label='Tahun 2' AND subject='Bahasa Melayu'
                     AND sp_code='2.2.1' AND verified=1"""
            ).fetchall()
    except (sqlite3.Error, OSError) as exc:
        raise SourceUnavailable("BM T2 SP 2.2.1 mapping proof unavailable") from exc
    if (len(values) != 1 or str(values[0][0] or "").strip() != "2.2"
            or not str(values[0][2] or "").strip()):
        raise SourceUnavailable("BM T2 SP 2.2.1 SK mapping ambiguous")
    return "2.2", {
        "sk_text": str(values[0][1] or "").strip(),
        "sp_text": str(values[0][2]).strip(),
    }



def _select(runtime, year, unit, token):
    if (type(year) is not int or year not in range(1, 7)
            or not isinstance(unit, str) or not 0 < len(unit.strip()) <= 300
            or not isinstance(token, str) or not TOKEN.fullmatch(token)):
        raise ValueError("Invalid native BM selection")
    if not getattr(runtime, "CIKGULAJU_DB_V2600_ACTIVE", False):
        raise SourceUnavailable("Active Telegram master database unavailable")
    path = getattr(runtime, "DB_PATH", None)
    if not isinstance(path, (str, os.PathLike)) or not Path(path).is_file():
        raise SourceUnavailable("Master database unavailable")
    try:
        rows = _bm_verified_structured_rows(path, year)
    except (OSError, ValueError, Exception) as exc:
        raise SourceUnavailable("Verified BM sequence unavailable") from exc
    groups = {}
    for row in rows:
        key = (row["theme"], row["unit_code"],
               row["unit_title"], row["topic"])
        groups.setdefault(key, []).append(row)
    matched = [(key, members) for key, members in groups.items()
               if key[2] == unit.strip()
               and bm_sequence_token(year, *key) == token]
    if len(matched) != 1:
        raise SourceUnavailable("BM selection does not match Telegram sequence")
    key, members = matched[0]
    pairs = {}
    for r in members:
        sk = str(r.get("sk_code") or "").strip()
        sp = str(r.get("sp_code") or "").strip()
        if sk and sp:
            corrected_sk, proof = _correct_one_verified_bm_mapping(
                path, year, key, sk, sp
            )
            pairs.setdefault((corrected_sk, sp), {
                "sk_code": corrected_sk,
                "sk_text": (proof["sk_text"] if proof else
                            str(r.get("sk_text") or "")),
                "sp_code": sp,
                "sp_text": (proof["sp_text"] if proof else
                            str(r.get("sp_text") or "")),
            })
    if not pairs:
        raise SourceUnavailable("BM PdP lacks a verified SK/SP pair")
    return key, members, list(pairs.values())


def _state(runtime, year, unit, token, teacher):
    (theme, code, title, topic), rows, standards = _select(
        runtime, year, unit, token)
    cls, dt, tm, pupils, day = _teacher_metadata(teacher, "BM")
    first = rows[0]

    def joined(field):
        parts = []
        for row in rows:
            value = str(row.get(field) or "").strip()
            if value and value not in parts:
                parts.append(value)
        return "; ".join(parts)

    state = {
        "task": "rph",
        "quick_material_flow": True,
        "assessment_mode": "formative",
        "year": f"Tahun {year}", "year_label": f"Tahun {year}",
        "subject": "Bahasa Melayu",
        "unit": title, "unit_title": title,
        "topic": title, "subtopic": topic, "pdp_title": topic,
        "rpt_theme": theme, "rpt_unit_title": title,
        "rpt_topic": topic, "unit_code": code,
        "skill_metadata": joined("skill_metadata"),
        "textbook_ref": joined("textbook_ref"),
        "activitybook_ref": joined("activitybook_ref"),
        "rph_class": cls,
        "rph_date": __import__("datetime").date.fromisoformat(dt).strftime("%d/%m/%Y") if dt else "",
        "rph_day": day, "rph_time": tm, "rph_students": pupils,
        "rph_teacher_reflection": clean_reflection(teacher.get("reflection", "")),
        "variation_seed": "web-bm-verified-" + token,
    }
    source_seq = str(first.get("source_sequence_no") or "")
    if source_seq.isdigit() and 0 < int(source_seq) < 10000:
        state["pdp_no"] = int(source_seq)
        state["source_sequence_no"] = int(source_seq)
    # verified_pdp_sequence carries the exact grouped SP codes, but some
    # rows have blank wording. Enrich only through the same v26.00 master
    # curriculum_standards table for the exact BM year/SK/SP, read-only.
    from web.bm_web_rph_refinement import complete_verified_bm_standards
    source_path = getattr(runtime, "DB_PATH", None)
    standards = list(complete_verified_bm_standards(source_path, year, standards))
    commit = getattr(runtime, "_commit_multi_sp", None)
    if not callable(commit):
        raise SourceUnavailable("Telegram BM grouped SP engine unavailable")
    try:
        commit(state, standards)
    except Exception as exc:
        raise SourceUnavailable("Native BM SP mapping failed") from exc
    state["selected_sp_codes"] = list(state.get("grouped_sp_codes") or [])
    if not state.get("sk_code") or not state.get("sp_code"):
        raise SourceUnavailable("Native BM RPH standards unavailable")
    # Opt in to Web-only BM activity refinement with identity from the live,
    # read-only Telegram master source, never from browser-supplied prose.
    state["_bm_web_native_source"] = "verified_pdp_sequence"
    state["_bm_web_verified_standards"] = tuple(dict(item) for item in standards)
    return state


def _content(runtime, state):
    generator = getattr(runtime, "_local_rph_text", None)
    if not callable(generator):
        raise SourceUnavailable("Native Telegram RPH composer unavailable")
    try:
        document = generator(state)
    except Exception as exc:
        raise SourceUnavailable("Native Telegram BM RPH unavailable") from exc
    if not isinstance(document, str) or len(document.strip()) < 500:
        raise SourceUnavailable("BM RPH content incomplete")
    return document


def create_native_bm_rph_blueprint(runtime):
    for name in ("_commit_multi_sp", "_local_rph_text",
                 "create_word_file", "create_pdf_file"):
        if not callable(getattr(runtime, name, None)):
            raise TypeError("Telegram BM RPH engine incomplete")

    # Hook the existing Word/PDF row boundary once. Every other Telegram flow
    # remains unchanged because only this endpoint sets the BM Web source flag.
    from web.bm_web_rph_refinement import install as install_bm_web_refinement
    if not install_bm_web_refinement(runtime):
        raise TypeError("BM Web row refinement not installed")
    bp = Blueprint("telegram_native_bm_sequence_rph", __name__)

    @bp.after_request
    def private(resp):
        resp.headers["Cache-Control"] = "no-store, private"
        resp.headers["Vary"] = "Authorization"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    @bp.before_request
    def auth():
        if os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED") != "1":
            return jsonify({"error": "Native BM RPH disabled"}), 503
        if not _authorization():
            return jsonify({"error": "Unauthorized"}), 401

    def query():
        if (set(request.args) != {"year", "subject", "unit", "lesson"}
                or any(len(request.args.getlist(k)) != 1 for k in request.args)
                or request.args["subject"] != "BM"
                or not re.fullmatch(r"[1-6]", request.args["year"])):
            raise ValueError("Invalid BM selection")
        return (int(request.args["year"]), request.args["unit"],
                request.args["lesson"])

    @bp.get("/internal/rph/v1/bm-sequence/availability")
    def availability():
        try:
            year, unit, token = query()
            state = _state(runtime, year, unit, token, {
                "class": "", "date": "", "time": "", "students": "",
            })
            _content(runtime, state)
        except (ValueError, SourceUnavailable):
            return jsonify({"available": False}), 404
        return jsonify({"available": True, "generator": "telegram-native"})

    @bp.post("/internal/rph/v1/bm-sequence/render")
    def render():
        if (not request.is_json or request.content_length is None
                or request.content_length > MAX_BODY):
            return jsonify({"error": "Invalid document request"}), 400
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {
                "selection", "teacher", "format"}:
            return jsonify({"error": "Invalid selection"}), 400
        selected = data["selection"]
        fmt = data["format"]
        if (fmt not in MIMES or not isinstance(selected, dict)
                or set(selected) != {"year", "subject", "unit", "lesson"}
                or selected["subject"] != "BM"):
            return jsonify({"error": "Invalid BM selection"}), 400
        try:
            state = _state(runtime, selected["year"],
                           selected["unit"], selected["lesson"],
                           data["teacher"])
            text = _content(runtime, state)
        except (ValueError, SourceUnavailable, TypeError, KeyError):
            return jsonify({"error": "BM PdP RPH unavailable"}), 404

        unique = "web" + uuid.uuid4().hex
        output = None
        try:
            output = (runtime.create_word_file(state, text, unique)
                      if fmt == "word" else runtime.create_pdf_file(
                          state, text, unique))
            dest = Path(output).resolve(strict=True)
            temporary = Path(tempfile.gettempdir()).resolve()
            if dest.parent != temporary or not dest.name.startswith(unique + "_"):
                raise ValueError("Unexpected output path")
            if not 1000 <= dest.stat().st_size <= MAX_FILE:
                raise ValueError("Invalid BM RPH document")
            body = dest.read_bytes()
            if fmt == "word":
                body = compact_web_word_notes(body)
                if not body.startswith(b"PK\x03\x04"):
                    raise ValueError("Invalid Word signature")
                with ZipFile(io.BytesIO(body)) as f:
                    if f.testzip() or "word/document.xml" not in f.namelist():
                        raise ValueError("Invalid DOCX archive")
            elif not body.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF signature")
            response = Response(body, mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = (
                'attachment; filename="CikguLaju_RPH.' +
                ("docx" if fmt == "word" else "pdf") + '"')
            return response
        except Exception as exc:
            print("Native BM RPH render failed:", type(exc).__name__, flush=True)
            return jsonify({"error": "Telegram BM document unavailable"}), 503
        finally:
            if isinstance(output, (str, os.PathLike)):
                try:
                    dest = Path(output).resolve()
                    if (dest.parent == Path(tempfile.gettempdir()).resolve()
                            and dest.name.startswith(unique + "_")):
                        dest.unlink(missing_ok=True)
                except (OSError, ValueError):
                    pass

    return bp
