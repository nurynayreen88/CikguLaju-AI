"""Native Sains/Matematik Web RPH through Telegram's verified PdP sequence.

Unlike RPT-week rows, these subjects choose an exact grouped PdP sequence
from Telegram's _sm2542_rows (including every mapped SP). Unit keys are
derived from the same unit-code/title pair as the Telegram bot menu.
No material is generated for guessed row numbers or unrelated subjects.
"""
import hashlib
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
from web.telegram_verified_rpt_rph_bridge import (
    _authorization, _teacher_metadata, SourceUnavailable,
)

SUBJECTS = {"MATH": "Matematik", "SCIENCE": "Sains"}
MAX_FILE = 15 * 1024 * 1024


def _source(runtime, year, subject):
    if type(year) is not int or not 1 <= year <= 6 or subject not in SUBJECTS:
        raise ValueError("Invalid subject/year")
    if not getattr(runtime, "CIKGULAJU_DB_V2600_ACTIVE", False):
        raise SourceUnavailable("Main Telegram curriculum inactive")
    rows_reader = getattr(runtime, "_sm2542_rows", None)
    units_reader = getattr(runtime, "_sm2542_unique_units", None)
    if not callable(rows_reader) or not callable(units_reader):
        raise SourceUnavailable("Telegram PdP sequence unavailable")
    try:
        rows = rows_reader(f"Tahun {year}", SUBJECTS[subject])
        units = units_reader(rows)
    except Exception as exc:
        raise SourceUnavailable("Native PdP sequence unavailable") from exc
    if not isinstance(rows, list) or not isinstance(units, list):
        raise SourceUnavailable("Unexpected PdP source")
    if len(rows) > 5000 or len(units) > 500:
        raise SourceUnavailable("Oversized native PdP sequence")
    return rows, units


def _unit_token(unit_code, unit_title):
    raw = str(unit_code) + "\x00" + str(unit_title)
    return "u" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _unit_catalog(units):
    output = []
    for code, title in units:
        code, title = str(code or "").strip(), str(title or "").strip()
        if not title or len(code) > 80 or len(title) > 250:
            continue
        label = (code + " • " if code else "") + title
        output.append({
            "value": _unit_token(code, title), "label": label,
            "_unit_code": code, "_unit_title": title,
        })
    if len({x["value"] for x in output}) != len(output):
        raise SourceUnavailable("Ambiguous unit sequence")
    return output


def _pdp_groups(rows, code, title):
    chosen = [
        row for row in rows
        if isinstance(row, dict) and (
            ((str(row.get("unit_code") or "").strip(),
              str(row.get("unit_title") or "").strip()) == (code, title))
            or (not code and not str(row.get("unit_title") or "").strip()
                and str(row.get("theme") or "").strip() == title)
        )
    ]
    groups = {}
    for row in chosen:
        key = str(row.get("pdp_sequence_code") or "").strip()
        if key:
            groups.setdefault(key, []).append(row)
    return groups


def _available_groups(rows, unit, year, subject):
    groups = {
        code: items for code, items in
        _pdp_groups(rows, unit["_unit_code"], unit["_unit_title"]).items()
        if len(code) <= 100 and not any(ord(c) < 32 for c in code)
        and any(str(row.get("sk_code") or "").strip()
                and str(row.get("sp_code") or "").strip() for row in items)
    }
    if year == 6 and subject == "MATH":
        # Six source-backed Year 6 ratio lessons currently carry *Data* 8.x
        # codes (DSKP 2021 requires 7.2/7.3/7.4). Hide only the exact
        # known-bad codes. This also protects stale availability/render URLs
        # before the Web can debit a user's free trial credit.
        from web.math_y6_ratio_source_hold_20261110 import (
            held_math_y6_ratio_source,
        )
        groups = {
            code: items for code, items in groups.items()
            if not held_math_y6_ratio_source(year, subject, code, items)
        }
    return groups


def _resolve(runtime, year, subject, unit_token, pdp_code=None):
    if (not isinstance(unit_token, str)
            or not re.fullmatch(r"u[a-f0-9]{24}", unit_token)):
        raise ValueError("Invalid unit token")
    rows, units = _source(runtime, year, subject)
    matched = [item for item in _unit_catalog(units) if item["value"] == unit_token]
    if len(matched) != 1:
        raise SourceUnavailable("Unit not verified by Telegram")
    unit = matched[0]
    groups = _available_groups(rows, unit, year, subject)
    if pdp_code is None:
        return unit, groups
    if not isinstance(pdp_code, str) or not 0 < len(pdp_code) <= 100:
        raise ValueError("Invalid PdP code")
    if any(ord(c) < 32 for c in pdp_code):
        raise ValueError("Invalid PdP code")
    found = groups.get(pdp_code)
    if not found:
        raise SourceUnavailable("PdP not present in Telegram sequence")
    pairs = set()
    mapped = []
    for row in found:
        sk, sp = (str(row.get(k) or "").strip() for k in ("sk_code", "sp_code"))
        if not sk or not sp:
            continue
        pair = sk, sp
        if pair not in pairs:
            pairs.add(pair)
            mapped.append({
                "sk_code": sk, "sk_text": str(row.get("sk_text") or ""),
                "sp_code": sp, "sp_text": str(row.get("sp_text") or ""),
            })
    if not mapped:
        raise SourceUnavailable("Native PdP lacks verified SK/SP")
    return unit, found, mapped


def _build_state(runtime, year, subject, unit_token, pdp_code, teacher):
    unit, rows, mapped = _resolve(runtime, year, subject, unit_token, pdp_code)
    cls, dt, tm, pupils, day = _teacher_metadata(teacher, subject)
    first = rows[0]
    title = unit["_unit_title"]
    def join(field):
        values = []
        for row in rows:
            val = str(row.get(field) or "").strip()
            if val and val not in values:
                values.append(val)
        return "; ".join(values)
    state = {
        "task": "rph", "quick_material_flow": True,
        "assessment_mode": "formative",
        "year": f"Tahun {year}", "year_label": f"Tahun {year}",
        "subject": SUBJECTS[subject],
        "unit": title, "unit_title": title,
        "topic": title,
        "subtopic": str(first.get("pdp_title") or "").strip(),
        "pdp_title": str(first.get("pdp_title") or "").strip(),
        "pdp_sequence_code": pdp_code,
        "source_sequence_no": first.get("source_sequence_no"),
        "pdp_no": first.get("source_sequence_no"),
        "rpt_theme": str(first.get("theme") or ""),
        "rpt_unit_title": title,
        "rpt_topic": str(first.get("pdp_title") or ""),
        "skill_metadata": join("skill_metadata"),
        "textbook_ref": join("textbook_ref"),
        "activitybook_ref": join("activitybook_ref"),
        "rph_class": cls, "rph_date": (date.fromisoformat(dt).strftime("%d/%m/%Y") if dt else ""), "rph_time": tm,
        "rph_day": day, "rph_students": pupils,
        "rph_teacher_reflection": clean_reflection(teacher.get("reflection", "")),
        "variation_seed": "web-native-pdp-" + subject + "-" + pdp_code,
    }
    group = getattr(runtime, "_commit_multi_sp", None)
    if not callable(group):
        raise SourceUnavailable("Native grouped SP resolver unavailable")
    group(state, mapped)
    state["selected_sp_codes"] = list(state.get("grouped_sp_codes") or [])
    if not state.get("sp_code") or not state.get("selected_sp_codes"):
        raise SourceUnavailable("No grouped SP selected")
    return state


def _source_text(runtime, state):
    local = getattr(runtime, "_local_rph_text", None)
    if not callable(local):
        raise SourceUnavailable("Native Telegram lesson text unavailable")
    try:
        text = local(state)
    except Exception as exc:
        raise SourceUnavailable("Native Telegram SP-specific RPH unavailable") from exc
    if not isinstance(text, str) or len(text.strip()) < 500:
        raise SourceUnavailable("SP-specific lesson activities incomplete")
    return text


def create_native_sequence_rph_blueprint(runtime):
    if not all(callable(getattr(runtime, x, None)) for x in (
            "_sm2542_rows", "_sm2542_unique_units", "_commit_multi_sp",
            "_local_rph_text", "create_word_file", "create_pdf_file")):
        raise TypeError("Native Telegram Maths/Science RPH engine incomplete")
    bp = Blueprint("telegram_native_sequence_rph", __name__)

    @bp.after_request
    def private(resp):
        resp.headers["Cache-Control"] = "no-store, private"
        resp.headers["Vary"] = "Authorization"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    @bp.before_request
    def authorized():
        if os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED") != "1":
            return jsonify({"error": "Native RPH disabled"}), 503
        if not _authorization():
            return jsonify({"error": "Unauthorized"}), 401

    def _query(expected):
        if set(request.args) != expected or any(len(request.args.getlist(k)) != 1
                                                 for k in request.args):
            raise ValueError("Unexpected query keys")
        raw = request.args["year"]
        if not re.fullmatch(r"[1-6]", raw):
            raise ValueError("Invalid year")
        subject = request.args["subject"]
        if subject not in SUBJECTS:
            raise ValueError("Invalid subject")
        return int(raw), subject

    @bp.get("/internal/rph/v1/sequence/units")
    def units():
        try:
            year, sub = _query({"year", "subject"})
            rows, known = _source(runtime, year, sub)
            catalog = [
                unit for unit in _unit_catalog(known)
                if _available_groups(rows, unit, year, sub)
            ]
        except (ValueError, SourceUnavailable):
            return jsonify({"error": "Native units unavailable"}), 503
        return jsonify({"source": "telegram-runtime-v1",
                        "items": [{"value": u["value"], "label": u["label"]}
                                  for u in catalog]})

    @bp.get("/internal/rph/v1/sequence/lessons")
    def lessons():
        try:
            year, sub = _query({"year", "subject", "unit"})
            _, groups = _resolve(runtime, year, sub, request.args["unit"])
            items = []
            for code, rows in groups.items():
                r = rows[0]
                seq = r.get("source_sequence_no")
                title = str(r.get("pdp_title") or code).strip()
                label = ("PdP " + str(seq) + " • " if seq not in (None, "") else
                         "PdP • ") + title
                if len(code) > 100 or not code or len(label) > 300:
                    continue
                # Keep only lesson-specific textbook references recorded by
                # the verified Telegram native sequence. No inferred pages.
                refs = []
                for item in rows:
                    value = str(item.get("textbook_ref") or "").strip()
                    if value and len(value) <= 120 and value not in refs:
                        refs.append(value)
                entry = {"value": code, "label": label}
                if refs:
                    entry["textbook_ref"] = " • ".join(refs[:3])
                items.append(entry)
        except (ValueError, SourceUnavailable):
            return jsonify({"error": "Native PdP choices unavailable"}), 503
        return jsonify({"source": "telegram-runtime-v1", "items": items})

    @bp.get("/internal/rph/v1/sequence/availability")
    def availability():
        try:
            year, sub = _query({"year", "subject", "unit", "lesson"})
            state = _build_state(runtime, year, sub, request.args["unit"],
                                 request.args["lesson"],
                                 {"class":"","date":"","time":"","students":""})
            _source_text(runtime, state)
        except (ValueError, SourceUnavailable):
            return jsonify({"available": False}), 404
        return jsonify({"available": True, "generator": "telegram-native"})

    @bp.post("/internal/rph/v1/sequence/render")
    def render():
        if (not request.is_json or request.content_length is None
                or request.content_length > 7000):
            return jsonify({"error": "Invalid document request"}), 400
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {
                "selection", "teacher", "format"}:
            return jsonify({"error": "Invalid selection"}), 400
        sel, fmt = data["selection"], data["format"]
        if not isinstance(sel, dict) or set(sel) != {
                "year", "subject", "unit", "lesson"} or fmt not in MIMES:
            return jsonify({"error": "Invalid selection"}), 400
        try:
            state = _build_state(runtime, sel["year"], sel["subject"],
                                 sel["unit"], sel["lesson"], data["teacher"])
            text = _source_text(runtime, state)
        except (ValueError, SourceUnavailable, KeyError, TypeError):
            return jsonify({"error": "Native PdP RPH unavailable"}), 404
        unique = "web" + uuid.uuid4().hex
        output = None
        try:
            output = (runtime.create_word_file(state, text, unique) if fmt == "word"
                      else runtime.create_pdf_file(state, text, unique))
            path = Path(output).resolve(strict=True)
            temp = Path(tempfile.gettempdir()).resolve()
            if path.parent != temp or not path.name.startswith(unique+"_"):
                raise ValueError("Unexpected RPH output")
            if not 1000 <= path.stat().st_size <= MAX_FILE:
                raise ValueError("Invalid RPH length")
            content = path.read_bytes()
            if fmt == "word":
                content = compact_web_word_notes(content)
                if not content.startswith(b"PK\x03\x04"):
                    raise ValueError("Invalid Word file")
                with ZipFile(io.BytesIO(content)) as archive:
                    if archive.testzip() or "word/document.xml" not in archive.namelist():
                        raise ValueError("Invalid Word package")
            elif not content.startswith(b"%PDF-"):
                raise ValueError("Invalid PDF file")
            # This private Telegram endpoint powers Web native Maths Word/PDF.
            # The actual output is checked before Web can debit trial credits.
            # Sains and direct Telegram bot handlers remain unchanged.
            if sel["subject"] == "MATH":
                from web.math_rph_delivery_quality_20261110 import (
                    MathQualityReadError, inspect_math_rph_document,
                )
                try:
                    quality = inspect_math_rph_document({
                        "source": "telegram-native-pdp-sequence",
                        "subject": "MATH",
                        "teacher": data["teacher"],
                    }, fmt, content)
                except MathQualityReadError:
                    return jsonify({
                        "error": "RPH Matematik belum boleh disahkan.",
                        "code": "MATH_RPH_QUALITY_CHECK_UNAVAILABLE",
                    }), 503
                if quality.get("inspection") == "PDF_PARSER_UNAVAILABLE":
                    return jsonify({
                        "error": "Semakan PDF Matematik belum tersedia.",
                        "code": "MATH_RPH_QUALITY_CHECK_UNAVAILABLE",
                    }), 503
                if quality["issues"]:
                    return jsonify({
                        "error": "RPH Matematik perlu pembetulan sebelum dimuat turun.",
                        "code": "MATH_RPH_QUALITY_REVIEW_REQUIRED",
                    }), 503
            response = Response(content,mimetype=MIMES[fmt])
            response.headers["Content-Disposition"] = (
                'attachment; filename="CikguLaju_RPH.' +
                ("docx" if fmt == "word" else "pdf") + '"'
            )
            return response
        except Exception as exc:
            print("Native PdP RPH unavailable:",type(exc).__name__,flush=True)
            return jsonify({"error": "Telegram RPH rendering failed"}), 503
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
