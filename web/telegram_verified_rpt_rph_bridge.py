"""Private Web -> Telegram RPH bridge for exact verified master RPT rows.

This adapter never accepts RPH prose, SK/SP codes, or an arbitrary file path from
the browser. It resolves an exact active Telegram master-database row and passes
that source to the original Telegram local RPH text and Word/PDF generators.

Scope is deliberately limited to BM and Pendidikan Islam. Mathematics and
Science use separate native PdP-sequence engines and must not be mapped by
matching a misleading RPT row/sequence number.
"""
import hmac
import io
import os
import re
import sqlite3
import tempfile
import uuid
from datetime import date
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from flask import Blueprint, Response, jsonify, request

from web.native_rph_telegram_api import MIMES, compact_web_word_notes
from web.rph_teacher_reflection import clean_reflection, valid_teacher_fields

CODE_LABELS = {"BM": "Bahasa Melayu", "PI": "Pendidikan Islam"}
MAX_FILE = 15 * 1024 * 1024
MAX_BODY = 7000


class SourceUnavailable(Exception):
    pass


def _authorization():
    secret = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    return (os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED") == "1"
            and len(secret) >= 32
            and hmac.compare_digest(request.headers.get("Authorization", ""),
                                    "Bearer " + secret))


def _validate_selection(selection):
    if not isinstance(selection, dict) or set(selection) != {"year", "subject", "unit", "lesson"}:
        raise ValueError("Invalid curriculum selection")
    year, subject, unit, lesson = (
        selection[k] for k in ("year", "subject", "unit", "lesson")
    )
    if type(year) is not int or year not in range(1, 7):
        raise ValueError("Invalid year")
    if subject not in CODE_LABELS:
        raise ValueError("Invalid subject")
    if not isinstance(unit, str) or not unit.strip() or len(unit) > 300:
        raise ValueError("Invalid unit")
    if type(lesson) is not int or not 0 < lesson < 2**31:
        raise ValueError("Invalid RPT row ID")
    return year, subject, unit, lesson


def _resolve_verified_rpt(runtime, selection):
    year, code, unit, lesson = _validate_selection(selection)
    if not getattr(runtime, "CIKGULAJU_DB_V2600_ACTIVE", False):
        raise SourceUnavailable("Authoritative Telegram database inactive")
    db = getattr(runtime, "DB_PATH", None)
    if not isinstance(db, (str, os.PathLike)) or not Path(db).is_file():
        raise SourceUnavailable("Authoritative Telegram database missing")
    path = Path(db).resolve()
    if path.is_symlink() or not path.is_file():
        raise SourceUnavailable("Invalid master database path")
    uri = path.as_uri() + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            matched = conn.execute(
                """SELECT * FROM rpt_entries
                   WHERE id=? AND year_label=? AND subject=? AND verified=1
                     AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                   LIMIT 1""",
                (lesson, f"Tahun {year}", CODE_LABELS[code]),
            ).fetchone()
            if matched is None:
                raise SourceUnavailable("Verified RPT row unavailable")
            row = dict(matched)
            # Unit is the exact value shown by the authoritative dropdown.
            if (row.get("unit_title") or "").strip() != unit.strip():
                raise SourceUnavailable("RPT unit and selected lesson differ")
            src_activity = str(row.get("activity_note") or "").strip()
            if len(src_activity) < 30 or src_activity.casefold() in (
                    "aktiviti berpandu, aplikasi dan pentaksiran formatif mengikut sp.",
                    "aktiviti mengikut sk dan sp"):
                raise SourceUnavailable("Lesson-specific source activity unavailable")
            standards = [dict(item) for item in conn.execute(
                """SELECT standard_type,standard_code,standard_text,sequence_no
                   FROM rpt_entry_standards
                   WHERE rpt_entry_id=? AND verified=1
                   ORDER BY CASE standard_type WHEN 'SK' THEN 0 ELSE 1 END,
                            sequence_no, id""",
                (lesson,),
            ).fetchall()]
            sk = [s for s in standards if s["standard_type"] == "SK"
                  and str(s["standard_code"] or "").strip()]
            sp = [s for s in standards if s["standard_type"] == "SP"
                  and str(s["standard_code"] or "").strip()]
            if not sk or not sp:
                raise SourceUnavailable("Verified SK/SP incomplete")
            row["_std"] = standards
            if code == "PI":
                detail = conn.execute(
                    """SELECT * FROM pi_pdp_details_v2591
                       WHERE year_label=? AND pdp_no=? AND verified=1
                       LIMIT 1""",
                    (f"Tahun {year}", row.get("sequence_no")),
                ).fetchone()
                if detail is None:
                    raise SourceUnavailable("Verified Jawi PdP context unavailable")
                row.update(dict(detail))
    except (sqlite3.Error, OSError) as exc:
        raise SourceUnavailable("Master RPT read failed") from exc
    return row


def _teacher_metadata(teacher, code):
    if not valid_teacher_fields(teacher):
        raise ValueError("Invalid teacher metadata")
    clean_reflection(teacher.get("reflection", ""))
    cls, dt, tm, pupils = (teacher[k] for k in ("class", "date", "time", "students"))
    if any(not isinstance(v, str) for v in (cls, dt, tm, pupils)):
        raise ValueError("Invalid teacher field")
    if len(cls) > 40 or (cls and not re.fullmatch(r"[\w .\-/()]+", cls)):
        raise ValueError("Invalid class")
    if dt:
        if not re.fullmatch(r"20\d\d-\d\d-\d\d", dt):
            raise ValueError("Invalid date")
        actual = date.fromisoformat(dt)
        if actual.year not in range(2025, 2032):
            raise ValueError("Invalid date range")
        day = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"][actual.weekday()]
    else:
        day = ""
    if tm:
        ticks = re.split(r"\s*-\s*", tm)
        if (len(ticks) not in (1, 2)
                or not all(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t) for t in ticks)
                or len(ticks) == 2 and ticks[0] >= ticks[1]):
            raise ValueError("Invalid time")
    if pupils and (not re.fullmatch(r"[1-9]\d{0,2}", pupils) or int(pupils) > 200):
        raise ValueError("Invalid student count")
    return cls, dt, tm, pupils, day


def _native_state(runtime, selection, teacher):
    year, code, unit, lesson = _validate_selection(selection)
    row = _resolve_verified_rpt(runtime, selection)
    cls, dt, tm, pupils, day = _teacher_metadata(teacher, code)
    standards = row["_std"]
    sk = [s for s in standards if s["standard_type"] == "SK"
          and str(s.get("standard_code") or "").strip()]
    sp = [s for s in standards if s["standard_type"] == "SP"
          and str(s.get("standard_code") or "").strip()]
    src = dict(row)
    src.pop("_std", None)
    state = {
        "task": "rph",
        "quick_material_flow": True,
        "rph_mode": "fast_rpt",
        "year": f"Tahun {year}",
        "year_label": f"Tahun {year}",
        "subject": CODE_LABELS[code],
        "unit": unit,
        "rpt_entry_id": lesson,
        "pdp_no": row.get("sequence_no"),
        "lesson_no": row.get("sequence_no"),
        "lesson": row.get("sequence_no"),
        "topic": str(row.get("topic") or unit),
        "subtopic": str(row.get("subtopic") or row.get("skill_focus") or ""),
        "rpt_activity_note": str(row.get("activity_note") or ""),
        "rpt_assessment_note": str(row.get("assessment_note") or ""),
        "rph_class": cls, "rph_date": (date.fromisoformat(dt).strftime("%d/%m/%Y") if dt else ""), "rph_time": tm,
        "rph_day": day, "rph_students": pupils,
        "rph_teacher_reflection": clean_reflection(teacher.get("reflection", "")),
        "_quick_selected_rpt_row_v2388": src,
        "quick_rpt_row": src,
        "variation_seed": "web-rpt-" + str(lesson),
    }
    if callable(getattr(runtime, "_apply_rpt_structure_context_v2384", None)):
        runtime._apply_rpt_structure_context_v2384(state, row)
    state.update({
        "grouped_sk_codes": [str(s["standard_code"]) for s in sk],
        "selected_sk_codes": [str(s["standard_code"]) for s in sk],
        "grouped_sk_texts": [str(s.get("standard_text") or "") for s in sk],
        "grouped_sp_codes": [str(s["standard_code"]) for s in sp],
        "selected_sp_codes": [str(s["standard_code"]) for s in sp],
        "grouped_sp_texts": [str(s.get("standard_text") or "") for s in sp],
        "sk_code": str(sk[0]["standard_code"]),
        "sk_text": str(sk[0].get("standard_text") or ""),
        "sp_code": str(sp[0]["standard_code"]),
        "sp_text": str(sp[0].get("standard_text") or ""),
    })
    if code == "PI":
        state.update({
            "_pi_full_jawi_rph_v25210": True,
            "_pi_khatam_tasmik_v25210": False,
            "topic": str(row.get("topic") or row.get("skill_focus") or unit),
            "subtopic": str(row.get("subtopic") or ""),
            "rpt_objective_jawi": str(row.get("objective_jawi") or ""),
            "textbook_unit": str(row.get("textbook_unit") or ""),
            "textbook_pages": str(row.get("textbook_pages") or ""),
        })
    return state


def _native_text(runtime, state):
    generate = getattr(runtime, "_local_rph_text", None)
    if not callable(generate):
        raise SourceUnavailable("Native RPH text engine absent")
    try:
        text = generate(state)
    except Exception as exc:
        raise SourceUnavailable("Native RPH content unavailable") from exc
    if not isinstance(text, str) or len(text.strip()) < 500:
        raise SourceUnavailable("RPH source content incomplete")
    # This route must never invent a source or return a generic unverified RPH.
    if not (state.get("sp_code") and state.get("rpt_entry_id")):
        raise SourceUnavailable("No confirmed lesson standards")
    return text


def create_native_db_rph_blueprint(runtime):
    if not all(callable(getattr(runtime, name, None)) for name in (
            "create_word_file", "create_pdf_file", "_local_rph_text")):
        raise TypeError("Native Telegram RPH engine unavailable")
    bp = Blueprint("telegram_native_verified_rpt_rph", __name__)

    @bp.after_request
    def no_cache(resp):
        resp.headers["Cache-Control"] = "no-store, private"
        resp.headers["Vary"] = "Authorization"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    @bp.before_request
    def authorize():
        if os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED") != "1":
            return jsonify({"error": "Native RPH disabled"}), 503
        if not _authorization():
            return jsonify({"error": "Unauthorized"}), 401

    @bp.get("/internal/rph/v1/verified-rpt/availability")
    def availability():
        args = request.args
        if set(args) != {"year", "subject", "unit", "lesson"} or any(
                len(args.getlist(k)) != 1 for k in args):
            return jsonify({"available": False}), 400
        try:
            if not re.fullmatch(r"[1-6]", args["year"]) or not re.fullmatch(
                    r"[1-9][0-9]{0,9}", args["lesson"]):
                raise ValueError("Invalid number")
            selection = {
                "year": int(args["year"]),
                "subject": args["subject"],
                "unit": args["unit"],
                "lesson": int(args["lesson"]),
            }
            state = _native_state(runtime, selection, {
                "class": "", "date": "", "time": "", "students": "",
            })
            _native_text(runtime, state)
        except (ValueError, SourceUnavailable):
            return jsonify({"available": False}), 404
        return jsonify({"available": True, "generator": "telegram-native"})

    @bp.post("/internal/rph/v1/verified-rpt/render")
    def render():
        if (not request.is_json or request.content_length is None
                or request.content_length > MAX_BODY):
            return jsonify({"error": "Invalid RPH request"}), 400
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {
                "selection", "teacher", "format"}:
            return jsonify({"error": "Invalid RPH selection"}), 400
        fmt = body["format"]
        if fmt not in MIMES:
            return jsonify({"error": "Invalid format"}), 400
        try:
            state = _native_state(runtime, body["selection"], body["teacher"])
            text = _native_text(runtime, state)
        except (ValueError, SourceUnavailable, KeyError):
            return jsonify({"error": "Verified lesson RPH unavailable"}), 404
        unique = "web" + uuid.uuid4().hex
        output = None
        try:
            output = (runtime.create_word_file(state, text, unique) if fmt == "word"
                      else runtime.create_pdf_file(state, text, unique))
            path = Path(output).resolve(strict=True)
            temp = Path(tempfile.gettempdir()).resolve()
            if path.parent != temp or not path.name.startswith(unique + "_"):
                raise ValueError("Unexpected output path")
            if not 1000 <= path.stat().st_size <= MAX_FILE:
                raise ValueError("RPH output invalid")
            data = path.read_bytes()
            if fmt == "word":
                data = compact_web_word_notes(data)
                if not data.startswith(b"PK\x03\x04"):
                    raise ValueError("Invalid Word document")
                with ZipFile(io.BytesIO(data)) as archive:
                    if archive.testzip() or "word/document.xml" not in archive.namelist():
                        raise ValueError("Invalid Word package")
            elif not data.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF")
            response = Response(data, mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = (
                'attachment; filename="CikguLaju_RPH.' +
                ("docx" if fmt == "word" else "pdf") + '"'
            )
            return response
        except Exception as exc:
            print("Verified RPT native RPH render unavailable:",
                  type(exc).__name__, flush=True)
            return jsonify({"error": "Native document unavailable"}), 503
        finally:
            if isinstance(output, (str, os.PathLike)):
                try:
                    target = Path(output).resolve()
                    if (target.parent == Path(tempfile.gettempdir()).resolve()
                            and target.name.startswith(unique + "_")):
                        target.unlink(missing_ok=True)
                except (OSError, ValueError):
                    pass

    return bp
