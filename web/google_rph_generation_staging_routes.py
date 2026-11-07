"""Opt-in Google RPH generation on ISOLATED staging, disabled by default.

Uses Google account UUID, the same Telegram-native verified Word+PDF source,
private durable storage and atomic one-credit-per-bundle RPC. Never writes to
Telegram's production user, subscription or RPH tables.

REQUIRES CIKGULAJU_GOOGLE_RPH_STAGING_ENABLED=1 *and* trusted internal
Telegram renderer API credentials, configured privately in Render staging.
"""
import hashlib
import hmac
import os
import re
import time
import uuid
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, make_response, request

from web.google_web_catalog_staging import _actor
from web.google_auth_staging_routes import _enabled_config
from web.google_account_store import google_staging_account_profile, GoogleAccountUnavailable
from web.google_native_rph_bundle import (
    render_native_google_rph_bundle, NativeGoogleRPHNotReady, _teacher_fields)
from web.google_rph_bundle_job_store import (
    selection_fingerprint, prepare_private_bundle, publish_rendered_bundle,
    BundleCommitUnconfirmed)
from web.google_rph_bundle_delivery import _ready_job, RPHDeliveryUnavailable

bp = Blueprint("google_rph_generate_staging", __name__)
MAX_BODY = 5000
MAX_AGE = 3600


def _native_renderer_configured(cfg):
    """Non-secret diagnostic. Do not expose API URLs or token material."""
    if not isinstance(cfg, dict) or not cfg.get("host"):
        return False
    base = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    parsed = urlsplit(base)
    return bool(
        parsed.scheme == "https" and parsed.hostname and parsed.port is None
        and not parsed.username and not parsed.password
        and parsed.path in ("", "/") and not parsed.query
        and not parsed.fragment and isinstance(token, str) and len(token) >= 32
        and parsed.hostname not in (cfg["host"], "cikgulaju-web.onrender.com")
    )


def _generator_config():
    if os.environ.get("CIKGULAJU_GOOGLE_RPH_STAGING_ENABLED") != "1":
        return None
    cfg = _enabled_config()
    return cfg if _native_renderer_configured(cfg) else None


def _same_origin(cfg):
    return (request.headers.get("Origin") == cfg["origin"]
            and request.headers.get("Sec-Fetch-Site", "same-origin")
            in ("same-origin", "none"))


def _request_payload(content):
    if not isinstance(content, dict) or set(content) != {"selection", "teacher"}:
        raise ValueError("Invalid RPH request")
    pick = content.get("selection")
    teacher = _teacher_fields(content.get("teacher"))
    if not isinstance(pick, dict) or set(pick) != {
            "year", "subject", "unit", "lesson", "component"}:
        raise ValueError("Invalid lesson selection")
    year = pick.get("year")
    subject = pick.get("subject")
    unit = pick.get("unit")
    lesson = pick.get("lesson")
    component = pick.get("component")
    if (type(year) is not int or year not in range(2,7)
            or subject not in ("ENGLISH", "MORAL", "PJPK", "PSV")
            or not isinstance(unit, str) or not 0 < len(unit) <= 300
            or not isinstance(lesson, str) or not 0 < len(lesson) <= 120
            or (subject == "PJPK" and component not in ("PJ", "PK"))
            or (subject != "PJPK" and component is not None)):
        raise ValueError("Invalid source fields")
    from web.unified_rph_web import pdp_options
    rows = pdp_options(year, subject, unit, component=component)
    matched = [row for row in rows if row["value"] == lesson]
    if len(matched) != 1:
        raise ValueError("Lesson not in exact source inventory")
    return {"year":year,"subject":subject,"unit":unit,
            "lesson":lesson,"component":component}, teacher


def _token(account_id, job_id, selection_hash, secret, *, issued=None):
    at = int(time.time() if issued is None else issued)
    body = f"jobv1.{account_id}.{job_id}.{selection_hash}.{at}"
    mac = hmac.new(secret.encode("utf-8"),body.encode("ascii"),hashlib.sha256).hexdigest()
    return body+"."+mac


def _verify_ticket(ticket, account_id, selection_hash, secret, *, now=None):
    if not isinstance(ticket, str) or len(ticket) > 370:
        return None
    parts = ticket.split(".")
    if len(parts) != 6 or parts[0] != "jobv1":
        return None
    _, subject, ref, digest, at, supplied_mac = parts
    if (subject != account_id or digest != selection_hash
            or not re.fullmatch(r"[0-9a-f]{64}",supplied_mac)
            or not re.fullmatch(r"[0-9]{1,12}",at)):
        return None
    try:
        canonical = str(uuid.UUID(ref))
    except (TypeError, ValueError, AttributeError):
        return None
    if canonical != ref:
        return None
    timestamp = int(time.time() if now is None else now)
    if int(at) > timestamp or timestamp - int(at) > MAX_AGE:
        return None
    body = ".".join(parts[:-1])
    expected = hmac.new(secret.encode("utf-8"),body.encode("ascii"),hashlib.sha256).hexdigest()
    return ref if hmac.compare_digest(expected,supplied_mac) else None


def _ready_links(job_id):
    base = "/api/google-staging/web/rph/jobs/" + job_id + "/download/"
    return {"word":base+"word","pdf":base+"pdf"}


@bp.after_request
def protect(response):
    response.headers["Cache-Control"]="no-store, private"
    response.headers["Vary"]="Cookie"
    response.headers["X-Content-Type-Options"]="nosniff"
    return response


@bp.get("/api/google-staging/web/rph/capabilities")
def capabilities():
    actor, err = _actor()
    if err is not None:
        return err
    ready = _generator_config() is not None
    return jsonify({"google_verified":True,"staging_only":True,
                    "generation_enabled":ready,
                    "download_enabled":True if ready else False,
                    "note":"Janaan Google hanya aktif selepas enjin Telegram disambung."})


@bp.post("/api/google-staging/web/rph/issue")
def issue():
    actor, err = _actor()
    if err is not None:
        return err
    cfg = _generator_config()
    if cfg is None:
        return jsonify({"error":"Penjana RPH Google staging belum diaktifkan"}),503
    if not _same_origin(cfg):
        return jsonify({"error":"Permintaan rentas laman ditolak"}),403
    if not request.is_json or request.content_length is None or request.content_length>MAX_BODY:
        return jsonify({"error":"Permintaan terlalu besar"}),400
    try:
        choice, teacher = _request_payload(request.get_json(silent=True))
    except (ValueError,KeyError,TypeError,OSError):
        return jsonify({"error":"Lesson dan maklumat guru tidak sah"}),400
    try:
        prof=google_staging_account_profile(cfg,actor.account_id)
        if prof["trial_remaining"]==0:
            from web.google_payment_store import web_payment_access
            paid=web_payment_access(cfg,actor.account_id)
            if not paid.get("payment_access_active"):
                return jsonify({"error":"10 janaan percuma sudah habis","remaining":0}),403
    except (GoogleAccountUnavailable,KeyError,ValueError,TypeError,RuntimeError):
        return jsonify({"error":"Baki akaun belum boleh disahkan"}),503
    digest=selection_fingerprint(choice,teacher)
    job_id=str(uuid.uuid4())
    try:
        prepared=prepare_private_bundle(cfg,actor,job_id,digest)
    except (BundleCommitUnconfirmed,ValueError):
        return jsonify({"error":"Rekod janaan belum boleh disahkan"}),503
    if prepared["status"]!="prepared":
        return jsonify({"error":"Status janaan tidak sah"}),503
    return jsonify({"job_id":job_id,
                    "ticket":_token(actor.account_id,job_id,digest,cfg["secret"]),
                    "status":"prepared","staging_only":True,
                    "charged":False})


@bp.post("/api/google-staging/web/rph/generate")
def generate():
    actor, err = _actor()
    if err is not None:
        return err
    cfg = _generator_config()
    if cfg is None:
        return jsonify({"error":"Penjana RPH Google staging belum diaktifkan"}),503
    if not _same_origin(cfg):
        return jsonify({"error":"Permintaan rentas laman ditolak"}),403
    if not request.is_json or request.content_length is None or request.content_length>MAX_BODY:
        return jsonify({"error":"Permintaan terlalu besar"}),400
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict) or set(payload)!={"ticket","selection","teacher"}:
        return jsonify({"error":"Permintaan janaan tidak sah"}),400
    try:
        choice,teacher=_request_payload({"selection":payload["selection"],"teacher":payload["teacher"]})
    except (ValueError,KeyError,TypeError,OSError):
        return jsonify({"error":"Lesson tidak sah"}),400
    digest=selection_fingerprint(choice,teacher)
    job_id=_verify_ticket(payload.get("ticket"),actor.account_id,digest,cfg["secret"])
    if job_id is None:
        return jsonify({"error":"Tiket janaan tidak sah atau sudah tamat"}),403
    try:
        previous=_ready_job(cfg,actor,job_id)
    except (RPHDeliveryUnavailable,ValueError):
        return jsonify({"error":"Status janaan belum boleh disahkan",
                        "job_id":job_id}),503
    if previous is None:
        return jsonify({"error":"Rekod janaan tiada","job_id":job_id}),404
    if previous["status"]=="ready":
        return jsonify({"status":"ready","already_ready":True,"job_id":job_id,
                        "downloads":_ready_links(job_id),"staging_only":True})
    try:
        bundle=render_native_google_rph_bundle(
            choice["year"],choice["subject"],choice["unit"],choice["lesson"],
            teacher,component=choice["component"])
    except (NativeGoogleRPHNotReady,ValueError,TypeError):
        return jsonify({"error":"RPH native Telegram belum tersedia untuk Lesson ini",
                        "job_id":job_id}),503
    try:
        result=publish_rendered_bundle(
            cfg,actor,job_id,digest,bundle["word"],bundle["pdf"])
    except (BundleCommitUnconfirmed,ValueError):
        return jsonify({"error":"Status simpanan/potongan belum pasti. Semak semula status janaan ini.",
                        "job_id":job_id,"outcome_unconfirmed":True}),503
    if result.get("status")=="ready":
        return jsonify({"status":"ready","job_id":job_id,
                        "downloads":_ready_links(job_id),
                        "remaining":result.get("remaining"),
                        "already_ready":bool(result.get("already_ready",False)),
                        "staging_only":True})
    if result.get("allowed") is False:
        return jsonify({"error":"Baki 10 janaan telah habis",
                        "remaining":result.get("remaining",0),
                        "job_id":job_id}),403
    return jsonify({"error":"Status RPH belum boleh dipastikan",
                    "job_id":job_id,"outcome_unconfirmed":True}),503


@bp.get("/api/google-staging/web/rph/jobs/<job_id>/status")
def job_status(job_id):
    actor, err=_actor()
    if err is not None:
        return err
    if request.args:
        return jsonify({"error":"Parameter tidak dibenarkan"}),400
    try:
        job=_ready_job(_enabled_config(),actor,job_id)
    except ValueError:
        return jsonify({"error":"ID janaan tidak sah"}),400
    except RPHDeliveryUnavailable:
        return jsonify({"error":"Status janaan tidak tersedia"}),503
    if job is None:
        return jsonify({"error":"Janaan tidak dijumpai"}),404
    ready=job["status"]=="ready"
    return jsonify({"status":job["status"],"job_id":job_id,
                    "download_ready":ready,
                    "downloads":_ready_links(job_id) if ready else {},
                    "staging_only":True})
