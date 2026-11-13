"""Private Web classroom assessment records."""
import csv
from datetime import date
from io import BytesIO, StringIO
import json
import re
from uuid import UUID, uuid4
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from flask import Blueprint, Response, jsonify, request

from web.pbd_store import Conflict, RECORDS, ROSTERS, StorageError, one, request_rows, scope, write
from web.pbd_xlsx import read_rows
from web.teacher_profile_routes import _auth
from web.teacher_profile_store import ProfileUnavailable, ProfileValidation, get_profile

bp = Blueprint("web_pbd", __name__, url_prefix="/api/web/pbd")
STATUS = ("Boleh sendiri", "Dengan bimbingan", "Belum menguasai", "Belum dinilai")
METHODS = ("Pemerhatian", "Lisan", "Penulisan", "Pelbagai kaedah")
TP = tuple(f"TP{n}" for n in range(1, 7))
PAGE_SIZE = 25


class Invalid(ValueError):
    pass


def exact(data, fields):
    if not isinstance(data, dict) or set(data) != set(fields.split()):
        raise Invalid("Medan rekod tidak lengkap atau tidak sah.")
    return data


def text(value, limit, label, required=False):
    if not isinstance(value, str):
        raise Invalid(f"{label} mesti dalam bentuk teks.")
    value = value.strip()
    if len(value) > limit or any(ord(c) < 32 and c != "\n" for c in value):
        raise Invalid(f"{label} terlalu panjang atau mengandungi aksara tidak sah.")
    if required and not value:
        raise Invalid(f"Isi {label.lower()} dahulu.")
    return value


def uid_text(value, optional=False):
    if optional and value == "":
        return value
    if not isinstance(value, str):
        raise Invalid("Pengenal rekod tidak sah.")
    try:
        return str(UUID(value))
    except ValueError:
        raise Invalid("Pengenal rekod tidak sah.") from None


def date_text(value):
    value = text(value, 10, "Tarikh", True)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise Invalid("Tarikh tidak sah.") from None
    if parsed.isoformat() != value:
        raise Invalid("Tarikh tidak sah.")
    return value


def select_value(value, choices, label):
    if not isinstance(value, str) or value not in ("", *choices):
        raise Invalid(f"Pilihan {label} tidak sah.")
    return value


def name_code(data):
    name = text(data["name"], 120, "Nama murid", True)
    code = text(data["code"], 20, "Kod murid")
    if "\n" in name or "\n" in code or re.search(r"\d{7,}", code):
        raise Invalid("Guna nama dan kod ringkas seperti M01.")
    return {"name": name, "code": code}


def clean_roster(data, old):
    if not isinstance(data, list) or len(data) > 100:
        raise Invalid("Maksimum 100 murid bagi setiap kelas.")
    existing = {s["id"] for s in old}
    ids, identities, codes = set(), set(), set()
    cleaned = []
    for item in data:
        exact(item, "id name code")
        student = name_code(item)
        ident = (student["name"].casefold(), student["code"].casefold())
        code = ident[1]
        if ident in identities or (code and code in codes):
            raise Invalid("Nama atau kod murid berulang. Guna kod berlainan bagi nama yang sama.")
        identities.add(ident)
        if code:
            codes.add(code)
        key = uid_text(item["id"], optional=True)
        if key and (key not in existing or key in ids):
            raise Invalid("Senarai murid telah berubah. Muat semula dahulu.")
        key = key or str(uuid4())
        ids.add(key)
        cleaned.append({"id": key, **student})
    return cleaned


def clean_record(data, roster, previous=None):
    exact(data, "id version kind date subject lesson sk sp criteria1 criteria2 period entries")
    kind = select_value(data["kind"], ("assessment", "report"), "jenis")
    if not kind or (previous and kind != previous["kind"]):
        raise Invalid("Jenis rekod tidak sah.")
    rec = {
        "kind": kind,
        "record_date": date_text(data["date"]),
        "subject": text(data["subject"], 80, "Subjek", True),
    }
    details = {}
    for key, limit, label in (
        ("lesson", 180, "Lesson/PdP"), ("sk", 200, "SK"), ("sp", 200, "SP"),
        ("criteria1", 450, "Kriteria 1"), ("criteria2", 450, "Kriteria 2"),
        ("period", 120, "Tempoh pelaporan"),
    ):
        needed = key == ("criteria1" if kind == "assessment" else "period")
        details[key] = text(data[key], limit, label, needed)
    available = {}
    if previous:
        available.update({s["id"]: s for s in previous["details"]["entries"]})
    available.update({s["id"]: s for s in roster})
    entries = data["entries"]
    if not isinstance(entries, list) or not 0 < len(entries) <= 100:
        raise Invalid("Pilih sekurang-kurangnya seorang murid.")
    results, seen = [], set()
    for entry in entries:
        exact(entry, "id status1 status2 method note followup tp")
        key = uid_text(entry["id"])
        if key not in available or key in seen:
            raise Invalid("Senarai murid telah berubah. Muat semula dahulu.")
        seen.add(key)
        student = available[key]
        item = {k: student[k] for k in ("id", "name", "code")}
        item["note"] = text(entry["note"], 350, "Catatan")
        if kind == "assessment":
            item["status1"] = select_value(entry["status1"], STATUS, "kriteria 1") or STATUS[-1]
            if details["criteria2"]:
                item["status2"] = select_value(entry["status2"], STATUS, "kriteria 2") or STATUS[-1]
            item["method"] = select_value(entry["method"], METHODS, "kaedah")
            item["followup"] = text(entry["followup"], 350, "Tindakan susulan")
        else:
            item["tp"] = select_value(entry["tp"], TP, "TP")
        results.append(item)
    details["entries"] = results
    return {**rec, "details": details}


def header_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


def import_rows(file):
    data = file.read(1_000_001)
    if len(data) > 1_000_000:
        raise Invalid("Saiz maksimum fail ialah 1 MB.")
    try:
        if file.filename.casefold().endswith(".csv"):
            sample = data.decode("utf-8-sig")
            rows = csv.reader(StringIO(sample), delimiter=";" if sample.splitlines() and ";" in sample.splitlines()[0] else ",")
            return extract_rows(rows)
        if not file.filename.casefold().endswith(".xlsx"):
            raise Invalid("Gunakan fail .xlsx atau .csv.")
        with ZipFile(BytesIO(data)) as archive:
            members = archive.infolist()
            if (len(members) > 100 or sum(m.file_size for m in members) > 8_000_000
                    or any(m.flag_bits & 1 for m in members)
                    or len({m.filename for m in members}) != len(members)):
                raise Invalid("Fail Excel terlalu besar atau berkunci.")
            return extract_rows(read_rows(archive))
    except Invalid:
        raise
    except (ValueError, BadZipFile, csv.Error, KeyError, TypeError, OSError, ParseError,
            NotImplementedError, RuntimeError):
        raise Invalid("Fail senarai murid tidak dapat dibaca.") from None


def extract_rows(rows):
    iterator = iter(rows)
    for index, row in enumerate(iterator):
        if index >= 20:
            raise Invalid("Lajur Nama Murid tidak ditemui.")
        headings = [header_name(value) for value in row]
        match = [i for i, label in enumerate(headings) if label in ("namamurid", "namapenuhmurid", "nama", "namapenuh", "studentname")]
        if len(match) == 1:
            name_index = match[0]
            code_index = next((i for i, label in enumerate(headings) if label in ("kodmurid", "kodmuridpilihan")), None)
            break
    else:
        raise Invalid("Lajur Nama Murid tidak ditemui.")
    result = []
    for row in iterator:
        raw_name = row[name_index] if name_index < len(row) else None
        if raw_name is None or not str(raw_name).strip():
            continue
        raw_code = row[code_index] if code_index is not None and code_index < len(row) else ""
        if any(isinstance(value, str) and value.startswith("=") for value in (raw_name, raw_code)):
            raise Invalid("Tampal nama dan kod murid sebagai nilai biasa dalam Excel.")
        result.append(name_code({"name": raw_name, "code": str(raw_code) if raw_code is not None else ""}))
        if len(result) > 100:
            raise Invalid("Pilih satu kelas sahaja dengan maksimum 100 murid.")
    if not result:
        raise Invalid("Tiada nama murid dalam fail.")
    return result


@bp.after_request
def private(response):
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@bp.errorhandler(Invalid)
def invalid(exc):
    return jsonify({"error": str(exc)}), 400


@bp.errorhandler(Conflict)
def conflict(_):
    return jsonify({"error": "Rekod sudah berubah. Muat semula sebelum menyimpan."}), 409


@bp.errorhandler(StorageError)
@bp.errorhandler(ProfileUnavailable)
@bp.errorhandler(ProfileValidation)
def unavailable(_):
    return jsonify({"error": "Storan Rekod PBD belum dapat dihubungi. Cuba lagi."}), 503


def same_origin():
    if request.headers.get("Origin") != "https://" + request.host:
        raise Invalid("Asal permintaan tidak sah.")


def json_body():
    same_origin()
    if not request.is_json or not 0 < (request.content_length or 0) <= 200000:
        raise Invalid("Saiz atau format rekod tidak sah.")
    return request.get_json(silent=True)


def scoped(conf, uid):
    cls = request.args.get("class", "")
    year = request.args.get("year", "")
    if not re.fullmatch(r"20[2-9][0-9]|2100", year):
        raise Invalid("Pilih sesi akademik yang sah.")
    classes = get_profile(conf["supabase_url"], conf["supabase_key"], uid)["class_names"]
    if cls not in classes:
        raise Invalid("Pilih kelas daripada Profil Saya.")
    return scope(cls, int(year)), cls, int(year)


def current_roster(conf, uid, filters):
    return one(conf, uid, ROSTERS, {**filters, "select": "students,version"}) or {"students": [], "version": ""}


@bp.get("/classes")
def classes():
    conf, uid, err = _auth()
    if err is not None:
        return err
    profile = get_profile(conf["supabase_url"], conf["supabase_key"], uid)
    return jsonify({"classes": profile["class_names"]})


@bp.route("/roster", methods=["GET", "PUT"])
def roster():
    conf, uid, err = _auth()
    if err is not None:
        return err
    filters, cls, year = scoped(conf, uid)
    body = exact(json_body(), "students version") if request.method == "PUT" else None
    current = current_roster(conf, uid, filters)
    if request.method == "GET":
        return jsonify(current)
    version = uid_text(body["version"], optional=True)
    if version != current["version"]:
        raise Conflict()
    students = clean_roster(body["students"], current["students"])
    payload = {"students": students, "version": str(uuid4())}
    if not version:
        payload.update(class_name=cls, school_year=year)
    saved = write(conf, uid, ROSTERS, filters, payload, version)
    return jsonify({k: saved[k] for k in ("students", "version")})


@bp.post("/import")
def preview_import():
    _, _, err = _auth()
    if err is not None:
        return err
    same_origin()
    if not 0 < (request.content_length or 0) <= 1_100_000 or "file" not in request.files:
        raise Invalid("Pilih fail Excel atau CSV sehingga 1 MB.")
    return jsonify({"students": import_rows(request.files["file"])})


@bp.route("/records", methods=["GET", "POST"])
def records():
    conf, uid, err = _auth()
    if err is not None:
        return err
    filters, cls, year = scoped(conf, uid)
    if request.method == "GET":
        page = request.args.get("page", "1")
        if not re.fullmatch(r"[1-9][0-9]{0,3}", page):
            raise Invalid("Halaman tidak sah.")
        student = uid_text(request.args.get("student", ""), optional=True)
        if student:
            filters["details"] = "cs." + json.dumps({"entries": [{"id": student}]}, separators=(",", ":"))
        rows = request_rows(conf, uid, RECORDS, "GET", {
            **filters, "select": "id,kind,record_date,subject,lesson:details->>lesson,period:details->>period",
            "limit": PAGE_SIZE + 1, "offset": (int(page) - 1) * PAGE_SIZE,
            "order": "record_date.desc,id.desc",
        })
        return jsonify({"records": rows[:PAGE_SIZE], "more": len(rows) > PAGE_SIZE})
    body = exact(json_body(), "id version kind date subject lesson sk sp criteria1 criteria2 period entries")
    key = uid_text(body["id"])
    version = uid_text(body["version"], optional=True)
    record_filters = {**filters, "id": "eq." + key}
    previous = one(conf, uid, RECORDS, {**record_filters, "select": "kind,details,version"})
    if (previous or {}).get("version", "") != version:
        raise Conflict()
    students = current_roster(conf, uid, filters)["students"]
    payload = {**clean_record(body, students, previous), "version": str(uuid4())}
    if not version:
        payload.update(id=key, class_name=cls, school_year=year)
    saved = write(conf, uid, RECORDS, record_filters, payload, version)
    return jsonify({"id": saved["id"], "version": saved["version"]})


def csv_value(value):
    value = str(value or "")
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


@bp.route("/records/<uuid:record_id>", methods=["GET", "DELETE"])
def record(record_id):
    conf, uid, err = _auth()
    if err is not None:
        return err
    filters, cls, year = scoped(conf, uid)
    filters["id"] = "eq." + str(record_id)
    columns = "id,version,kind,record_date,subject,details"
    if request.method == "DELETE":
        body = exact(json_body(), "version")
        version = uid_text(body["version"])
        rows = request_rows(conf, uid, RECORDS, "DELETE", {
            **filters, "version": "eq." + version, "select": "id",
        })
        if len(rows) != 1:
            raise Conflict()
        return jsonify({"deleted": True})
    saved = one(conf, uid, RECORDS, {**filters, "select": columns})
    if saved is None:
        return jsonify({"error": "Rekod tidak ditemui."}), 404
    if request.args.get("format") != "csv":
        return jsonify(saved)
    output = StringIO()
    writer = csv.writer(output)
    d = saved["details"]
    common = ["Kelas", "Sesi Akademik", "Tarikh", "Subjek", "Nama Murid", "Kod Murid"]
    is_report = saved["kind"] == "report"
    writer.writerow(common + (["Tempoh", "Bidang / Tema / Kemahiran", "TP", "Bukti / Catatan"] if is_report else [
        "Lesson/PdP", "SK", "SP", "Kriteria 1", "Status 1", "Kriteria 2", "Status 2",
        "Kaedah", "Bukti / Catatan", "Tindakan Susulan",
    ]))
    for s in d["entries"]:
        tail = ([d["period"], d["lesson"], s["tp"], s["note"]] if is_report else [
            d["lesson"], d["sk"], d["sp"], d["criteria1"], s["status1"], d["criteria2"],
            s.get("status2", ""), s["method"], s["note"], s["followup"],
        ])
        writer.writerow([csv_value(v) for v in [cls, year, saved["record_date"], saved["subject"], s["name"], s["code"], *tail]])
    return Response("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="Rekod_PBD_CikguLaju.csv"'})
