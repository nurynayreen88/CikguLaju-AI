"""Admin Web review downloads proxied from the Telegram Matematik SJKT source."""

from io import BytesIO
import json
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, Request, build_opener

from flask import Blueprint, abort, render_template, request, send_file

from web.admin_usage_web import allowed_admin_ids
from web.document_integrity import validate_word_document
from web.native_telegram_rph_client import BlockRedirects, MAX_DOCUMENT, MIMES, NativeRPHUnavailable
from web.native_verified_rpt_rph_client import _backend
from web.teacher_profile_routes import _auth

bp = Blueprint("matematik_sjkt_t2_review_web", __name__, template_folder="templates")
WEB_PATH = "/admin/semakan/matematik-sjkt-tahun-2"
SOURCE_PATH = "/internal/rph/v1/matematik-sjkt-t2/review"
TEACHER_LENGTHS = {"class": 40, "date": 10, "time": 13, "students": 3, "reflection": 500}


@bp.before_request
def _require_admin():
    _, uid, error = _auth()
    if error is not None:
        return error
    if uid not in allowed_admin_ids():
        abort(403)
    if request.args:
        abort(400)


@bp.after_request
def _private_headers(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _request_source(suffix, mime, limit, *, teacher=None):
    try:
        base, token = _backend()
        headers = {"Authorization": "Bearer " + token, "Accept": mime}
        data = None
        if teacher is not None:
            data = json.dumps(teacher, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = Request(base + SOURCE_PATH + suffix, data=data, headers=headers)
        with build_opener(HTTPSHandler(), BlockRedirects()).open(req, timeout=15) as response:
            if response.status != 200 or response.headers.get_content_type() != mime:
                raise NativeRPHUnavailable("Unexpected review response")
            payload = response.read(limit + 1)
        if len(payload) > limit:
            raise NativeRPHUnavailable("Oversized review response")
        return payload
    except HTTPError as exc:
        if exc.code == 404:
            abort(404)
        if exc.code == 400 and teacher is not None:
            abort(400, description="Butiran guru tidak sah.")
        abort(503, description="Sumber semakan Telegram belum tersedia.")
    except (URLError, OSError, NativeRPHUnavailable, ValueError):
        abort(503, description="Sumber semakan Telegram belum tersedia.")


def _options(unit=None):
    limit = 8 if unit is None else 96
    try:
        rows = json.loads(_request_source("" if unit is None else f"/{unit}", "application/json", 32_000))
        if not isinstance(rows, list) or not 1 <= len(rows) <= limit:
            raise ValueError("Invalid review catalogue")
        ids = [row["value"] for row in rows]
        if (any(type(n) is not int or not 1 <= n <= limit for n in ids)
                or ids != sorted(set(ids))
                or unit is None and ids != list(range(1, limit + 1))
                or any(not isinstance(row["label"], str) or not 1 <= len(row["label"]) <= 300 for row in rows)
                or unit is not None and any(
                    not isinstance(row[key], str) or not 1 <= len(row[key]) <= 60
                    for row in rows for key in ("sp", "buku_teks", "buku_aktiviti")
                )):
            raise ValueError("Invalid review catalogue")
    except (KeyError, TypeError, ValueError):
        abort(503, description="Katalog semakan Telegram tidak dapat disahkan.")
    return rows


@bp.get(WEB_PATH)
@bp.get(WEB_PATH + "/<int:unit>")
def catalogue(unit=None):
    if unit is not None and not 1 <= unit <= 8:
        abort(404)
    return render_template("matematik_sjkt_t2_review.html", unit=unit, options=_options(unit))


@bp.get(WEB_PATH + "/<int:unit>/<int:pdp>")
def teacher_fields(unit, pdp):
    if not 1 <= unit <= 8 or not 1 <= pdp <= 96:
        abort(404)
    selected = next((row for row in _options(unit) if row["value"] == pdp), None)
    if selected is None:
        abort(404)
    return render_template("matematik_sjkt_t2_review.html", unit=unit, selected=selected)


@bp.route(WEB_PATH + "/<int:unit>/<int:pdp>/<fmt>", methods=("GET", "POST"))
def document(unit, pdp, fmt):
    if not 1 <= unit <= 8 or not 1 <= pdp <= 96 or fmt not in MIMES:
        abort(404)
    teacher = None
    if request.method == "POST":
        origin = request.headers.get("Origin")
        if origin not in ("https://" + request.host, request.host_url.rstrip("/")):
            abort(403)
        if request.mimetype != "application/x-www-form-urlencoded" or not 0 < (request.content_length or 0) <= 8000:
            abort(400)
        fields = request.form
        if set(fields) != set(TEACHER_LENGTHS) or any(
            len(fields.getlist(key)) != 1 or len(fields[key]) > limit
            for key, limit in TEACHER_LENGTHS.items()
        ):
            abort(400, description="Butiran guru tidak sah.")
        teacher = fields.to_dict()
    content = _request_source(f"/{unit}/{pdp}/{fmt}", MIMES[fmt], MAX_DOCUMENT, teacher=teacher)
    if fmt == "word":
        try:
            validate_word_document(content)
        except ValueError:
            abort(503, description="Fail Word tidak dapat disahkan.")
    elif len(content) < 1000 or not content.startswith(b"%PDF-") or not content.rstrip().endswith(b"%%EOF"):
        abort(503, description="Fail PDF tidak dapat disahkan.")
    extension = "docx" if fmt == "word" else "pdf"
    filename = f"RPH_2027_Matematik_SJKT_Tahun_2_PdP_{pdp:03}.{extension}"
    return send_file(BytesIO(content), mimetype=MIMES[fmt], download_name=filename, as_attachment=True)
