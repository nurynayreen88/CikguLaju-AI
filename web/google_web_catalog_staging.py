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
from web.provider_neutral_web_identity import from_verified_google_account

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
    config = _enabled_config()
    if config is None:
        return None, (jsonify({"error": "Google staging unavailable"}), 503)
    account_id = verify_google_identity_ticket(
        request.cookies.get(TICKET_COOKIE), config["secret"])
    if account_id is None:
        return None, (jsonify({"error": "Log masuk Google diperlukan"}), 401)
    try:
        profile = google_staging_account_profile(config, account_id)
        identity = from_verified_google_account(
            account_id, {**profile, "account_id": account_id})
        return identity, None
    except (GoogleAccountUnavailable, ValueError, TypeError):
        return None, (jsonify({"error": "Akaun Google belum boleh disahkan"}), 503)


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
            "google_verified": True,
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
        "google_verified": True, "staging_only": True,
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
