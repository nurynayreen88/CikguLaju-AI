"""Read-only, authenticated CikguLaju Web curriculum selector for Google staging.

Uses the SAME local verified standalone source inventory functions as the
existing Web /api/web/rph/availability path, rather than fabricated lessons.
No Telegram app or production database, no RPH documents or trial debits.
"""
from pathlib import Path
from flask import Blueprint, jsonify, make_response, redirect, request, send_file

from web.google_auth_staging_routes import _enabled_config, TICKET_COOKIE
from web.google_account_store import google_staging_account_profile, GoogleAccountUnavailable
from web_google_identity_sessions import verify_google_identity_ticket
from web.provider_neutral_web_identity import (
    from_verified_google_account, from_verified_linked_telegram_account)

bp = Blueprint("google_web_catalog_staging", __name__)
SUBJECTS = {
    "ENGLISH": "English",
    "MORAL": "Pendidikan Moral",
    "PJPK": "Pendidikan Jasmani dan Kesihatan",
    "PSV": "Pendidikan Seni Visual",
}
YEARS = tuple(range(2, 7))


@bp.after_request
def private_cache(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _actor():
    """One staging canonical account, two independently verified cookies.

    Telegram never receives a Google OAuth ticket. A linked Telegram session
    is rechecked against the private DB on every protected request. Conflicting
    valid Google and Telegram sessions fail closed rather than switching user.
    """
    config = _enabled_config()
    if config is None:
        return None, (jsonify({"error": "Web staging unavailable"}), 503)
    google_id = verify_google_identity_ticket(
        request.cookies.get(TICKET_COOKIE), config["secret"])
    telegram_uid, linked_id = None, None
    # Import locally: linking blueprint imports this module's _actor.
    from web.google_telegram_signin_staging_routes import (
        TELEGRAM_COOKIE, _verify_ticket, _linked_account)
    from web.google_telegram_link_staging_routes import (
        _link_config, StagingLinkUnavailable)
    telegram_uid = _verify_ticket(
        request.cookies.get(TELEGRAM_COOKIE), config["secret"])
    if telegram_uid is not None:
        pair = _link_config()
        if pair is None or pair[0]["supabase_url"] != config["supabase_url"]:
            return None, (jsonify({"error": "Sesi Telegram staging tidak tersedia"}), 503)
        try:
            linked_id = _linked_account(config, telegram_uid)
        except (StagingLinkUnavailable, KeyError, TypeError, ValueError):
            return None, (jsonify({"error": "Pemadanan Telegram belum boleh disahkan"}), 503)
        if linked_id is None:
            return None, (jsonify({"error": "Akaun Telegram tidak dipautkan"}), 401)
    if google_id is not None and linked_id is not None and google_id != linked_id:
        return None, (jsonify({"error": "Dua sesi berlainan. Log keluar salah satu akaun dahulu."}), 403)
    account_id = google_id or linked_id
    if account_id is None:
        return None, (jsonify({"error": "Log masuk Google atau Telegram diperlukan"}), 401)
    try:
        profile = google_staging_account_profile(config, account_id)
        trusted = {**profile, "account_id": account_id}
        identity = (from_verified_google_account(account_id, trusted)
                    if google_id is not None else
                    from_verified_linked_telegram_account(telegram_uid, account_id, trusted))
        return identity, None
    except (GoogleAccountUnavailable, ValueError, TypeError):
        return None, (jsonify({"error": "Akaun staging belum boleh disahkan"}), 503)


@bp.get("/google-staging-web")
def staging_web():
    actor, failure = _actor()
    if failure is not None:
        if failure[1] == 401:
            return redirect("/google-staging-login", code=303)
        return failure
    response = make_response(send_file(
        Path(__file__).with_name("google_staging_web.html"),
        mimetype="text/html", max_age=0))
    return response


@bp.get("/api/google-staging/web/catalog")
def catalog():
    actor, failure = _actor()
    if failure is not None:
        return failure
    args = request.args
    if any(key not in ("year", "subject", "component", "unit") for key in args):
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    if any(len(args.getlist(key)) != 1 for key in args):
        return jsonify({"error": "Parameter berulang"}), 400
    if not args:
        return jsonify({
            "years": list(YEARS),
            "subjects": [{"value": key, "label": label}
                         for key, label in SUBJECTS.items()],
            "google_verified": actor.provider == "google",
            "identity_verified": True,
            "auth_provider": actor.provider,
            "staging_only": True,
            "rph_generation_enabled": False,
            "note": "Katalog metadata berasaskan sumber Web sedia ada; tiada janaan atau potongan kredit."
        })
    year = args.get("year")
    subject = args.get("subject")
    unit = args.get("unit")
    component = args.get("component")
    if (year is None or len(year) != 1 or not year.isdigit()
            or int(year) not in YEARS
            or subject not in SUBJECTS
            or (subject == "PJPK" and component not in ("PJ", "PK"))
            or (subject != "PJPK" and component is not None)):
        return jsonify({"error": "Pilihan Tahun/Subjek/Komponen tidak sah"}), 400
    if unit is not None and (not unit.strip() or len(unit) > 300):
        return jsonify({"error": "Unit tidak sah"}), 400
    from web.unified_rph_web import unit_options, pdp_options
    try:
        if unit is None:
            records = unit_options(int(year), subject, component=component)
        else:
            # The source returns public lesson metadata, not document content.
            records = pdp_options(int(year), subject, unit, component=component)
    except (ValueError, TypeError, OSError):
        return jsonify({"error": "Sumber kurikulum belum tersedia"}), 503
    if not isinstance(records, list) or len(records) > 500:
        return jsonify({"error": "Senarai kurikulum tidak sah"}), 503
    if unit is not None:
        # Never leak raw file paths or grant download via metadata.
        records = [{"value": row["value"], "label": row["label"],
                    "lesson_no": row["lesson_no"],
                    "textbook_ref": row.get("textbook_ref") or None,
                    "download_enabled": False}
                   for row in records]
    return jsonify({
        "items": records,
        "level": "lessons" if unit is not None else "units",
        "google_verified": actor.provider == "google",
        "identity_verified": True, "auth_provider": actor.provider,
        "staging_only": True,
        "rph_generation_enabled": False,
        "note": "RPH hanya tersedia selepas integrasi kuota bersama disahkan."
    })


@bp.get("/api/google-staging/web/materials")
def materials():
    actor, failure = _actor()
    if failure is not None:
        return failure
    if not request.args or set(request.args) != {
            "year", "subject", "unit", "lesson", "component"}:
        return jsonify({"error": "Pilihan PdP perlu lengkap"}), 400
    from web.unified_rph_web import pdp_options
    args = request.args
    if any(len(args.getlist(k)) != 1 for k in args):
        return jsonify({"error": "Parameter tidak sah"}), 400
    y, subj, comp, unit, lesson = (args.get(k) for k in
                                  ("year", "subject", "component", "unit", "lesson"))
    if (not y or not y.isdigit() or int(y) not in YEARS
            or subj not in SUBJECTS or not isinstance(unit, str)
            or not unit.strip() or len(unit) > 300
            or not isinstance(lesson, str) or len(lesson) > 120
            or (subj == "PJPK" and comp not in ("PJ", "PK"))
            or (subj != "PJPK" and comp != "")):
        return jsonify({"error": "Pilihan PdP tidak sah"}), 400
    items = pdp_options(int(y), subj, unit,
                        component=comp if comp else None)
    matched = [item for item in items if item["value"] == lesson]
    if len(matched) != 1:
        return jsonify({"error": "PdP tidak dijumpai dalam sumber Web"}), 404
    return jsonify({
        "lesson": matched[0]["label"],
        "textbook_ref": matched[0].get("textbook_ref") or None,
        "materials": [
            {"label": "RPH Word", "available": False},
            {"label": "RPH PDF", "available": False},
        ],
        "staging_only": True,
        "rph_generation_enabled": False,
        "trial_debited": False,
        "note": "Pautan muat turun tidak diaktifkan sebelum akaun dan potongan kuota disatukan."
    })


@bp.get("/api/google-staging/web/access/status")
def linked_staging_access():
    """Staging read-only access status for either verified account provider.

    Never copy, infer, or assert production Telegram entitlements. Production
    subscriptions must be reconciled through a separate reviewed migration.
    """
    actor, failure = _actor()
    if failure is not None:
        return failure
    if request.args:
        return jsonify({"error": "Parameter tidak dibenarkan"}), 400
    from web.google_payment_store import web_payment_access, PaymentUnavailable
    from web.provider_neutral_web_identity import canonical_staging_account
    try:
        account_id = canonical_staging_account(actor)
        profile = google_staging_account_profile(_enabled_config(), account_id)
        access = web_payment_access(_enabled_config(), account_id)
        if (type(profile.get("trial_remaining")) is not int
                or not 0 <= profile["trial_remaining"] <= 10
                or type(access.get("payment_access_active")) is not bool
                or not isinstance(access.get("active_plans"), list)
                or len(access["active_plans"]) > 100):
            raise ValueError("Invalid staging entitlements")
        plans = []
        for plan in access["active_plans"]:
            if (not isinstance(plan, dict)
                    or plan.get("plan_code") not in ("rakan_pembangun", "monthly", "annual")
                    or (plan.get("valid_until") is not None
                        and (not isinstance(plan["valid_until"], str)
                             or len(plan["valid_until"]) > 50))):
                raise ValueError("Invalid staging entitlement")
            plans.append({"plan_code": plan["plan_code"],
                          "valid_until": plan.get("valid_until")})
    except (PaymentUnavailable, GoogleAccountUnavailable,
            ValueError, KeyError, TypeError):
        return jsonify({"error": "Status akses staging belum boleh disahkan"}), 503
    from web.staging_production_paid_status_client import verified_linked_paid_status
    # Read-only comparison to production, if the separate bridge is enabled.
    # NEVER use these verified fields as authorization to create a staging
    # entitlement, approve payment or bypass the atomic RPH quota ledger.
    production = verified_linked_paid_status(actor, _enabled_config())
    return jsonify({
        "identity_verified": True, "auth_provider": actor.provider,
        "staging_only": True, "trial_remaining": profile["trial_remaining"],
        "staging_payment_access_active": access["payment_access_active"],
        "staging_active_plans": plans,
        "production_entitlements_synced": False,
        "real_payments_enabled": False,
        "note": "Status langganan produksi dibaca secara berasingan; tiada kelulusan atau pemindahan hak akses automatik.",
        **production,
    })
