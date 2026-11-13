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

from flask import Blueprint, g, jsonify, request, send_file

from web.english_rpt_2027_http import _account, _has_paid_access
from web.rph_teacher_reflection import clean_reflection

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
    "SEJARAH": "Sejarah",
    "RBT": "Reka Bentuk dan Teknologi",
    "ARAB": "Bahasa Arab",
    "MUZIK": "Pendidikan Muzik",
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

@lru_cache(maxsize=1000)
def _english_page_reference(path):
    """Read only source-stated Student's/Pupil's Book pages; never derive them
    from a Lesson number, unit name, or a PDF page offset.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    refs = []
    for match in re.finditer(
        r"\b(?:Student(?:'s|’s)?\s+Book|Pupil(?:'s|’s)?\s+Book|SB|PB)\s+"
        r"pp?\.\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?",
        content, re.I,
    ):
        start, end = int(match[1]), int(match[2] or match[1])
        if not 0 < start <= end <= 1000:
            continue
        label = str(start) + ("–" + str(end) if start != end else "")
        if label not in refs:
            refs.append(label)
    # Multiple references can be valid, but avoid potentially misleading
    # catch-all pages when a draft mentions many different activities.
    return "Student's Book m/s " + ", ".join(refs) if 0 < len(refs) <= 3 else ""


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
        record = {"unit": topic, "label": f"Lesson {n:03d} — {focus or topic}",
                  "lesson": n, "token": f"e-{year}-{n:03d}",
                  "path": path, "status": "PRATONTON BELUM MUKTAMAD"}
        textbook_ref = _english_page_reference(path)
        if textbook_ref:
            record["textbook_ref"] = textbook_ref
        result.append(record)
    # Normalize differences in SOW Unit letter case and whitespace only.
    # This keeps every original Lesson ID, text, token and file unchanged.
    canonical = {}
    for item in result:
        source_label = " ".join(item["unit"].split())
        item["unit"] = canonical.setdefault(source_label.casefold(), source_label)
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

# PJ only: the existing 2027 339-PdP source stores one *lesson title* per
# manifest row, NOT a canonical unit title. Group the unchanged PdP sequence
# against the printed PJ textbook unit contents (Years 2–6). Each tuple is
# (last inclusive PdP, printed unit number, printed unit title). Some units
# have no drafted PdP and must not be invented in the menu.
# The original RPH, SK/SP, page reference, and PdP token remain untouched.
PJ_TEXTBOOK_UNIT_SEGMENTS = {
    2: ((2, 1, "Cabaran Ruang"), (17, 2, "Mari Bersenam"),
        (19, 3, "Senamrobik"), (27, 4, "Sarkas"),
        (29, 6, "Santai Ria"), (30, 7, "Semangat Membara"),
        (37, 8, "Larian Cergas")),
    3: ((4, 1, "Gimnas Gemilang"), (6, 2, "Langkah Berirama"),
        (9, 3, "Serang Sampai Menang"), (13, 4, "Semangat Berjuang"),
        (16, 5, "Hebat Balingan, Hebat Pukulan"),
        (21, 6, "Olahragawan Harapan"), (23, 7, "Keyakinan di Air"),
        (28, 8, "Ceria dan Sihat"), (30, 9, "Cergas Teratur"),
        (38, 10, "Jom Senam untuk Sihat")),
    4: ((7, 1, "Gerak Gimnas"), (8, 2, "Gerak Kreatif Bertema"),
        (12, 3, "Johan Kategori Serangan"), (16, 4, "Sedia Bertarung"),
        (18, 5, "Pemukul Hebat Pemadang Cekap"),
        (24, 6, "Mengejar Juara"), (26, 7, "Keselamatan Diutamakan"),
        (28, 8, "Rekreasi Berilmu"), (34, 9, "Kecergasan Diri")),
    5: ((8, 1, "Jadi Yang Terbaik"), (10, 2, "Riang Ria di Dasar Lautan"),
        (14, 3, "Serang Menang"), (17, 4, "Handal Jaring"),
        (21, 5, "Rondas Kampung"), (27, 6, "Olahraga Asas"),
        (31, 8, "Permainan Warisan"), (32, 9, "Cergas Selalu"),
        (33, 10, "Cergas dan Sihat")),
    6: ((7, 1, "Gimnastik Asas"), (9, 2, "Pergerakan Berirama"),
        (12, 3, "Kategori Serangan"), (15, 4, "Kategori Jaring"),
        (19, 5, "Kategori Pukul dan Memadang"),
        (25, 6, "Olahraga Asas"), (28, 8, "Cabaran Rekreasi"),
        (29, 9, "Konsep Kecergasan"), (34, 10, "Kekal Aktif")),
}


def _pj_canonical_unit(year, pdp):
    """Return a published textbook unit, never an individual RPH title."""
    for last_pdp, number, title in PJ_TEXTBOOK_UNIT_SEGMENTS.get(year, ()):
        if pdp <= last_pdp:
            return f"Unit {number}: {title}"
    return None


def _pj_activity_title(title):
    """Move the title after an embedded UNIT prefix into the PdP choice."""
    if re.match(r"(?i)^\s*UNIT\s+\d+\b", title):
        found = re.search(r"(?i)\bTAJUK\s*:?\s*", title)
        if found and title[found.end():].strip():
            return title[found.end():].strip(" |:-")
    return title


# Pendidikan Kesihatan has nine DSKP domains, not one Unit per lesson.
# The RPT manifest contains separate *activity* titles for every PdP. Group
# choices by their actual SK domain, retaining every original lesson/title.
# Label as Bidang rather than inventing textbook Unit names.
PK_DSKP_DOMAINS = {
    1: "Pendidikan Kesihatan Reproduktif dan Sosial (PEERS)",
    2: "Penyalahgunaan Bahan",
    3: "Pengurusan Mental dan Emosi",
    4: "Kekeluargaan",
    5: "Perhubungan",
    6: "Penyakit",
    7: "Keselamatan",
    8: "Pemakanan",
    9: "Pertolongan Cemas",
}


def _pk_domain(candidate):
    sk_codes = candidate.get("sk")
    if not isinstance(sk_codes, list) or not sk_codes:
        return None
    domains = set()
    for code in sk_codes:
        match = re.fullmatch(r"([1-9])\.\d{1,2}", str(code or "").strip())
        if match is None:
            return None
        domains.add(int(match[1]))
    if len(domains) != 1:
        return None
    number = domains.pop()
    return f"Bidang {number}: {PK_DSKP_DOMAINS[number]}"


def _pjpk_records(year, component):
    if component not in ("PJ", "PK"):
        return []
    from web.pjpk_2027_preview_runtime import MAXIMUM, _source
    short = component.lower()
    entries = []
    if component == "PJ" and (
            not PJ_TEXTBOOK_UNIT_SEGMENTS.get(year)
            or PJ_TEXTBOOK_UNIT_SEGMENTS[year][-1][0] != MAXIMUM["pj"][year]):
        return []
    for n in range(1, MAXIMUM[short][year] + 1):
        candidate = _source(year, short, n, root=ROOT)
        if candidate is None:
            continue
        title = candidate["title"]
        path = ROOT / "rph_standalone" / "pjpk" / f"year{year}_{short}" / f"lesson_{n:03d}.md"
        if not path.is_file():
            continue
        unit = (_pj_canonical_unit(year, n) if component == "PJ"
                else _pk_domain(candidate))
        if not unit:
            continue
        activity = _pj_activity_title(title) if component == "PJ" else title
        entries.append({"unit": unit, "label": f"PdP {n:03d} — {activity}",
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
    if type(year) is int and year == 1 and subject == "ENGLISH" and component in (None, ""):
        from web.english_y1_kssr_rph import PLANS, UNIT
        return [
            {"unit": UNIT, "label": plan.title, "lesson": number,
             "token": f"e-1-{number:03d}", "status": "KSSR SEMAKAN 2017",
             "textbook_ref": plan.textbook_ref, "fields": plan.fields()}
            for number, plan in PLANS.items()
        ]
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
    choices = []
    for row in source_records(year, subject, component):
        if row["unit"] != unit:
            continue
        entry = {"value": row["token"], "label": row["label"],
                 "download_enabled": False, "standalone_rph_verified": False,
                 "lesson_no": row["lesson"]}
        if row.get("textbook_ref"):
            entry["textbook_ref"] = row["textbook_ref"]
        choices.append(entry)
    return choices

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
    if subject == "ENGLISH" and year == 1:
        fields = row["fields"]
    elif row["path"] is None:
        return None
    elif subject == "ENGLISH" and year == 6:
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
    extras = {"teacher_class", "teacher_date", "teacher_time",
              "teacher_start", "teacher_end", "teacher_students"}
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
    """Strict printable teacher fields; no change to auth, Lesson or payment."""
    cls = request.args.get("teacher_class", "")
    dt = request.args.get("teacher_date", "")
    old_time = request.args.get("teacher_time", "")
    start = request.args.get("teacher_start", "")
    end = request.args.get("teacher_end", "")
    students = request.args.get("teacher_students", "")
    if any(not isinstance(x, str) for x in (cls, dt, old_time, start, end, students)):
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

    def valid_clock(value):
        return bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value))

    # Existing clients still use teacher_time; new clients must supply both
    # start/end. Do not silently accept a single endpoint or inverted times.
    if old_time and (start or end):
        raise ValueError("Ambiguous time fields")
    if start or end:
        if not (valid_clock(start) and valid_clock(end) and start < end):
            raise ValueError("Start/end time must be a valid increasing range")
        tm = start + " - " + end
    else:
        tm = old_time
        if tm:
            parts = re.split(r"\s*-\s*", tm)
            if len(parts) not in (1, 2) or not all(valid_clock(piece) for piece in parts):
                raise ValueError("Invalid time")
            if len(parts) == 2:
                if parts[0] >= parts[1]:
                    raise ValueError("Invalid time range")
                tm = parts[0] + " - " + parts[1]
    if students:
        if not re.fullmatch(r"[1-9][0-9]{0,2}", students) or not 1 <= int(students) <= 200:
            raise ValueError("Invalid number of pupils")
    return {"class": cls.strip(), "date": dt, "time": tm, "students": students}


def _fill_roster_count(teacher, account):
    if teacher["students"] or not teacher["class"]:
        return
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from web.pbd_store import StorageError, roster_count, scope
    from web_v1_telegram_auth_routes import _config

    conf = _config()
    uid = account.get("telegram_user_id")
    if not conf or conf.get("account_backend") != "supabase" or type(uid) is not int or uid <= 0:
        return
    school_year = (date.fromisoformat(teacher["date"]).year if teacher["date"]
                   else datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).year)
    try:
        count = roster_count(conf, uid, scope(teacher["class"], school_year))
    except StorageError:
        return
    if 1 <= count <= 200:
        teacher["students"] = str(count)


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

    def selected_rph(*, require_generation_access=True, for_download=False):
        """Authenticate every request; check quota only for actual paid/trial
        preview and document generation, not read-only source availability.
        No RPH content or file bytes leave the availability endpoint.
        """
        account, error = _account()
        if error is not None:
            return None, error
        # Free RPH uses the *same* ten-credit Supabase balance as Telegram.
        # A paid account is unlimited; a trial account needs a verified,
        # strictly typed positive balance. Do not provision credits here.
        paid = _has_paid_access(account)
        credits = account.get("free_remaining") if isinstance(account, dict) else None
        if require_generation_access and not paid and (type(credits) is not int or not 0 <= credits <= 10):
            return None, (jsonify({
                "error": "Baki janaan percuma belum dapat disahkan. Cuba Refresh.",
                "code": "RPH_TRIAL_BALANCE_UNAVAILABLE"}), 503)
        if require_generation_access and not paid and credits == 0:
            return None, (jsonify({
                "error": "10 janaan RPH percuma telah habis. Aktifkan Rakan Pembangun untuk akses tanpa had.",
                "code": "FREE_TRIAL_EXHAUSTED", "remaining": 0}), 403)
        # Never add account/payment details to a returned preview JSON or
        # the server-to-server native Telegram document payload.
        g.cikgulaju_rph_account = account
        g.cikgulaju_rph_paid = paid
        try:
            year, subject, unit, token, component = _selection()
            teacher = _teacher_context()
        except (ValueError, TypeError):
            return None, (jsonify({"error": "Pilihan Tahun/Subjek/Unit/PdP tidak sah"}), 400)
        if for_download and request.method == "POST":
            body = request.get_json(silent=True) if (
                request.is_json and 0 < (request.content_length or 0) <= 8192
            ) else None
            try:
                if not isinstance(body, dict) or set(body) != {"reflection"}:
                    raise ValueError("Invalid reflection request")
                reflection = clean_reflection(body["reflection"])
            except ValueError:
                return None, (jsonify({
                    "error": "Semak refleksi. Hadnya 500 aksara dan 6 baris.",
                    "code": "INVALID_RPH_REFLECTION",
                }), 400)
            if reflection:
                teacher["reflection"] = reflection
        if for_download:
            _fill_roster_count(teacher, account)
        # BM's REAL Telegram flow uses verified_pdp_sequence, NOT rpt_entries.
        # Never reinterpret an opaque BM PdP token as an RPT row ID.
        if subject == "BM":
            from web.native_telegram_bm_rph_client import (
                verified_native_bm_available, NativeRPHUnavailable,
            )
            try:
                verified_native_bm_available(year, unit, token)
            except (NativeRPHUnavailable, ValueError):
                return None, (jsonify({
                    "error": "PdP Bahasa Melayu belum dapat disahkan menggunakan sumber Telegram sebenar.",
                    "code": "TELEGRAM_NATIVE_BM_RPH_NOT_READY",
                }), 503)
            return {
                "source": "telegram-native-bm-pdp",
                "year": year, "subject": subject, "unit": unit,
                "lesson": token, "teacher": teacher,
            }, None
        # Pendidikan Islam still resolves its own exact native master RPT row.
        if subject == "PI":
            from web.native_verified_rpt_rph_client import (
                verified_rpt_available, NativeRPHUnavailable,
            )
            try:
                verified_rpt_available(year, subject, unit, token)
            except (NativeRPHUnavailable, ValueError):
                return None, (jsonify({
                    "error": "RPH subjek ini belum boleh disahkan daripada RPT utama Telegram bagi PdP dipilih.",
                    "code": "TELEGRAM_RPT_RPH_NOT_READY",
                }), 503)
            return {
                "source": "telegram-verified-rpt-master",
                "year": year, "subject": subject, "unit": unit,
                "lesson": int(token), "teacher": teacher,
            }, None
        if subject in ("MATH", "SCIENCE"):
            from web.native_telegram_sequence_rph_client import (
                verified_native_sequence_available, NativeRPHUnavailable,
            )
            try:
                verified_native_sequence_available(year, subject, unit, token)
            except (NativeRPHUnavailable, ValueError):
                return None, (jsonify({
                    "error": "PdP Sains/Matematik belum dapat disahkan dengan enjin RPH Telegram.",
                    "code": "TELEGRAM_NATIVE_PDP_RPH_NOT_READY",
                }), 503)
            return {
                "source": "telegram-native-pdp-sequence",
                "year": year, "subject": subject, "unit": unit,
                "lesson": token, "teacher": teacher,
            }, None
        if subject == "RBT":
            if year not in (4,5,6) or component not in (None,""):
                return None,(jsonify({"error":"RBT untuk Tahun 4–6 sahaja"}),400)
            from web.native_telegram_rbt_2027_client import (
                rbt_available,NativeRPHUnavailable,
            )
            try:
                rbt_available(year,unit,token)
            except (NativeRPHUnavailable,ValueError):
                return None,(jsonify({
                    "error":"Sumber RBT Unit/PdP ini belum aktif dalam Telegram.",
                    "code":"TELEGRAM_RBT_SOURCE_UNAVAILABLE",
                }),503)
            return {
                "source":"telegram-native-rbt-2027",
                "year":year,"subject":subject,"unit":unit,
                "lesson":token,"teacher":teacher,
                "status":"DRAF UNTUK SEMAKAN GURU",
            },None
        if subject == "SEJARAH":
            if year not in (4,5,6) or component not in (None, ""):
                return None, (jsonify({"error":"Sejarah tersedia untuk Tahun 4–6 sahaja"}),400)
            from web.native_telegram_sejarah_2027_client import (
                sejarah_available, NativeRPHUnavailable,
            )
            try:
                sejarah_available(year, unit, token)
            except (NativeRPHUnavailable, ValueError):
                return None, (jsonify({
                    "error": "Sumber RPH Sejarah untuk Unit/PdP ini belum aktif pada Telegram.",
                    "code": "TELEGRAM_SEJARAH_SOURCE_UNAVAILABLE",
                }), 503)
            return {
                "source": "telegram-native-sejarah-2027",
                "year": year, "subject": subject,
                "unit": unit, "lesson": token, "teacher": teacher,
                "status": "DRAF CADANGAN",
            }, None
        if subject in ("ARAB", "MUZIK"):
            if year not in range(2, 7) or component not in (None, ""):
                return None, (jsonify({"error":"Subjek ini hanya tersedia untuk Tahun 2–6"}),400)
            from web.native_telegram_other_draft_client import (
                draft_available, NativeRPHUnavailable,
            )
            try:
                formats = draft_available(year, subject, unit, token)
            except (NativeRPHUnavailable, ValueError):
                return None, (jsonify({
                    "error":"RPH DRAF belum boleh disahkan dengan sumber asal Telegram.",
                    "code":"TELEGRAM_OTHER_DRAFT_SOURCE_UNAVAILABLE",
                }),503)
            return {
                "source":"telegram-provisional-subjects-2027",
                "year":year,"subject":subject,"unit":unit,
                "lesson":token,"teacher":teacher,
                "status":"DRAF UNTUK SEMAKAN GURU",
                "formats":list(formats),
            },None
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
        # Telegram's Year 5 standalone bridge is explicitly release-gated.
        # Until a Lesson is approved there, Web must not generate its draft as
        # though it were the same plan delivered in the Telegram bot.
        if subject == "ENGLISH" and year == 5:
            from web.english_y5_standalone_runtime import approved_for_telegram
            if not approved_for_telegram(result["lesson"]):
                return None, (jsonify({
                    "error": "RPH English Year 5 ini belum diluluskan untuk penjana Telegram. Tiada RPH berbeza digunakan di Web.",
                    "code": "TELEGRAM_RPH_PARITY_NOT_READY"
                }), 503)
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
        selected, err = selected_rph(require_generation_access=False)
        if err is not None:
            return err
        # This endpoint only confirms SOURCE readiness to the authenticated
        # account. It does not release material, alter quota or bypass payment.
        account = g.cikgulaju_rph_account
        credits = account.get("free_remaining")
        paid = bool(g.cikgulaju_rph_paid)
        valid_credits = type(credits) is int and 0 <= credits <= 10
        allowed = paid or (valid_credits and credits > 0)
        access = ("paid" if paid else
                  "trial" if valid_credits and credits > 0 else
                  "exhausted" if valid_credits and credits == 0 else
                  "unavailable")
        result={"available": True, "generator": "telegram-native",
                "download_allowed": allowed, "access_status": access}
        # Preserve the existing JSON contract for English/BM/PI/other users.
        # Publish DRAF and format restrictions only for the new subjects.
        if selected.get("source")=="telegram-native-rbt-2027":
            result.update({"status":selected["status"],"formats":["word","pdf"]})
        if selected.get("source")=="telegram-provisional-subjects-2027":
            result.update({"status": selected["status"],
                           "formats": selected["formats"]})
        return jsonify(result)

    @bp.get("/api/web/rph/pbd-context")
    def pbd_context():
        """Reuse only the assessment fields from an accessible RPH preview."""
        selected, err = selected_rph(require_generation_access=False)
        if err is not None:
            return err
        if not g.cikgulaju_rph_paid:
            return jsonify({})
        header = {item["label"]: item["value"]
                  for item in selected.get("telegram_layout", {}).get("header", [])}
        def field(*labels, limit):
            return " / ".join(header[label] for label in labels
                              if header.get(label) not in (None, "", "—"))[:limit]
        return jsonify({
            "sk": field("Main Content Standard", "Complementary Content Standard",
                        "Standard Kandungan", limit=200),
            "sp": field("Main Learning Standard", "Complementary Learning Standard",
                        "Standard Pembelajaran", limit=200),
            "criteria1": field("Assessment", "Pentaksiran", limit=450),
        })

    @bp.get("/api/web/rph/preview")
    def preview():
        selected, err = selected_rph()
        if err is not None:
            return err
        # Full RPH source JSON is a complete teaching artifact. A free
        # user must not bypass the one-use trial charge by reading preview.
        if not g.cikgulaju_rph_paid:
            return jsonify({
                "error": "Pratonton penuh bukan sebahagian percubaan. Gunakan Jana RPH Word atau PDF.",
                "code": "TRIAL_PREVIEW_UNAVAILABLE"}), 403
        return jsonify(selected)

    def _native_document(selected, fmt):
        """Render via Telegram first; charge trial atomically only afterwards.

        A failed renderer/invalid file never spends a credit. An authenticated
        paid user never spends credits. No browser may choose a quota reference.
        """
        from web.native_telegram_rph_client import request_native_rph, NativeRPHUnavailable
        try:
            if selected.get("source") == "telegram-native-bm-pdp":
                from web.native_telegram_bm_rph_client import request_native_bm_rph
                document = request_native_bm_rph(selected, fmt)
            elif selected.get("source") == "telegram-verified-rpt-master":
                from web.native_verified_rpt_rph_client import request_verified_rpt_rph
                document = request_verified_rpt_rph(selected, fmt)
            elif selected.get("source") == "telegram-native-rbt-2027":
                from web.native_telegram_rbt_2027_client import request_rbt_rph
                document=request_rbt_rph(selected,fmt)
            elif selected.get("source") == "telegram-native-sejarah-2027":
                from web.native_telegram_sejarah_2027_client import request_sejarah_rph
                document = request_sejarah_rph(selected, fmt)
            elif selected.get("source") == "telegram-provisional-subjects-2027":
                from web.native_telegram_other_draft_client import request_draft_rph
                if fmt not in selected.get("formats", ()):
                    return None, (jsonify({
                        "error":"Format RPH DRAF ini belum diluluskan untuk muat turun.",
                        "code":"DRAFT_RPH_FORMAT_NOT_VERIFIED",
                    }),503), None
                document = request_draft_rph(selected, fmt)
            elif selected.get("source") == "telegram-native-pdp-sequence":
                from web.native_telegram_sequence_rph_client import request_native_sequence_rph
                document = request_native_sequence_rph(selected, fmt)
            else:
                document = request_native_rph(selected, fmt)
        except (NativeRPHUnavailable, ValueError):
            return None, (jsonify({
                "error": "Penjana RPH Telegram belum dapat dihubungi. Pilihan guru dikekalkan; cuba semula.",
                "code": "TELEGRAM_RPH_GENERATOR_UNAVAILABLE"
            }), 503), None
        # Matematik only: check clear defects in the REAL Telegram Word/PDF
        # before either paid delivery or a free-trial credit debit. Never
        # invent an objective, alter a source SK/SP, or change other subjects.
        if (selected.get("source") == "telegram-native-pdp-sequence"
                and selected.get("subject") == "MATH"):
            from web.math_rph_delivery_quality_20261110 import (
                MathQualityReadError, inspect_math_rph_document,
            )
            try:
                quality = inspect_math_rph_document(
                    selected, fmt, document.getvalue())
            except MathQualityReadError:
                return None, (jsonify({
                    "error": "Kualiti fail RPH Matematik tidak dapat disemak. Kredit percubaan tidak digunakan.",
                    "code": "MATH_RPH_QUALITY_CHECK_UNAVAILABLE",
                }), 503), None
            if quality["issues"]:
                return None, (jsonify({
                    "error": "RPH Matematik ini memerlukan pembetulan sebelum boleh dimuat turun. Kredit percubaan tidak digunakan.",
                    "code": "MATH_RPH_QUALITY_REVIEW_REQUIRED",
                }), 503), None
        if g.cikgulaju_rph_paid:
            return document, None, None
        from web.rph_delivery_quota import authorize_rendered_document
        from web_v1_telegram_auth_routes import _config
        config = _config()
        if not config or config.get("account_backend") != "supabase":
            return None, (jsonify({
                "error": "Sambungan baki janaan percuma belum tersedia.",
                "code": "RPH_TRIAL_SOURCE_UNAVAILABLE"}), 503), None
        account = g.cikgulaju_rph_account
        try:
            charged = authorize_rendered_document(
                account, account["telegram_user_id"], document.getvalue(),
                config["supabase_url"], config["supabase_key"])
        except Exception:
            # A transport timeout can be an uncertain RPC result, so do not
            # claim the balance was unchanged or automatically retry a debit.
            return None, (jsonify({
                "error": "Pengesahan baki janaan tidak berjaya. Refresh status akaun sebelum cuba lagi.",
                "code": "RPH_TRIAL_CHARGE_UNCONFIRMED"}), 503), None
        if not charged["allowed"]:
            return None, (jsonify({
                "error": "Baki janaan RPH percuma telah habis. Aktifkan Rakan Pembangun untuk akses tanpa had.",
                "code": "FREE_TRIAL_EXHAUSTED",
                "remaining": charged["remaining"]}), 403), None
        return document, None, charged["remaining"]

    @bp.route("/api/web/rph/word", methods=["GET", "POST"])
    def word():
        selected, err = selected_rph(for_download=True)
        if err is not None:
            return err
        document, error, trial_remaining = _native_document(selected, "word")
        if error is not None:
            return error
        lesson_tag = (f"{selected['lesson']:03d}" if type(selected["lesson"]) is int
                      else re.sub(r"[^A-Za-z0-9_-]", "_", selected["lesson"])[:80])
        filename = f"CIKGULAJU_RPH_{selected['subject']}_TAHUN_{selected['year']}_{lesson_tag}.docx"
        response = send_file(document,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,download_name=filename,conditional=False)
        response.headers["X-RPH-Generator"] = "telegram-native"
        response.headers["X-RPH-Access-Mode"] = (
            "paid" if g.cikgulaju_rph_paid else "trial")
        if trial_remaining is not None:
            response.headers["X-RPH-Trial-Remaining"] = str(trial_remaining)
        return response

    @bp.route("/api/web/rph/pdf", methods=["GET", "POST"])
    def pdf():
        selected, err = selected_rph(for_download=True)
        if err is not None:
            return err
        document, error, trial_remaining = _native_document(selected, "pdf")
        if error is not None:
            return error
        lesson_tag = (f"{selected['lesson']:03d}" if type(selected["lesson"]) is int
                      else re.sub(r"[^A-Za-z0-9_-]", "_", selected["lesson"])[:80])
        filename = f"CIKGULAJU_RPH_{selected['subject']}_TAHUN_{selected['year']}_{lesson_tag}.pdf"
        response = send_file(document,mimetype="application/pdf",
            as_attachment=True,download_name=filename,conditional=False)
        response.headers["X-RPH-Generator"] = "telegram-native"
        response.headers["X-RPH-Access-Mode"] = (
            "paid" if g.cikgulaju_rph_paid else "trial")
        if trial_remaining is not None:
            response.headers["X-RPH-Trial-Remaining"] = str(trial_remaining)
        return response

    # Extra teaching resources are independent of RPH generation credits.
    # Selection is still bound to the exact logged-in user's source catalog.
    # The Web never guesses an RPT ID, exposes Telegram credentials or
    # copies files from an unsynchronized Web-side legacy database.
    def _extra_selection():
        if set(request.args) != {"year", "subject", "unit", "lesson"}:
            raise ValueError("Unexpected extra resource selection")
        year, sub, unit, lesson, component = _selection()
        if component is not None:
            raise ValueError("Unsupported extra resource component")
        if sub == "ENGLISH" and year in range(2, 7):
            found = [row for row in source_records(year, sub)
                     if row["unit"] == unit and row["token"] == lesson]
            if len(found) != 1:
                raise ValueError("English Lesson identity mismatch")
            return year, sub, unit, lesson, found[0]["lesson"]
        if sub == "MUZIK" and year in range(2, 7):
            return year, sub, unit, lesson, None
        raise ValueError("No verified source for optional resources")

    @bp.get("/api/web/rph/extra-materials")
    def extra_materials():
        account, error = _account()
        if error is not None:
            return error
        try:
            year, sub, unit, token, number = _extra_selection()
        except (ValueError, TypeError):
            return jsonify({"items": [], "status": "BELUM_TERSEDIA"})
        try:
            from web.native_telegram_extra_materials_20261106 import (
                english_workbook_metadata, music_source_links,
                english_student_book_metadata, english_audio_tracks,
            )
            if sub == "ENGLISH":
                from urllib.parse import urlencode
                params = urlencode({"year": year, "subject": sub,
                                    "unit": unit, "lesson": token})
                items, missing = [], []
                # Each verified Workbook uses the existing Telegram route.
                try:
                    label = english_workbook_metadata(year, number)
                    if label:
                        items.append({"type": "workbook", "title": label,
                                      "url": "/api/web/rph/english-workbook?" + params,
                                      "action": "Download"})
                except Exception:
                    missing.append("Workbook")
                if year in (2, 3, 4):
                    # The additional APIs are optional until Telegram deploys
                    # them. A missing new route must not hide existing Workbook.
                    try:
                        label = english_student_book_metadata(year, number)
                        if label:
                            items.insert(0, {"type": "textbook", "title": label,
                                             "url": "/api/web/rph/english-student-book?" + params,
                                             "action": "Download"})
                    except Exception:
                        missing.append("Student Book")
                    try:
                        tracks = english_audio_tracks(year, number)
                        for track in tracks:
                            items.append({
                                "type": "audio", "title": track["title"],
                                "url": "/api/web/rph/english-audio/" +
                                       str(track["index"]) + "?" + params,
                                "action": "Download",
                            })
                    except Exception:
                        missing.append("Audio")
                if missing and not items:
                    return jsonify({"items": [], "error":
                                    "Sumber bahan English Telegram belum dapat disahkan."}), 503
                note = ("Bahan mengikut halaman dan trek Lesson asal; tiada janaan RPH digunakan."
                        + (" Sumber lain belum dapat disahkan: " + ", ".join(missing)
                           if missing else ""))
                return jsonify({"items": items, "status": "SUMBER_ASAL", "note": note})
            # Music intentionally remains original-owner VIEW links only.
            items = music_source_links(year, unit, token)
        except Exception:
            return jsonify({"items": [], "error":
                            "Sumber bahan tambahan Telegram belum dapat disahkan."}), 503
        return jsonify({"items": items, "status": "SUMBER_ASAL",
                        "note": "Pautan audio luar: akses, kandungan dan hak edar belum disahkan."})

    @bp.get("/api/web/rph/english-workbook")
    def english_workbook():
        account, error = _account()
        if error is not None:
            return error
        try:
            year, sub, unit, token, number = _extra_selection()
            if sub != "ENGLISH":
                raise ValueError("Wrong resource")
        except (ValueError, TypeError):
            return jsonify({"error": "Pilihan Lesson Buku Aktiviti tidak sah"}), 400
        try:
            from web.native_telegram_extra_materials_20261106 import english_workbook_pdf
            content = english_workbook_pdf(year, number)
        except Exception:
            return jsonify({"error": "Fail Buku Aktiviti dari Telegram belum tersedia"}), 503
        return send_file(BytesIO(content), mimetype="application/pdf",
                         as_attachment=True, conditional=False,
                         download_name=f"CikguLaju_English_Y{year}_Lesson_{number:03d}_Workbook.pdf")

    @bp.get("/api/web/rph/english-student-book")
    def english_student_book():
        account, error = _account()
        if error is not None:
            return error
        try:
            year, sub, unit, token, number = _extra_selection()
            if sub != "ENGLISH" or year not in (2, 3, 4):
                raise ValueError("Wrong Student Book source")
        except (ValueError, TypeError):
            return jsonify({"error": "Pilihan Student Book tidak sah"}), 400
        try:
            from web.native_telegram_extra_materials_20261106 import english_student_book_pdf
            data = english_student_book_pdf(year, number)
        except Exception:
            return jsonify({"error": "Halaman Student Book belum tersedia"}), 503
        return send_file(BytesIO(data), mimetype="application/pdf",
                         as_attachment=True, conditional=False,
                         download_name=f"CikguLaju_English_Y{year}_Lesson_{number:03d}_Student_Book.pdf")

    @bp.get("/api/web/rph/english-audio/<int:track>")
    def english_audio(track):
        account, error = _account()
        if error is not None:
            return error
        try:
            year, sub, unit, token, number = _extra_selection()
            if sub != "ENGLISH" or year not in (2, 3, 4) or not 1 <= track <= 4:
                raise ValueError("Invalid track")
        except (ValueError, TypeError):
            return jsonify({"error": "Pilihan trek audio tidak sah"}), 400
        try:
            from web.native_telegram_extra_materials_20261106 import english_audio_mp3, english_audio_wma
            if year == 2:
                data = english_audio_wma(number, track)
                mime, extension = "audio/x-ms-wma", "wma"
            else:
                data = english_audio_mp3(year, number, track)
                mime, extension = "audio/mpeg", "mp3"
        except Exception:
            return jsonify({"error": "Trek audio belum disahkan atau tidak tersedia"}), 503
        return send_file(BytesIO(data), mimetype=mime,
                         as_attachment=True, conditional=False,
                         download_name=f"CikguLaju_English_Y{year}_Lesson_{number:03d}_Track_{track}.{extension}")

    return bp
