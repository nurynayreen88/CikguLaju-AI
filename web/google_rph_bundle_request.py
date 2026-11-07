"""Staging-only, opt-in Google-native RPH prepare/complete HTTP flow.

The staging account is derived ONLY from a verified, signed Google cookie.
One opaque server-created job is bound to its owner and exact validated
selection by a short-lived HMAC ticket; the database owns durable replay and
atomic finalization. No production account, fake Telegram ID, or fallback.
Leave CIKGULAJU_GOOGLE_RPH_STAGING_ENABLED unset until end-to-end acceptance.
"""
import hashlib
import hmac
import os
import re
import secrets
import time

from flask import Blueprint, jsonify, request

from web.google_auth_staging_routes import _enabled_config
from web.google_web_catalog_staging import _actor, SUBJECTS, YEARS
from web.google_native_rph_bundle import (
    _teacher_fields, render_native_google_rph_bundle,
    NativeGoogleRPHNotReady,
)
from web.google_rph_bundle_job_store import (
    selection_fingerprint, prepare_private_bundle,
    publish_rendered_bundle, BundleCommitUnconfirmed,
)
from web.google_rph_bundle_quota import server_generation_reference
from web.google_rph_bundle_delivery import _ready_job, RPHDeliveryUnavailable

bp = Blueprint("google_native_rph_requests_staging", __name__)
TICKET_TTL = 1800
SELECTION_FIELDS = {"year", "subject", "component", "unit", "lesson"}


class CurriculumUnavailable(RuntimeError):
    pass


@bp.after_request
def private_responses(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def _enabled():
    # This flag is intentionally separate from staging Google OAuth readiness.
    return os.environ.get("CIKGULAJU_GOOGLE_RPH_STAGING_ENABLED") == "1"


def _same_origin(config):
    return (request.headers.get("Origin") == config["origin"]
            and request.headers.get("Sec-Fetch-Site", "same-origin")
                in ("same-origin", "none")
            and request.content_length is not None
            and 0 < request.content_length <= 4096
            and request.mimetype == "application/json"
            and not request.args)


def _selection_and_teacher(body):
    if not isinstance(body, dict) or set(body) != {"selection", "teacher"}:
        raise ValueError("Complete RPH request required")
    selected = body["selection"]
    if not isinstance(selected, dict) or set(selected) != SELECTION_FIELDS:
        raise ValueError("Unknown RPH selection fields")
    year, subject, component, unit, lesson = (
        selected[k] for k in ("year", "subject", "component", "unit", "lesson"))
    if (type(year) is not int or year not in YEARS or subject not in SUBJECTS
            or not isinstance(unit, str) or not unit.strip() or len(unit) > 300
            or not isinstance(lesson, str) or not lesson.strip()
            or len(lesson) > 120
            or (subject == "PJPK" and component not in ("PJ", "PK"))
            or (subject != "PJPK" and component != "")):
        raise ValueError("Invalid source lesson selection")
    teacher = _teacher_fields(body["teacher"])
    if not teacher["class"] or not teacher["date"] or not teacher["time"]:
        raise ValueError("Teaching class, date and time required")
    # Exact source-backed choice, never a fabricated lesson token.
    from web.unified_rph_web import pdp_options
    try:
        lessons = pdp_options(year, subject, unit,
                              component=component if component else None)
    except (ValueError, KeyError, OSError, TypeError):
        raise CurriculumUnavailable("Curriculum source unavailable") from None
    if (not isinstance(lessons, list) or len(lessons) > 500
            or sum(isinstance(x, dict) and x.get("value") == lesson
                   for x in lessons) != 1):
        raise ValueError("Lesson not found in verified source")
    return dict(selected), teacher, selection_fingerprint(selected, teacher)


def _make_ticket(secret, account, job_id, selected_hash, *, now=None):
    issued = int(time.time() if now is None else now)
    prefix = f"{job_id}.{issued}"
    signed = f"cikgulaju-staging-job-v1|{account}|{selected_hash}|{prefix}"
    sig = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return prefix + "." + sig


def _verify_ticket(ticket, secret, account, selected_hash, *, now=None):
    if not isinstance(ticket, str) or len(ticket) > 200:
        return None
    parts = ticket.split(".")
    if len(parts) != 3 or not re.fullmatch(r"[0-9a-f-]{36}", parts[0]):
        return None
    job_id, issued, sig = parts
    if not issued.isascii() or not issued.isdigit() or not re.fullmatch(r"[0-9a-f]{64}", sig):
        return None
    try:
        import uuid
        if str(uuid.UUID(job_id)) != job_id:
            return None
    except (ValueError, AttributeError):
        return None
    clock = int(time.time() if now is None else now)
    epoch = int(issued)
    if str(epoch) != issued or epoch > clock or clock - epoch > TICKET_TTL:
        return None
    expected = _make_ticket(secret, account, job_id, selected_hash, now=epoch)
    return job_id if secrets.compare_digest(expected, ticket) else None


def _job_links(job_id):
    base = "/api/google-staging/web/rph/jobs/" + job_id + "/download/"
    return {"word": base + "word", "pdf": base + "pdf"}


@bp.post("/api/google-staging/web/rph/prepare")
def prepare():
    config = _enabled_config()
    if not config or not _enabled():
        return jsonify({"error": "Janaan Google staging belum dibuka"}), 503
    actor, failure = _actor()
    if failure is not None:
        return failure
    if not _same_origin(config):
        return jsonify({"error": "Asal atau jenis permintaan tidak sah"}), 403
    try:
        selection, teacher, digest = _selection_and_teacher(request.get_json(silent=True))
    except ValueError:
        return jsonify({"error": "Pilihan RPH tidak sah"}), 400
    except CurriculumUnavailable:
        return jsonify({"error": "Sumber RPH belum tersedia"}), 503
    job_id = server_generation_reference()
    try:
        result = prepare_private_bundle(config, actor, job_id, digest)
    except (BundleCommitUnconfirmed, ValueError, KeyError):
        return jsonify({"error": "Penyediaan janaan belum disahkan"}), 503
    if result.get("status") != "prepared":
        return jsonify({"error": "Status janaan luar jangka"}), 503
    ticket = _make_ticket(config["secret"], actor.account_id, job_id, digest)
    return jsonify({"job_id": job_id, "job_ticket": ticket,
                    "status": "prepared", "trial_debited": False,
                    "staging_only": True}), 201


@bp.post("/api/google-staging/web/rph/complete")
def complete():
    config = _enabled_config()
    if not config or not _enabled():
        return jsonify({"error": "Janaan Google staging belum dibuka"}), 503
    actor, failure = _actor()
    if failure is not None:
        return failure
    if not _same_origin(config):
        return jsonify({"error": "Asal atau jenis permintaan tidak sah"}), 403
    body = request.get_json(silent=True)
    if (not isinstance(body, dict) or set(body) != {"request", "job_ticket"}):
        return jsonify({"error": "Permintaan janaan tidak lengkap"}), 400
    try:
        selected, teacher, digest = _selection_and_teacher(body["request"])
    except ValueError:
        return jsonify({"error": "Pilihan RPH tidak sah"}), 400
    except CurriculumUnavailable:
        return jsonify({"error": "Sumber RPH belum tersedia"}), 503
    job_id = _verify_ticket(body["job_ticket"], config["secret"],
                            actor.account_id, digest)
    if job_id is None:
        return jsonify({"error": "Pengesahan janaan gagal atau tamat tempoh"}), 403
    try:
        # Verify persisted owner + exact selection *before* expensive rendering.
        current = prepare_private_bundle(config, actor, job_id, digest)
        if current["status"] == "ready":
            return jsonify({"job_id": job_id, "status": "ready",
                            "downloads": _job_links(job_id),
                            "replayed": True, "staging_only": True})
        if current["status"] != "prepared":
            return jsonify({"error": "Status janaan tidak sah"}), 503
        rendered = render_native_google_rph_bundle(
            selected["year"], selected["subject"], selected["unit"],
            selected["lesson"], teacher,
            component=selected["component"] if selected["component"] else None)
        outcome = publish_rendered_bundle(
            config, actor, job_id, digest, rendered["word"], rendered["pdf"])
    except NativeGoogleRPHNotReady:
        return jsonify({"error": "Penjana RPH asli belum tersedia; kredit tidak ditolak",
                        "job_id": job_id}), 503
    except (BundleCommitUnconfirmed, KeyError, ValueError, TypeError):
        return jsonify({"error": "Keputusan janaan belum pasti. Semak status ID sama; jangan mulakan janaan baharu.",
                        "job_id": job_id}), 503
    if not outcome.get("allowed") and outcome.get("status") == "prepared":
        return jsonify({"error": "Kuota percubaan telah habis",
                        "job_id": job_id, "status": "prepared"}), 403
    if outcome.get("status") != "ready" or not outcome.get("allowed"):
        return jsonify({"error": "Status pembayaran kredit tidak dapat disahkan",
                        "job_id": job_id}), 503
    return jsonify({"job_id": job_id, "status": "ready",
                    "remaining": outcome.get("remaining"),
                    "downloads": _job_links(job_id), "staging_only": True})


@bp.get("/api/google-staging/web/rph/jobs/<job_id>/status")
def job_status(job_id):
    config = _enabled_config()
    if not config:
        return jsonify({"error": "Google staging belum tersedia"}), 503
    actor, failure = _actor()
    if failure is not None:
        return failure
    if request.args:
        return jsonify({"error": "Parameter tidak sah"}), 400
    try:
        row = _ready_job(config, actor, job_id)
    except ValueError:
        return jsonify({"error": "ID janaan tidak sah"}), 400
    except RPHDeliveryUnavailable:
        return jsonify({"error": "Status janaan belum tersedia"}), 503
    if row is None:
        return jsonify({"error": "Janaan tidak dijumpai"}), 404
    response = {"job_id": row["id"], "status": row["status"],
                "staging_only": True}
    if row["status"] == "ready":
        response["downloads"] = _job_links(row["id"])
    return jsonify(response)
