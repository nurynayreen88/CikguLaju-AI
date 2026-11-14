"""Private timetable OCR endpoint for the CikguLaju Web service."""
import base64
import hmac
import json
import os
from threading import Lock

from flask import Blueprint, current_app, jsonify, request

from web.timetable_reader import read_timetable
from web.timetable_upload import (
    MAX_UPLOAD, READER_PATH, UnreadableTimetable, upload_mime,
)

bp = Blueprint("private_timetable_reader", __name__)
reader_lock = Lock()


@bp.after_request
def prevent_cache(response):
    response.headers["Cache-Control"] = "no-store, private"
    return response


@bp.post(READER_PATH)
def timetable_read():
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    header = request.headers.get("Authorization", "")
    if len(token) < 32 or not hmac.compare_digest(header.encode(), ("Bearer " + token).encode()):
        return jsonify(error="unauthorized"), 401
    if (request.args or request.content_length is None
            or not 0 < request.content_length <= MAX_UPLOAD
            or request.mimetype not in {"application/pdf", "image/png", "image/jpeg", "image/webp"}):
        return jsonify(error="Format atau saiz fail jadual tidak sah."), 400
    try:
        encoded_classes = request.headers.get("X-Timetable-Classes", "W10=")
        if len(encoded_classes) > 4096:
            raise ValueError
        classes = json.loads(base64.b64decode(encoded_classes, validate=True))
        if (not isinstance(classes, list) or len(classes) > 25
                or any(not isinstance(name, str) or not 0 < len(name) <= 40 for name in classes)):
            raise ValueError
    except ValueError:
        return jsonify(error="Senarai kelas tidak sah."), 400

    if not reader_lock.acquire(blocking=False):
        return jsonify(error="Pembaca jadual sedang digunakan. Cuba semula sekejap lagi."), 429
    try:
        data = request.get_data(cache=False)
        if upload_mime(data) != request.mimetype:
            raise UnreadableTimetable("Jenis fail jadual tidak sepadan.")
        review = request.headers.get("X-Timetable-Review")
        result = read_timetable(data, classes, guided=review == "2")
        if review not in ("1", "2"):
            result.pop("unclear_cells")
        return jsonify(result)
    except UnreadableTimetable as exc:
        return jsonify(error=str(exc)), 422
    except Exception as exc:
        current_app.logger.warning("Timetable OCR unavailable: %s", type(exc).__name__)
        return jsonify(error="Pembaca jadual belum tersedia."), 503
    finally:
        reader_lock.release()
