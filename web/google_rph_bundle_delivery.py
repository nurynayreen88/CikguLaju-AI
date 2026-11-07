"""Private, authenticated Google staging RPH download from durable Storage.

No generation, no debit, no public Storage signed URLs, no Telegram IDs.
Only a completed / ready / *already charged* exact job for the currently
verified Google account may release Word or PDF.
"""
from io import BytesIO
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from flask import Blueprint, jsonify, make_response, request, send_file

from web.google_web_catalog_staging import _actor
from web.google_auth_staging_routes import _enabled_config
from web.google_staging_service_auth import staging_service_headers

bp = Blueprint("google_rph_delivery_staging", __name__)
BUCKET = "web-rph-bundles-staging"
MAX_BYTES = 15 * 1024 * 1024
MIMES = {
    "word": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    "pdf": ("application/pdf", ".pdf"),
}


class RPHDeliveryUnavailable(RuntimeError):
    pass


def _canonical_id(value):
    try:
        canonical = str(uuid.UUID(value))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Invalid RPH bundle ID") from None
    if value != canonical:
        raise ValueError("Invalid RPH bundle ID")
    return canonical


def _ready_job(config, actor, job_id, *, transport=None):
    """No browser account_id accepted; ownership checked in DB and code."""
    jid = _canonical_id(job_id)
    if actor.provider != "google" or actor.account_id is None:
        raise ValueError("Verified Google account required")
    account_id = _canonical_id(actor.account_id)
    key = config["staging_service_key"]
    address = config["supabase_url"].rstrip("/")
    params = urlencode({
        "select": "id,account_id,status,document_manifest_sha256",
        "id": "eq." + jid,
        "account_id": "eq." + account_id,
        "limit": "1",
    })
    req = Request(address + "/rest/v1/web_rph_bundle_jobs?" + params,
                  headers=staging_service_headers(key), method="GET")
    opener = transport or urlopen
    try:
        with opener(req, timeout=8) as res:
            raw = res.read(8193)
            if res.status != 200 or len(raw) > 8192:
                raise RPHDeliveryUnavailable("Invalid job backend response")
        rows = json.loads(raw)
        if not isinstance(rows, list) or len(rows) != 1:
            return None
        row = rows[0]
        if not isinstance(row, dict) or row.get("id") != jid or row.get("account_id") != account_id:
            raise RPHDeliveryUnavailable("Owner mismatch")
        if row.get("status") not in ("prepared", "ready"):
            raise RPHDeliveryUnavailable("Invalid bundle status")
        if row["status"] == "ready":
            digest = row.get("document_manifest_sha256")
            if not isinstance(digest, str) or len(digest) != 64 or any(x not in "0123456789abcdef" for x in digest):
                raise RPHDeliveryUnavailable("Unverified Word/PDF manifest")
        return row
    except (HTTPError, URLError, OSError, ValueError, TypeError, KeyError):
        raise RPHDeliveryUnavailable("Private RPH job source unavailable") from None


def _private_file(config, account_id, job_id, fmt, *, transport=None):
    if fmt not in MIMES:
        raise ValueError("Unsupported format")
    mime, ext = MIMES[fmt]
    key = config["staging_service_key"]
    name = account_id + "/" + job_id + ext
    address = (config["supabase_url"].rstrip("/") +
               "/storage/v1/object/authenticated/" + BUCKET + "/" +
               quote(name, safe="/"))
    req = Request(address, headers=staging_service_headers(key), method="GET")
    opener = transport or urlopen
    try:
        with opener(req, timeout=15) as res:
            actual_mime = res.headers.get("Content-Type", "").split(";")[0].strip().lower()
            data = res.read(MAX_BYTES + 1)
            if res.status != 200 or actual_mime != mime or not 500 <= len(data) <= MAX_BYTES:
                raise RPHDeliveryUnavailable("Private file invalid")
        if fmt == "pdf":
            if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-2048:]:
                raise RPHDeliveryUnavailable("PDF corrupted")
        else:
            # Word is ZIP-based, but never expose arbitrary ZIP or HTML.
            from web.google_rph_bundle_quota import _validated_bytes
            _validated_bytes(data, "word")
        return data
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        raise RPHDeliveryUnavailable("Private RPH file unavailable") from None


@bp.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@bp.get("/api/google-staging/web/rph/jobs/<job_id>/download/<fmt>")
def download(job_id, fmt):
    actor, failure = _actor()
    if failure is not None:
        return failure
    if fmt not in MIMES or request.args:
        return jsonify({"error": "Permintaan muat turun tidak sah"}), 400
    try:
        row = _ready_job(_enabled_config(), actor, job_id)
    except ValueError:
        return jsonify({"error": "ID janaan tidak sah"}), 400
    except RPHDeliveryUnavailable:
        return jsonify({"error": "Semakan janaan belum tersedia"}), 503
    if row is None:
        return jsonify({"error": "Janaan tidak dijumpai"}), 404
    if row["status"] != "ready":
        return jsonify({"error": "Fail RPH belum siap atau belum dibayar dengan kredit"}), 409
    try:
        data = _private_file(_enabled_config(), actor.account_id, row["id"], fmt)
    except (RPHDeliveryUnavailable, ValueError):
        return jsonify({"error": "Fail RPH belum boleh dimuat turun"}), 503
    mime, ext = MIMES[fmt]
    response = make_response(send_file(BytesIO(data), mimetype=mime,
                as_attachment=True, download_name="CIKGULAJU_RPH_" +
                row["id"][:8] + ext, conditional=False))
    response.headers["X-RPH-Generator"] = "telegram-native"
    response.headers["X-RPH-Delivery"] = "private-staging-bundle"
    return response
