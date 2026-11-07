"""Dedicated staging admin Telegram Login Widget. Does not touch live accounts."""
import os
import re
import uuid
from pathlib import Path
from flask import Blueprint, jsonify, make_response, request, send_file
from web.google_auth_staging_routes import _enabled_config
from web.google_staging_admin_sessions import (
    issue_staging_admin_ticket, verify_staging_admin_ticket)
from web_v1_telegram_login import verify_telegram_login

bp = Blueprint("google_staging_admin_auth", __name__)
ADMIN_COOKIE = "cikgulaju_staging_admin_ticket"


def admin_allowlist():
    raw = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ADMIN_TELEGRAM_IDS", "")
    values = [v.strip() for v in raw.split(",") if v.strip()]
    if not values or any(not re.fullmatch(r"[0-9]{4,18}", v) for v in values):
        return frozenset()
    return frozenset(int(v) for v in values)


def _bot():
    token = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ADMIN_BOT_TOKEN", "")
    name = os.environ.get("CIKGULAJU_GOOGLE_STAGING_ADMIN_BOT_USERNAME", "").lstrip("@")
    if (not re.fullmatch(r"[0-9]{5,15}:[A-Za-z0-9_-]{20,}", token)
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{4,31}", name)):
        return None
    return token, name


def _config():
    config = _enabled_config()
    if config is None or not admin_allowlist() or _bot() is None:
        return None
    return config


def _same_origin(config):
    return (request.headers.get("Origin") == config["origin"]
            and request.headers.get("Sec-Fetch-Site","same-origin") in
                ("same-origin","none"))


def _get_verified_admin(config):
    ticket = request.cookies.get(ADMIN_COOKIE)
    uid = verify_staging_admin_ticket(ticket, config["secret"])
    return uid if uid in admin_allowlist() else None


@bp.get("/admin/google-staging-login")
def staging_admin_login():
    config = _config()
    if not config:
        return jsonify({"error":"Staging admin Telegram belum dikonfigurasi"}),503
    return send_file(Path(__file__).with_name("google_staging_admin_login.html"),
                     mimetype="text/html",max_age=0)


@bp.get("/api/auth/google/admin/bot")
def staging_bot_public_name():
    config = _config()
    if not config:
        return jsonify({"error":"Staging admin belum tersedia"}),503
    response = jsonify({"bot_username":_bot()[1]})
    response.headers["Cache-Control"]="no-store"
    return response


@bp.post("/api/auth/google/admin/telegram")
def staging_admin_widget():
    config = _config()
    if not config:
        return jsonify({"error":"Pengesahan admin staging belum tersedia"}),503
    if not _same_origin(config):
        return jsonify({"error":"Asal permintaan tidak sah"}),403
    if (not request.is_json or request.content_length is None
            or request.content_length > 8192):
        return jsonify({"error":"Permintaan tidak sah"}),400
    payload = request.get_json(silent=True)
    uid = verify_telegram_login(payload,_bot()[0],max_age_seconds=120)
    if type(uid) is not int or uid not in admin_allowlist():
        return jsonify({"error":"Admin tidak dibenarkan"}),403
    ticket = issue_staging_admin_ticket(uid,config["secret"])
    response = jsonify({"authenticated":True})
    response.set_cookie(ADMIN_COOKIE,ticket,secure=True,httponly=True,
                        samesite="Lax",max_age=3600,path="/")
    response.headers["Cache-Control"]="no-store"
    return response


@bp.get("/api/auth/google/admin/session")
def staging_admin_session_status():
    config=_config()
    if not config:
        return jsonify({"authenticated":False}),503
    uid=_get_verified_admin(config)
    response=make_response(jsonify({"authenticated":uid is not None}),
                           200 if uid else 401)
    response.headers["Cache-Control"]="no-store, private"
    return response


@bp.post("/api/auth/google/admin/logout")
def staging_admin_logout():
    config=_config()
    if not config:
        return jsonify({"error":"Staging admin belum tersedia"}),503
    if not _same_origin(config):
        return jsonify({"error":"Asal permintaan tidak sah"}),403
    response=jsonify({"authenticated":False})
    response.delete_cookie(ADMIN_COOKIE,path="/",secure=True,httponly=True,
                           samesite="Lax")
    response.headers["Cache-Control"]="no-store"
    return response
