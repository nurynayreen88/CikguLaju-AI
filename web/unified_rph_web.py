"""Unified source-backed Web RPH preview after Year > Subject > Unit > Lesson/PdP.

Staging only. It never imports app.py, writes to databases, changes Telegram,
or treats a verified RPT row or a generic template as an approved RPH.

The catalog is built from explicit English SOW lesson identity, Moral crosswalk,
and PJPK 339-PdP manifest. Missing or contradictory source files fail closed.
For other subjects, keep existing database navigation; no invented preview.
"""
import csv
from datetime import date
from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
import re
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Blueprint, jsonify, request, send_file

from web.english_rpt_2027_http import _account, _has_paid_access

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "audits/english_primary_2_6_official_sow_index_20261103.json"
SUBJECT_LABELS = {
    "ENGLISH": "Bahasa Inggeris",
    "BM": "Bahasa Melayu",
    "MATH": "Matematik",
    "SCIENCE": "Sains",
    "PI": "Pendidikan Islam",
    "PJPK": "PJPK",
    "MORAL": "Pendidikan Moral",
    "PSV": "Pendidikan Seni Visual",
}
SOURCE_SUBJECTS = frozenset(("ENGLISH", "MORAL", "PJPK", "PSV"))
MAX_TOKEN = 40

def _safe_text(value, limit=300):
    return isinstance(value, str) and 0 < len(value) <= limit and bool(value.strip())

@lru_cache(maxsize=1)
def english_index():
    try:
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        lessons = index["lessons"]
        if index.get("version") != "2026-11-03-source-table-2-6":
            return {}
        if any(sum(k.startswith(f"{year}/") for k in lessons) != 160 for year in range(2, 7)):
            return {}
        return lessons
    except (OSError, TypeError, ValueError, KeyError):
        return {}

def _english_records(year):
    index = english_index()
    result = []
    for n in range(1, 161):
        rec = index.get(f"{year}/{n}")
        if not isinstance(rec, dict) or rec.get("n") != n:
            continue
        topic = str(rec.get("topic") or "").strip()
        focus = str(rec.get("focus") or "").strip()
        if not topic:
            topic = "Lesson pilihan guru"
        path = ROOT / "rph_standalone" / "english" / f"year{year}" / f"lesson_{n:03d}.md"
        if not path.is_file():
            continue
        result.append({"unit": topic, "label": f"Lesson {n:03d} — {focus or topic}",
                       "lesson": n, "token": f"e-{year}-{n:03d}",
                       "path": path, "status": "PRATONTON BELUM MUKTAMAD"})
    return result

def _moral_records(year):
    from web.pendidikan_moral_80_runtime import load_candidate
    crosswalk = ROOT / "rpt_2027" / "pendidikan_moral" / f"year{year}_crosswalk_DSKP.json"
    try:
        info = json.loads(crosswalk.read_text(encoding="utf-8"))
        if info.get("status") != "DRAF_SEMAK" or len(info["units"]) != 14:
            return []
    except (OSError, ValueError, TypeError, KeyError):
        return []
    entries = []
    for n in range(1, 43):
        candidate = load_candidate(year, n)
        if candidate is None:
            continue
        idx = (n-1)//3
        unit = info["units"][idx]
        if int(unit.get("unit", -1)) != idx + 1:
            continue
        title = str(unit.get("title") or "").strip()
        if not title:
            continue
        path = ROOT / "rph_standalone" / "pendidikan_moral" / f"year{year}" / f"lesson_{n:03d}.md"
        if not path.is_file():
            continue
        entries.append({"unit": f"Unit {idx+1:02d} — {title}",
                        "label": f"PdP {n:03d} — {candidate['title']}",
                        "lesson": n, "token": f"m-{year}-{n:03d}",
                        "path": path, "status": "PRATONTON BELUM MUKTAMAD"})
    return entries

def _pjpk_records(year, component):
    if component not in ("PJ", "PK"):
        return []
    from web.pjpk_2027_preview_runtime import MAXIMUM, _source
    short = component.lower()
    entries = []
    for n in range(1, MAXIMUM[short][year] + 1):
        candidate = _source(year, short, n, root=ROOT)
        if candidate is None:
            continue
        title = candidate["title"]
        path = ROOT / "rph_standalone" / "pjpk" / f"year{year}_{short}" / f"lesson_{n:03d}.md"
        if not path.is_file():
            continue
        entries.append({"unit": str(title), "label": f"PdP {n:03d} — {title}",
                        "lesson": n, "token": f"p-{year}-{component}-{n:03d}",
                        "path": path, "status": "PRATONTON BELUM MUKTAMAD"})
    return entries

@lru_cache(maxsize=1)
def _psv_release_approved():
    """Do not release PSV merely because 210 draft source files exist."""
    try:
        from web.psv_2027_rph_release_bridge import _approved
        return _approved(ROOT) is True
    except Exception:
        return False


def _psv_records(year):
    path = ROOT / "rpt_2027" / "psv" / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv"
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            lines = list(csv.DictReader(handle))
        if len(lines) != 42:
            return []
        rows = []
        for n, rec in enumerate(lines, 1):
            if rec.get("PdP") != f"{n:03d}" or rec.get("Tahun") != str(year) or rec.get("Status") not in ("DRAF_SEMAK", "READY"):
                return []
            title = (rec.get("Tajuk/aktiviti PdP") or rec.get("Tajuk karya cadangan") or "").strip()
            unit = (rec.get("Tajuk unit") or rec.get("Tajuk karya cadangan") or "").strip()
            if not title or not unit:
                return []
            approved = rec.get("Status") == "READY" and _psv_release_approved()
            candidate = ROOT / "rph_standalone" / "psv" / f"year{year}" / f"lesson_{n:03d}.md"
            release_path = candidate if approved and candidate.is_file() and not candidate.is_symlink() else None
            rows.append({"unit": unit, "label": f"PdP {n:03d} — {title}",
                         "lesson": n, "token": f"v-{year}-{n:03d}",
                         "path": release_path, "status": "READY" if release_path else "RPH BELUM TERSEDIA"})
        return rows
    except (OSError, ValueError, csv.Error, KeyError):
        return []

def source_records(year, subject, component=None):
    if type(year) is not int or year not in range(2, 7):
        return []
    if subject == "ENGLISH" and component in (None, ""):
        return _english_records(year)
    if subject == "MORAL" and component in (None, ""):
        return _moral_records(year)
    if subject == "PJPK":
        return _pjpk_records(year, component)
    if subject == "PSV" and component in (None, ""):
        return _psv_records(year)
    return []

def unit_options(year, subject, component=None):
    records = source_records(year, subject, component)
    return [{"value": name, "label": name} for name in
            dict.fromkeys(row["unit"] for row in records)]

def pdp_options(year, subject, unit, component=None):
    if not _safe_text(unit):
        raise ValueError("Invalid unit")
    return [{"value": row["token"], "label": row["label"],
             "download_enabled": False, "standalone_rph_verified": False}
            for row in source_records(year, subject, component) if row["unit"] == unit]

def _read_source(row, year, subject):
    path = row.get("path")
    if path is None or not path.is_file() or path.is_symlink():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    if len(text) < 400 or len(text) > 100000:
        return None
    n = row["lesson"]
    if subject == "ENGLISH":
        if not re.search(r"(?m)^# English Year %d [—–-] (?:Standalone RPH [—–-] )?Lesson 0*%d(?:\b|[:—])" % (year, n), text):
            return None
    elif subject == "MORAL":
        if not text.startswith(f"# RPH Pendidikan Moral Tahun {year} — PdP {n:03d}"):
            return None
        if "DRAF" not in text[:200]:
            return None
    elif subject == "PJPK":
        component = row["token"].split("-")[2]
        suffix = "Jasmani" if component == "PJ" else "Kesihatan"
        if not text.startswith(f"# RPH Pendidikan {suffix} Tahun {year} — PdP {n:03d}"):
            return None
        if "DRAF" not in text[:300]:
            return None
    elif subject == "PSV":
        if not text.startswith(f"# RPH Pendidikan Seni Visual Tahun {year} — PdP {n:03d}"):
            return None
        if not re.search(r"(?m)^\*\*Status:\*\*\s*READY\s*$", text):
            return None
    return text

def _fields_from_markdown(raw):
    lines = raw.splitlines()
    result = []
    current_heading = "Maklumat RPH"
    block = []
    def flush():
        if block:
            value = "\n".join(block).strip()
            if value:
                result.append({"label": current_heading, "value": value})
            block.clear()
    ignore_technical_section = False
    for line in lines[1:]:
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            ignore_technical_section = bool(re.match(
                r"^(?:Verified mapping and limits|Original book and audio access|"
                r"Original source access|Jejak audit|Bukti audit|Audit notes|"
                r"Source QA|QA checklist)", current_heading, re.I))
        elif not ignore_technical_section:
            # Do not erase valid Topic, SK/SP or duration when an inline
            # technical status appears at the beginning of a shared line.
            # This is used by English Year 5 standalone sources.
            cleanline = re.sub(
                r"\*\*(?:STATUS|QA(?: status)?|Resource status|Jejak audit|"
                r"Bukti visual buku teks|Non-textbook source rule):?\*\*"
                r"(?:(?!\*\*[^*]{1,90}:\*\*).)*",
                "", line, flags=re.I)
            if cleanline.strip():
                block.append(cleanline.rstrip())
    flush()
    return result

def verified_preview(year, subject, unit, token, component=None):
    """Every selection is bound to a known source catalog row, never an RPT ID guess."""
    if subject not in SUBJECT_LABELS or not _safe_text(unit) or not _safe_text(token, MAX_TOKEN):
        return None
    matching = [row for row in source_records(year, subject, component)
                if row["token"] == token and row["unit"] == unit]
    if len(matching) != 1:
        return None
    row = matching[0]
    if row["path"] is None:
        return None
    if subject == "ENGLISH" and year == 6:
        # Same strict official SOW + overlay source already used by Web's
        # existing Year 6 RPH reader, not a generic RPT template.
        from web.english_y6_rph_2027_http import source_rows, FIELDS
        source = source_rows(row["lesson"])
        if source is None:
            return None
        fields = [{"label": label, "value": str(source.get(key) or "—")}
                  for key, label in FIELDS]
    else:
        raw = _read_source(row, year, subject)
        if raw is None:
            return None
        fields = _fields_from_markdown(raw)
        if not fields:
            return None
    return {"year": year, "subject": subject, "unit": unit,
            "lesson": row["lesson"], "selection": token,
            "title": row["label"], "status": row["status"],
            "fields": fields, "source": "existing-standalone-rph",
            "notice": "Pratonton RPH daripada sumber CikguLaju; pastikan maklumat kelas, aktiviti dan rujukan sesuai sebelum cetak."}

def _selection():
    required = {"year", "subject", "unit", "lesson"}
    extras = {"teacher_class", "teacher_date", "teacher_time"}
    keys = set(request.args)
    if not required.issubset(keys) or not keys.issubset(required | extras | {"component"}):
        raise ValueError("Unexpected selection keys")
    if any(len(request.args.getlist(key)) != 1 for key in keys):
        raise ValueError("Ambiguous selection")
    raw_year = request.args["year"]
    if len(raw_year) != 1 or raw_year not in "123456":
        raise ValueError("Invalid year")
    year = int(raw_year)
    subject, unit, lesson = (request.args[key] for key in ("subject", "unit", "lesson"))
    component = request.args.get("component")
    if subject not in SUBJECT_LABELS or not _safe_text(unit) or not _safe_text(lesson, MAX_TOKEN):
        raise ValueError("Invalid subject or lesson")
    if subject == "PJPK" and component not in ("PJ", "PK"):
        raise ValueError("Missing PJPK component")
    if subject != "PJPK" and component is not None:
        raise ValueError("Unexpected component")
    return year, subject, unit, lesson, component


def _teacher_context():
    """Strictly validated printable fields, never used for authentication or RPH mapping."""
    cls = request.args.get("teacher_class", "")
    dt = request.args.get("teacher_date", "")
    tm = request.args.get("teacher_time", "")
    if any(not isinstance(x, str) for x in (cls, dt, tm)):
        raise ValueError("Invalid printable fields")
    if cls and (len(cls) > 40 or not re.fullmatch(r"[\w .\-/()]+", cls, re.UNICODE)
                or not cls.strip()):
        raise ValueError("Invalid class")
    if dt:
        if len(dt) != 10 or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", dt):
            raise ValueError("Invalid date")
        parsed = date.fromisoformat(dt)
        if not 2025 <= parsed.year <= 2031:
            raise ValueError("Date outside supported range")
    if tm:
        if not re.fullmatch(r"\d{2}:\d{2}(?:\s*-\s*\d{2}:\d{2})?", tm):
            raise ValueError("Invalid time")
        import datetime
        for piece in re.split(r"\s*-\s*", tm):
            datetime.datetime.strptime(piece, "%H:%M")
    return {"class": cls.strip(), "date": dt, "time": tm}


def _docx(data):
    """Word and browser print use the same Telegram three-table RPH layout."""
    from web.rph_table_layout import build_rph_table_docx
    return build_rph_table_docx(data, SUBJECT_LABELS)


def create_blueprint():
    bp = Blueprint("unified_rph_preview", __name__)

    @bp.after_request
    def no_cache(resp):
        resp.headers["Cache-Control"] = "no-store, private"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Vary"] = "Cookie"
        return resp

    def selected_rph():
        account, error = _account()
        if error is not None:
            return None, error
        if not _has_paid_access(account):
            return None, (jsonify({"error": "Pratonton RPH Web memerlukan Rakan Pembangun atau langganan aktif; 10 janaan percuma kekal melalui Telegram"}), 403)
        try:
            year, subject, unit, token, component = _selection()
            teacher = _teacher_context()
        except (ValueError, TypeError):
            return None, (jsonify({"error": "Pilihan Tahun/Subjek/Unit/PdP tidak sah"}), 400)
        result = verified_preview(year, subject, unit, token, component)
        if result is None:
            return None, (jsonify({"error": "RPH tepat untuk Lesson/PdP ini belum tersedia di Web. Tiada RPH generik atau daripada tajuk lain digunakan.",
                                   "code": "RPH_SOURCE_NOT_VERIFIED"}), 503)
        from web.rph_shared_source_identity import source_fingerprint
        # Verify exact source/mapping bytes again at request time; the native
        # Telegram endpoint checks this same fingerprint against its own tree.
        digest = source_fingerprint(year, subject, result["lesson"], component)
        if digest is None:
            return None, (jsonify({"error": "RPH tidak dapat disahkan dengan sumber Telegram.",
                                   "code": "RPH_SOURCE_NOT_VERIFIED"}), 503)
        result["source_digest"] = digest
        result["teacher"] = teacher
        try:
            from web.telegram_rph_parity import build_layout
            result["telegram_layout"] = build_layout(result, SUBJECT_LABELS)
        except (ValueError, TypeError, KeyError):
            return None, (jsonify({
                "error": "Format RPH bagi Lesson/PdP ini belum lengkap. Sila pilih Lesson/PdP lain.",
                "code": "RPH_TELEGRAM_LAYOUT_INCOMPLETE"}), 503)
        return result, None

    @bp.get("/api/web/rph/availability")
    def availability():
        """Confirm a selected, paid RPH has a complete source-backed layout.

        This is a lightweight readiness check, not a preview: never send
        teaching content, server-side source paths, or download tokens.
        The real Word/PDF routes repeat all checks when the user downloads.
        """
        selected, err = selected_rph()
        if err is not None:
            return err
        return jsonify({"available": True, "generator": "telegram-native"})

    @bp.get("/api/web/rph/preview")
    def preview():
        selected, err = selected_rph()
        return err if err is not None else jsonify(selected)

    def _native_document(selected, fmt):
        """Use actual Telegram document generator, never Web's mock renderer."""
        from web.native_telegram_rph_client import request_native_rph, NativeRPHUnavailable
        try:
            return request_native_rph(selected, fmt), None
        except (NativeRPHUnavailable, ValueError):
            return None, (jsonify({
                "error": "Penjana RPH Telegram belum dapat dihubungi. Pilihan guru dikekalkan; cuba semula.",
                "code": "TELEGRAM_RPH_GENERATOR_UNAVAILABLE"
            }), 503)

    @bp.get("/api/web/rph/word")
    def word():
        selected, err = selected_rph()
        if err is not None:
            return err
        document, error = _native_document(selected, "word")
        if error is not None:
            return error
        filename = f"CIKGULAJU_RPH_{selected['subject']}_TAHUN_{selected['year']}_{selected['lesson']:03d}.docx"
        response = send_file(document,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,download_name=filename,conditional=False)
        response.headers["X-RPH-Generator"] = "telegram-native"
        return response

    @bp.get("/api/web/rph/pdf")
    def pdf():
        selected, err = selected_rph()
        if err is not None:
            return err
        document, error = _native_document(selected, "pdf")
        if error is not None:
            return error
        filename = f"CIKGULAJU_RPH_{selected['subject']}_TAHUN_{selected['year']}_{selected['lesson']:03d}.pdf"
        response = send_file(document,mimetype="application/pdf",
            as_attachment=True,download_name=filename,conditional=False)
        response.headers["X-RPH-Generator"] = "telegram-native"
        return response

    return bp
