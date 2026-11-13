"""Run the isolated Web V1 preview without importing production app.py.

Local-only command:
    python tools/run_web_v1_preview.py

The preview optionally reads a local SQLite database in read-only mode.
It has no authentication, credit or generation endpoints.
Do not expose this development server to the public internet.
"""
import os
import sqlite3
from pathlib import Path
import sys

from flask import Flask, send_file, jsonify, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web_v1_dropdown_catalog import subject_options, available_subject_options, unit_options, pdp_options, component_options
from web_v1_verified_pdp import list_explicit_pjpk_entries
from web_v1_entitlements import display_trusted_account
PREVIEW = ROOT / "web_v1_static_preview" / "index.html"
app = Flask(__name__)
from web_v1_telegram_auth_routes import auth_blueprint
app.register_blueprint(auth_blueprint)
from web.english_catalog_http import create_english_catalog_blueprint
app.register_blueprint(create_english_catalog_blueprint())
from web.english_rpt_2027_http import create_english_rpt_blueprint
app.register_blueprint(create_english_rpt_blueprint())
from web.rpt_2027_all_http import create_all_rpt_blueprint
app.register_blueprint(create_all_rpt_blueprint())
from web.english_y6_rph_2027_http import create_blueprint as create_y6_rph_blueprint
app.register_blueprint(create_y6_rph_blueprint())
from web.unified_rph_web import create_blueprint as create_unified_rph_blueprint
app.register_blueprint(create_unified_rph_blueprint())


@app.get("/")
def preview():
    response = send_file(PREVIEW, mimetype="text/html", conditional=True)
    response.headers["Cache-Control"] = "no-store, private"
    return response


@app.get("/health")
def health():
    mode = os.environ.get("CIKGULAJU_WEB_CATALOG_MODE", "telegram-api")
    if mode == "versioned-copy":
        from web.versioned_catalog_copy import (
            CurriculumCopyUnavailable, get_verified_web_copy,
        )
        try:
            snapshot = get_verified_web_copy(
                os.environ.get("CIKGULAJU_WEB_COPY_MANIFEST", ""))
            return {"status": "preview-only", "database_connected": True,
                    "curriculum_mode": "versioned-web-copy",
                    "copy_version": snapshot["version"],
                    "generation_enabled": False}
        except (CurriculumCopyUnavailable, OSError):
            return {"status": "preview-only", "database_connected": False,
                    "curriculum_mode": "versioned-web-copy",
                    "generation_enabled": False}, 503
    db = os.environ.get("CIKGULAJU_WEB_PREVIEW_DB", "")
    connected = False
    if db and Path(db).is_file():
        try:
            from urllib.parse import quote
            uri = "file:" + quote(str(Path(db).resolve()), safe="/:") + "?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=2) as connection:
                connected = connection.execute("PRAGMA quick_check(1)").fetchone()[0] == "ok"
        except (sqlite3.Error, OSError, ValueError):
            connected = False
    return {"status": "preview-only", "database_connected": connected,
            "generation_enabled": False}


@app.get("/api/options")
def options():
    """Read-only dropdowns for authenticated existing accounts only."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    config = _config()
    if config is None:
        return jsonify({"error": "Login not configured", "code": "WEB_AUTH_CONFIG_MISSING"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "Authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "Account lookup unavailable", "code": "TELEGRAM_ACCOUNT_SOURCE_UNAVAILABLE"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "Existing account required"}), 403
    try:
        year = int(request.args.get("year", ""))
        if year not in range(1, 7):
            return jsonify({"error": "invalid year"}), 400
        kind = request.args.get("kind", "")
        if kind not in ("subjects", "units", "pdp", "components",
                        "bm-themes", "bm-units", "bm-topics", "bm-pdp"):
            return jsonify({"error": "invalid option kind"}), 400
        if kind == "components":
            return jsonify(component_options(request.args.get("subject", "")))
        # A versioned Web copy is opt-in and is never misrepresented as the
        # active Telegram database. Accounts/quota still use shared Supabase.
        catalog_mode = os.environ.get("CIKGULAJU_WEB_CATALOG_MODE", "telegram-api")
        if catalog_mode == "versioned-copy":
            from web.versioned_catalog_copy import (
                CurriculumCopyUnavailable, get_verified_web_copy,
            )
            try:
                snapshot = get_verified_web_copy(
                    os.environ.get("CIKGULAJU_WEB_COPY_MANIFEST", ""))
                db = snapshot["path"]
            except (CurriculumCopyUnavailable, OSError):
                return jsonify({"error": "verified Web curriculum copy unavailable",
                                "code": "WEB_CURRICULUM_COPY_UNAVAILABLE"}), 503
        elif catalog_mode == "telegram-api":
            source_url = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
            source_token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
            if bool(source_url) != bool(source_token):
                return jsonify({"error": "authoritative curriculum configuration incomplete",
                                "code": "TELEGRAM_CURRICULUM_API_NOT_CONNECTED"}), 503
            if source_url and source_token:
                from web.authoritative_http_source import AuthoritativeHttpCurriculumSource
                from web.authoritative_curriculum_source import SharedSourceUnavailable
                try:
                    source = AuthoritativeHttpCurriculumSource(source_url, source_token)
                    # Prove the live Telegram source is available before resolving
                    # any Web lesson; never fall back silently to a stale copy.
                    shared_subjects = source.list_subjects(year)
                    if kind == "subjects":
                        items = [
                            {**row, "label": ("Bahasa Inggeris (SK) · KSSR Semakan 2017"
                                              if year == 1 else "Bahasa Inggeris (SK)")}
                            if row.get("value") == "ENGLISH" else row
                            for row in shared_subjects
                        ]
                        if year in range(2, 7):
                            from web.unified_rph_web import source_records
                            for code, label in (("MORAL", "Pendidikan Moral"),
                                                ("PJPK", "PJPK"),
                                                ("PSV", "Pendidikan Seni Visual")):
                                if any(row.get("value") == code for row in items):
                                    continue
                                available = bool(
                                    source_records(year, code, "PJ")
                                    or source_records(year, code, "PK")
                                ) if code == "PJPK" else bool(source_records(year, code))
                                if available:
                                    items.append({"value": code, "label": label})
                        if year in (4,5,6) and not any(
                                row.get("value") == "RBT" for row in items):
                            # Only advertise if the active Telegram RBT private
                            # source answers; never use local draft snapshots.
                            from web.native_telegram_rbt_2027_client import (
                                list_rbt_units, NativeRPHUnavailable,
                            )
                            try:
                                if list_rbt_units(year):
                                    items.append({"value":"RBT","label":"Reka Bentuk dan Teknologi (DRAF)"})
                            except (NativeRPHUnavailable, ValueError):
                                pass
                        if year in (4, 5, 6) and not any(
                                row.get("value") == "SEJARAH" for row in items):
                            from web.native_telegram_sejarah_2027_client import (
                                list_sejarah_units, NativeRPHUnavailable,
                            )
                            try:
                                if list_sejarah_units(year):
                                    items.append({"value":"SEJARAH","label":"Sejarah"})
                            except (NativeRPHUnavailable, ValueError):
                                pass  # Never advertise unavailable Telegram RPH.
                        if year in range(2, 7):
                            from web.native_telegram_other_draft_client import (
                                list_draft_units, NativeRPHUnavailable,
                            )
                            for draft_code, draft_label in (
                                ("ARAB", "Bahasa Arab (DRAF)"),
                                ("MUZIK", "Pendidikan Muzik (DRAF)"),
                            ):
                                if any(row.get("value")==draft_code for row in items):
                                    continue
                                try:
                                    if list_draft_units(year,draft_code):
                                        items.append({"value":draft_code,
                                                      "label":draft_label})
                                except (NativeRPHUnavailable,ValueError):
                                    pass  # Never show an unavailable Telegram source.
                        return jsonify(items)
                    subject = request.args.get("subject", "")
                    component = request.args.get("component")
                    if kind.startswith("bm-"):
                        if subject != "BM" or component not in (None, ""):
                            return jsonify({"error": "invalid BM selection"}), 400
                        if kind == "bm-themes":
                            return jsonify(source.list_bm_themes(year))
                        if kind == "bm-units":
                            return jsonify(source.list_bm_units(
                                year, request.args.get("theme", "")))
                        if kind == "bm-topics":
                            return jsonify(source.list_bm_topics(
                                year, request.args.get("theme", ""),
                                request.args.get("unit", "")))
                        return jsonify(source.list_bm_pdps(
                            year, request.args.get("theme", ""),
                            request.args.get("unit", ""),
                            request.args.get("topic", "")))
                    # BM cannot fall back to synthetic language skill domains.
                    if subject == "BM" and kind in ("units", "pdp"):
                        return jsonify({"error": "Use BM Tema / Unit / Tajuk",
                                        "code": "BM_HIERARCHY_REQUIRED"}), 400
                    # Sejarah Year 4–6 follows its own verified Telegram
                    # Unit/PdP source, never a copied RPT week or generic Web RPH.
                    if subject == "RBT" and kind in ("units","pdp"):
                        from web.native_telegram_rbt_2027_client import (
                            list_rbt_units, list_rbt_lessons, NativeRPHUnavailable,
                        )
                        if year not in (4,5,6) or component not in (None,""):
                            return jsonify({"error":"Invalid RBT year/component"}), 400
                        try:
                            choices=(list_rbt_units(year) if kind=="units"
                                     else list_rbt_lessons(
                                         year,request.args.get("unit","")))
                        except (NativeRPHUnavailable,ValueError):
                            return jsonify({
                                "error":"Telegram RBT Unit/PdP belum tersedia",
                                "code":"TELEGRAM_RBT_SOURCE_UNAVAILABLE",
                            }),503
                        return jsonify(choices)
                    if subject == "SEJARAH" and kind in ("units", "pdp"):
                        from web.native_telegram_sejarah_2027_client import (
                            list_sejarah_units, list_sejarah_lessons,
                            NativeRPHUnavailable,
                        )
                        if year not in (4,5,6) or component not in (None, ""):
                            return jsonify({"error":"Invalid Sejarah selection"}), 400
                        try:
                            choices = (list_sejarah_units(year) if kind == "units"
                                       else list_sejarah_lessons(
                                            year, request.args.get("unit", "")))
                        except (NativeRPHUnavailable, ValueError):
                            return jsonify({
                                "error":"Telegram Sejarah unit/PdP unavailable",
                                "code":"TELEGRAM_SEJARAH_SOURCE_UNAVAILABLE",
                            }), 503
                        return jsonify(choices)
                    if subject in ("ARAB", "MUZIK") and kind in ("units","pdp"):
                        from web.native_telegram_other_draft_client import (
                            list_draft_units, list_draft_lessons,
                            NativeRPHUnavailable,
                        )
                        if year not in range(2,7) or component not in (None,""):
                            return jsonify({"error":"Invalid DRAF subject/year"}),400
                        try:
                            choices=(list_draft_units(year,subject) if kind=="units"
                                     else list_draft_lessons(
                                         year,subject,request.args.get("unit","")))
                        except (NativeRPHUnavailable,ValueError):
                            return jsonify({
                                "error":"Sumber PdP DRAF di Telegram belum tersedia.",
                                "code":"TELEGRAM_OTHER_DRAFT_SOURCE_UNAVAILABLE",
                            }),503
                        return jsonify(choices)
                    # Mathematics and Science have an independent, grouped
                    # native PdP sequence. Never substitute weekly RPT IDs.
                    if subject in ("MATH", "SCIENCE") and kind in ("units", "pdp"):
                        from web.native_telegram_sequence_rph_client import (
                            list_native_units, list_native_lessons,
                            NativeRPHUnavailable,
                        )
                        if component not in (None, ""):
                            return jsonify({"error": "invalid component"}), 400
                        try:
                            source_units = list_native_units(year, subject)
                            if subject == "MATH":
                                from web.math_unit_groups import (
                                    grouped_math_units, matched_math_tokens,
                                    tagged_math_lessons,
                                )
                                if kind == "units":
                                    choices = grouped_math_units(source_units)
                                else:
                                    tokens = matched_math_tokens(
                                        source_units, request.args.get("unit", ""))
                                    if not tokens:
                                        return jsonify({"error": "Unknown Mathematics Unit"}), 400
                                    choices = tagged_math_lessons([
                                        (token, list_native_lessons(year, subject, token))
                                        for token in tokens
                                    ])
                            else:
                                from web.science_unit_groups import (
                                    grouped_science_units, matched_science_tokens,
                                    tagged_science_lessons,
                                )
                                if kind == "units":
                                    choices = grouped_science_units(year, source_units)
                                else:
                                    tokens = matched_science_tokens(
                                        year, source_units, request.args.get("unit", ""))
                                    if not tokens:
                                        return jsonify({"error": "Unknown Science Unit"}), 400
                                    choices = tagged_science_lessons([
                                        (token, list_native_lessons(year, subject, token))
                                        for token in tokens
                                    ])
                        except (NativeRPHUnavailable, ValueError):
                            return jsonify({
                                "error": "Telegram native PdP sequence unavailable",
                                "code": "TELEGRAM_NATIVE_PDP_UNAVAILABLE",
                            }), 503
                        return jsonify(choices)
                    if year in range(2, 7) or (year == 1 and subject == "ENGLISH"):
                        from web.unified_rph_web import SOURCE_SUBJECTS
                        if subject in SOURCE_SUBJECTS:
                            from web.unified_rph_web import unit_options as source_units, pdp_options as source_pdp
                            if kind == "units":
                                return jsonify(source_units(year, subject, component))
                            if kind == "pdp":
                                return jsonify(source_pdp(year, subject,
                                    request.args.get("unit", ""), component))
                    if kind == "units":
                        return jsonify(source.list_units(year, subject, component))
                    if kind == "pdp":
                        return jsonify(source.list_lessons(
                            year, subject, request.args.get("unit", ""), component))
                except (SharedSourceUnavailable, ValueError):
                    return jsonify({"error": "authoritative curriculum source unavailable",
                                    "code": "TELEGRAM_CURRICULUM_API_UNAVAILABLE"}), 503
            # Preserve the old fail-closed behavior: no unverified local DB.
            from web.shared_source_provenance import catalog_source_status
            if not catalog_source_status()["shared_source_verified"]:
                return jsonify({"error": "shared catalog source not verified",
                                "code": "TELEGRAM_CURRICULUM_API_NOT_CONNECTED"}), 503
            db = os.environ.get("CIKGULAJU_WEB_PREVIEW_DB", "")
            if not db or not Path(db).is_file():
                return jsonify({"error": "preview database not configured"}), 503
        else:
            return jsonify({"error": "invalid curriculum mode",
                            "code": "WEB_CURRICULUM_MODE_INVALID"}), 503
        if kind.startswith("bm-") or (
                request.args.get("subject") == "BM" and kind in ("units", "pdp")):
            return jsonify({"error": "Verified BM hierarchy requires active Telegram",
                            "code": "BM_TELEGRAM_HIERARCHY_REQUIRED"}), 503
        if kind == "subjects":
            available = available_subject_options(db, year)
            if year in range(2, 7):
                from web.unified_rph_web import source_records
                for code, label in (("MORAL", "Pendidikan Moral"),
                                    ("PJPK", "PJPK"), ("PSV", "Pendidikan Seni Visual")):
                    if any(item["value"] == code for item in available):
                        continue
                    if code == "PJPK":
                        exists = bool(source_records(year, code, "PJ")
                                      or source_records(year, code, "PK"))
                    else:
                        exists = bool(source_records(year, code))
                    if exists:
                        available.append({"value": code, "label": label})
            return jsonify(available)
        if kind in ("units", "pdp") and year in range(2, 7):
            from web.unified_rph_web import SOURCE_SUBJECTS
            if request.args.get("subject") in SOURCE_SUBJECTS:
                from web.unified_rph_web import unit_options as source_units, pdp_options as source_pdp
                chosen_subject = request.args["subject"]
                chosen_component = request.args.get("component")
                if kind == "units":
                    return jsonify(source_units(year, chosen_subject, chosen_component))
                return jsonify(source_pdp(year, chosen_subject,
                                          request.args.get("unit", ""), chosen_component))
        subject = request.args.get("subject", "")
        if subject == "PJPK":
            component = request.args.get("component", "")
            if component not in ("PJ", "PK"):
                return jsonify({"error": "select PJ or PK"}), 400
            records = list_explicit_pjpk_entries(db, year, component)
            if kind == "units":
                names = dict.fromkeys((r.get("unit_title") or "").strip() for r in records)
                return jsonify([{"value": n, "label": n} for n in names if n])
            unit = request.args.get("unit", "")
            if not unit or len(unit) > 300:
                return jsonify({"error": "invalid unit"}), 400
            return jsonify([{"value": str(r["id"]), "label": "PdP " + str(r["pdp_no"]) + " — " + str(r.get("subtopic") or r.get("topic") or ""), "standalone_rph_verified": False} for r in records if (r.get("unit_title") or "").strip() == unit])
        if kind == "units":
            return jsonify(unit_options(db, year, subject))
        if kind == "pdp":
            return jsonify(pdp_options(db, year, subject, request.args.get("unit", "")))
        return jsonify({"error": "invalid option kind"}), 400
    except (ValueError, FileNotFoundError, OSError):
        return jsonify({"error": "invalid selection or unavailable database"}), 400
    except Exception:
        app.logger.exception("Preview dropdown read failed")
        return jsonify({"error": "dropdown temporarily unavailable"}), 503



@app.get("/api/source/status")
def shared_source_status():
    """Distinguish a verified, independently deployed Web copy from live parity."""
    from web.shared_source_provenance import catalog_source_status
    from web.shared_domain_parity import parity_report
    mode = os.environ.get("CIKGULAJU_WEB_CATALOG_MODE", "telegram-api")
    if mode == "versioned-copy":
        from web.versioned_catalog_copy import (
            CurriculumCopyUnavailable, get_verified_web_copy,
        )
        try:
            snapshot = get_verified_web_copy(
                os.environ.get("CIKGULAJU_WEB_COPY_MANIFEST", ""))
        except (CurriculumCopyUnavailable, OSError):
            return jsonify({
                "curriculum_mode": "versioned-web-copy",
                "web_copy_verified": False, "shared_source_verified": False,
                "telegram_parity_verified": False, "reason": "web copy unavailable",
            }), 503
        return jsonify({
            "curriculum_mode": "versioned-web-copy",
            "web_copy_verified": True,
            "copy_version": snapshot["version"],
            "copy_sha256": snapshot["sha256"],
            "shared_source_verified": False,
            "telegram_parity_verified": False,
            "reason": "separate checksum-verified copy; manually update both releases",
        })
    url = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    if not url or len(token) < 32:
        return jsonify({"curriculum_mode": "telegram-api",
                        "shared_source_verified": False,
                        "telegram_parity_verified": False,
                        "reason": "Live Telegram catalog connection not configured"}), 503
    try:
        from web.authoritative_http_source import AuthoritativeHttpCurriculumSource
        items = AuthoritativeHttpCurriculumSource(url, token).list_subjects(2)
        if not items:
            raise ValueError("Telegram returned empty subject catalog")
    except Exception:
        return jsonify({"curriculum_mode": "telegram-api",
                        "shared_source_verified": False,
                        "telegram_parity_verified": False,
                        "reason": "Live Telegram catalog unavailable"}), 503
    return jsonify({"curriculum_mode": "telegram-api",
                    "shared_source_verified": True,
                    "catalog_parity_verified": True,
                    "telegram_parity_verified": False,
                    "reason": "Live Telegram curriculum catalog reachable; RPH generation parity still pending"})


@app.get("/api/deployment/status")
def deployment_status():
    """Explicit staging-only capabilities for web readiness checks."""
    return jsonify({
        "environment": "staging-preview",
        "hosting": "render",
        "telegram_production_separate": True,
        "account_linked": False,
        "rph_generation_enabled": False,
        "public_launch_ready": False,
    })


@app.get("/api/auth/capabilities")
def auth_capabilities():
    """Public, non-sensitive readiness flags; never infer auth from QR primitives."""
    from web_v1_telegram_auth_routes import _config
    ready = _config() is not None
    bot_username = os.environ.get("CIKGULAJU_WEB_BOT_USERNAME", "").lstrip("@")
    widget_ready = ready and bool(bot_username)
    return jsonify({
        "telegram_login_enabled": widget_ready,
        "telegram_widget_enabled": widget_ready,
        "bot_username": bot_username if widget_ready else "",
        "phone_qr_pairing_enabled": False,
        "existing_account_lookup_enabled": ready,
        "session_cookie_enabled": ready,
        "status": "configured" if widget_ready else "not-configured",
    })


@app.get("/api/shared/status")
def shared_status():
    return jsonify({"shared_backend_connected": False, "telegram_account_linked": False, "generation_enabled": False, "download_enabled": False})

@app.get("/api/account/status")
def account_status():
    """Expose trusted existing-account status, never browser-supplied credits."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    config = _config()
    if config is None:
        return jsonify({"authenticated": False, "error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"authenticated": False}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"authenticated": False, "error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, **display_trusted_account(account), "shared_backend_connected": True})


@app.get("/api/materials")
def materials():
    """Read approved materials from Telegram only, never a preview DB."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    from web.authoritative_curriculum_source import CurriculumKey, SharedSourceUnavailable

    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "Authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "Existing account required"}), 403
    if set(request.args) != {"year", "subject", "lesson"}:
        return jsonify({"error": "invalid material selection"}), 400
    if any(len(request.args.getlist(k)) != 1 for k in ("year", "subject", "lesson")):
        return jsonify({"error": "invalid material selection"}), 400
    try:
        year = int(request.args["year"])
        lesson = request.args["lesson"]
        subject = request.args["subject"]
        if not lesson.isascii() or not lesson.isdecimal() or len(lesson) > 12 or int(lesson) <= 0:
            raise ValueError("lesson must be an active RPT row ID")
        key = CurriculumKey(year=year, subject_code=subject, lesson_id=lesson)
        from web.authoritative_curriculum_source import validate_curriculum_key
        validate_curriculum_key(key)
    except (ValueError, TypeError):
        return jsonify({"error": "invalid material selection"}), 400
    source_url = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", "").strip()
    source_token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    if not source_url or not source_token:
        return jsonify({"error": "Telegram materials source not configured", "code": "MATERIAL_SOURCE_NOT_CONFIGURED"}), 503
    try:
        from web.authoritative_http_source import AuthoritativeHttpCurriculumSource
        items = AuthoritativeHttpCurriculumSource(source_url, source_token).get_approved_materials(key)
    except (SharedSourceUnavailable, ValueError):
        return jsonify({"error": "Telegram approved materials unavailable", "code": "APPROVED_MATERIALS_NOT_VERIFIED"}), 503
    # The remote API is trusted for data, not for browser-safe fields.
    # Use an explicit allow-list: no storage paths, secret keys or direct URLs.
    # Approval without verified delivery never enables a link.
    safe_items = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "invalid Telegram material response"}), 503
        if item.get("approved") is not True:
            continue
        ident, title = item.get("id"), item.get("title")
        kind = item.get("type")
        if (not isinstance(ident, str) or not ident or len(ident) > 128
                or ident in seen or not isinstance(title, str) or not title.strip()
                or len(title) > 200 or kind not in
                ("rph", "textbook", "workbook", "audio", "teacherbook", "rpt", "support")):
            return jsonify({"error": "invalid Telegram material metadata"}), 503
        seen.add(ident)
        safe_items.append({"id": ident, "title": title.strip(), "type": kind,
                           "approved": True, "download_enabled": False})
    response = jsonify({"items": safe_items, "download_enabled": False})
    response.headers["Cache-Control"] = "no-store, private"
    return response


@app.get("/api/materials/download/<material_id>")
def download_material(material_id):
    """Never serve unverified files or charge credits from the Web preview."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "Authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "Existing account required"}), 403
    if not material_id or len(material_id) > 128:
        return jsonify({"error": "invalid material identifier"}), 400
    return jsonify({"error": "approved file delivery not verified",
                    "code": "MATERIAL_DELIVERY_NOT_VERIFIED"}), 503


@app.post("/api/generate")
def generate():
    """Authorized, approval-gated document generation; no quota mutation."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    from web.approved_rph_reader import RPHLookupConfig, load_approved_rph
    from web.rph_download_pipeline import prepare_approved_download
    from flask import make_response
    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "existing account required"}), 403
    if os.environ.get("CIKGULAJU_ENV") != "staging" or os.environ.get("CIKGULAJU_WEB_RPH_STAGING_ENABLED") != "1":
        return jsonify({"error": "approved RPH generation not enabled"}), 503
    if os.environ.get("CIKGULAJU_WEB_RPH_DELIVERY_EXPERIMENT") != "1":
        return jsonify({"error": "Shared RPH delivery not enabled"}), 503
    if not request.is_json or (request.content_length or 0) > 2048:
        return jsonify({"error": "invalid request"}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"lesson_id", "format"}:
        return jsonify({"error": "invalid selection"}), 400
    lesson_id, fmt = payload["lesson_id"], payload["format"]
    if type(lesson_id) is not int or lesson_id <= 0 or fmt not in ("docx", "pdf"):
        return jsonify({"error": "invalid selection"}), 400
    names = ("CIKGULAJU_WEB_APPROVED_DB", "CIKGULAJU_WEB_APPROVED_TABLE",
             "CIKGULAJU_WEB_APPROVED_ID_COLUMN", "CIKGULAJU_WEB_APPROVED_TITLE_COLUMN",
             "CIKGULAJU_WEB_APPROVED_CONTENT_COLUMN", "CIKGULAJU_WEB_APPROVED_STATUS_COLUMN",
             "CIKGULAJU_WEB_APPROVED_STATUS_VALUE", "CIKGULAJU_WEB_APPROVED_REFERENCE_COLUMN")
    values = [os.environ.get(name, "") for name in names]
    if any(not value for value in values):
        return jsonify({"error": "approved content source not configured"}), 503
    try:
        rph = load_approved_rph(RPHLookupConfig(*values), lesson_id)
    except (LookupError, ValueError, sqlite3.Error, OSError):
        return jsonify({"error": "approved RPH not available"}), 404
    try:
        result = prepare_approved_download(
            rph, fmt, account, uid, os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SECRET_KEY"])
    except (ImportError, ValueError, KeyError, OSError):
        return jsonify({"error": "document delivery unavailable"}), 503
    if not result["allowed"]:
        return jsonify({"error": "no remaining trial credits"}), 403
    data, mime = result["document"], result["mime"]
    response = make_response(data)
    response.headers["Content-Type"] = mime
    response.headers["Content-Disposition"] = f'attachment; filename="cikgulaju-rph-{lesson_id}.{fmt}"'
    response.headers["Cache-Control"] = "no-store, private"
    return response

@app.get("/api/web/english/rph/capabilities")
def english_rph_capabilities():
    enabled = (os.environ.get("CIKGULAJU_ENV") == "staging"
               and os.environ.get("CIKGULAJU_WEB_RPH_STAGING_ENABLED") == "1")
    missing = []
    for package in ("docx", "reportlab"):
        try:
            __import__(package)
        except ImportError:
            missing.append("python-docx" if package == "docx" else package)
    from web.download_release_gate import public_download_ready
    release_ready = public_download_ready(
        durable_idempotency=False, delivery_replay=False,
        production_layout_parity=False, approval_verified=False,
        trial_policy_verified=False)
    return jsonify({
        "download_enabled": release_ready,
        "renderer_ready": not missing,
        "missing_packages": missing,
        "staging_generation_enabled": enabled,
        "telegram_generation_parity_verified": False,
        "shared_quota_debit_verified": False,
        "durable_retry_safety_verified": False,
        "delivery_replay_verified": False,
        "note": "Staging renderer only; Telegram generation and quota parity not verified.",
    })


@app.post("/api/web/english/rph")
def english_approved_rph():
    """Render only explicitly release-ready English lessons by year and lesson."""
    from web_v1_telegram_auth_routes import _config, COOKIE, _lookup
    from web_v1_sessions import verify_session_ticket
    from web.english_release_gate import load_release_ready_english
    from web.rph_document_renderer import ApprovedRPH
    from web.rph_download_pipeline import prepare_approved_download
    from flask import make_response
    config = _config()
    if config is None:
        return jsonify({"error": "login not configured"}), 503
    uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
    if uid is None:
        return jsonify({"error": "authentication required"}), 401
    try:
        account = _lookup(config, uid)
    except Exception:
        return jsonify({"error": "account lookup unavailable"}), 503
    if not account or account.get("telegram_user_id") != uid:
        return jsonify({"error": "existing account required"}), 403
    if os.environ.get("CIKGULAJU_ENV") != "staging" or os.environ.get("CIKGULAJU_WEB_RPH_STAGING_ENABLED") != "1":
        return jsonify({"error": "RPH downloads not enabled"}), 503
    if os.environ.get("CIKGULAJU_WEB_RPH_DELIVERY_EXPERIMENT") != "1":
        return jsonify({"error": "Shared RPH delivery not enabled"}), 503
    if not request.is_json or (request.content_length or 0) > 2048:
        return jsonify({"error": "invalid request"}), 400
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) != {"year", "lesson_no", "format"}:
        return jsonify({"error": "invalid request"}), 400
    year, lesson_no, fmt = payload["year"], payload["lesson_no"], payload["format"]
    if type(year) is not int or year not in (1, 2, 3) or type(lesson_no) is not int or not 1 <= lesson_no <= 160 or fmt not in ("docx", "pdf"):
        return jsonify({"error": "invalid selection"}), 400
    try:
        content = load_release_ready_english(year, lesson_no)
    except (LookupError, ValueError, OSError):
        return jsonify({"error": "lesson not approved for release"}), 404
    try:
        result = prepare_approved_download(
            ApprovedRPH(lesson_no, f"English Year {year} — Lesson {lesson_no}", content, f"release-ready:english:{year}:{lesson_no}"),
            fmt, account, uid, os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
    except (ImportError, ValueError, KeyError, OSError):
        return jsonify({"error": "document delivery unavailable"}), 503
    if not result["allowed"]:
        return jsonify({"error": "no remaining trial credits"}), 403
    data, mime = result["document"], result["mime"]
    response = make_response(data)
    response.headers["Content-Type"] = mime
    response.headers["Content-Disposition"] = f'attachment; filename="english-year{year}-lesson{lesson_no:03d}.{fmt}"'
    response.headers["Cache-Control"] = "no-store, private"
    return response


@app.after_request
def preview_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cache-Control"] = "no-store, private"
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
