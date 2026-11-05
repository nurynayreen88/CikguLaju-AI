"""Authenticated Web -> Telegram RPT cover service.

Reuses Telegram's already installed reportlab/pypdf/Pillow stack. No browser
access, no database writes, no source PDF replacement or quota debit. A source
SHA-256 mismatch fails closed rather than personalizing an out-of-sync RPT.
"""
import base64
import binascii
import hmac
import os
import re
from hashlib import sha256
from pathlib import Path

from flask import Blueprint, Response, jsonify, request

ROOT = Path(__file__).resolve().parents[1] / "rpt_2027"
MAX_BODY = 750_000
MAX_PDF = 25 * 1024 * 1024

RPT = {
    "english": ("English","english","RPT_ENGLISH_TAHUN_%d_2027_UNTUK_GURU.pdf"),
    "bahasa_melayu": ("Bahasa Melayu","bahasa_melayu","RPT_Bahasa_Melayu_Tahun_%d_2027_DRAF.pdf"),
    "matematik": ("Matematik","matematik","RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf"),
    "pendidikan_islam": ("Pendidikan Islam","pendidikan_islam","RPT_Pendidikan_Islam_Tahun_%d_2027_CikguLaju.pdf"),
    "pjpk": ("Pendidikan Jasmani dan Pendidikan Kesihatan (PJPK)","pjpk","RPT_PJPK_Tahun_%d_2027_DRAF.pdf"),
    "pendidikan_moral": ("Pendidikan Moral","pendidikan_moral","RPT_Pendidikan_Moral_Tahun_%d_2027_DRAF_WEB.pdf"),
    "psv": ("Pendidikan Seni Visual (PSV)","psv","RPT_PSV_Tahun_%d_2027_DRAF_WEB.pdf"),
}


def select_source(subject, year, root=ROOT):
    if subject not in RPT or type(year) is not int or not 2 <= year <= 6:
        raise ValueError("Invalid RPT selection")
    _label, folder, pattern = RPT[subject]
    path = Path(root) / folder / (pattern % year)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_PDF:
        raise ValueError("Missing RPT source")
    return path


def validate_payload(obj, *, root=ROOT):
    if not isinstance(obj, dict) or set(obj) != {
            "subject", "year", "source_sha256", "school", "state", "teacher", "logo"}:
        raise ValueError("Unexpected RPT input")
    path = select_source(obj["subject"], obj["year"], root)
    digest = obj["source_sha256"]
    if not isinstance(digest, str) or not re.fullmatch("[a-f0-9]{64}", digest):
        raise ValueError("Invalid RPT digest")
    original = path.read_bytes()
    if len(original) < 8000 or not original.startswith(b"%PDF-"):
        raise ValueError("Invalid source PDF")
    if not hmac.compare_digest(sha256(original).hexdigest(), digest):
        raise ValueError("Web/Telegram PDF content mismatch")
    for key, maxlen in (("school", 160), ("teacher", 100), ("state", 40)):
        val = obj[key]
        if not isinstance(val, str) or len(val) > maxlen or any(ord(c) < 32 for c in val):
            raise ValueError("Invalid school identity")
    logo_encoded = obj["logo"]
    logo = None
    if logo_encoded is not None:
        if not isinstance(logo_encoded, str) or len(logo_encoded) > 620000:
            raise ValueError("Invalid logo")
        try:
            logo = base64.b64decode(logo_encoded, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Invalid logo")
        if len(logo) > 450 * 1024 or not logo.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Invalid PNG logo")
    if not obj["school"].strip() and logo is None:
        raise ValueError("No school identity to personalize")
    identity = {"school": obj["school"].strip(), "teacher": obj["teacher"].strip(),
                "state": obj["state"].strip(), "logo": logo}
    return path, RPT[obj["subject"]][0], obj["year"], identity


def create_private_rpt_blueprint(*, root=ROOT):
    bp = Blueprint("telegram_private_school_rpt", __name__)

    @bp.after_request
    def protect(resp):
        resp.headers["Cache-Control"] = "no-store, private"
        resp.headers["Vary"] = "Authorization"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    @bp.post("/internal/rpt/v1/personalize")
    def personalize():
        token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
        header = request.headers.get("Authorization", "")
        if (os.environ.get("CIKGULAJU_WEB_NATIVE_RPH_ENABLED") != "1" or
                len(token) < 32 or not hmac.compare_digest(header, "Bearer " + token)):
            return jsonify({"error": "Unauthorized"}), 401
        if (request.content_length is None or request.content_length > MAX_BODY or
                request.mimetype != "application/json"):
            return jsonify({"error": "Invalid request size or type"}), 400
        try:
            obj = request.get_json(silent=True)
            path, subject, year, identity = validate_payload(obj, root=root)
        except (ValueError, TypeError, OSError):
            return jsonify({"error": "RPT source or identity does not match Telegram"}), 409
        try:
            from web.rpt_pdf_cover_renderer import personalized_pdf
            document = personalized_pdf(path, subject + " — Tahun " + str(year), 2027, identity)
            content = document.getvalue()
            if not content.startswith(b"%PDF-") or len(content) > MAX_PDF:
                raise ValueError("Invalid resulting RPT")
            response = Response(content, mimetype="application/pdf")
            response.headers["Content-Disposition"] = 'attachment; filename="RPT_Sekolah_2027.pdf"'
            return response
        except Exception:
            return jsonify({"error": "School RPT rendering unavailable"}), 503

    return bp
