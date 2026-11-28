"""Private Science 5P release candidate; NOT registered in production.

Use the real session and native catalogue contracts. Remains fail-closed
until a separate reviewed release decision and live-account QA. Candidate
documents retain the QA watermark. Never expose this as a production route.
"""
from __future__ import annotations
import os
from io import BytesIO
from flask import Blueprint, jsonify, request, send_file
from web.kp2027_math_canary_web import ORIGIN, debit_shared_trial
from web.kp2027_pilot_teacher_fields import EXTRA_FIELDS, TeacherFieldError
from web.rph_delivery_quota import authorize_rendered_document, has_active_paid_access
from web_v1_telegram_auth_routes import COOKIE, _config, _lookup
from web_v1_sessions import verify_session_ticket
from web import native_telegram_sequence_rph_client as native

URL = "/api/kssr/sk/science/5p/candidate/download"
AVAILABILITY_URL = "/api/kssr/sk/science/5p/candidate/available"
# No production release decision has been recorded.
RELEASE_APPROVED = False

def enabled():
    return RELEASE_APPROVED and os.getenv("CIKGULAJU_SCIENCE_5P_ENABLED") == "1"

def _inventory(year):
    from tools.audit_science_native_5p_documents_20261128 import inventory, support_inventory
    rows = inventory(year)
    return rows, support_inventory(year, rows)

def verified_selection(year, unit, lesson, rows):
    """Confirm original current native unit and lesson labels, order and pages."""
    import re
    if type(year) is not int or year not in (5,6):
        raise ValueError("Unsupported year")
    prefix = {5:"v",6:"w"}[year]
    if not isinstance(unit,str) or not re.fullmatch(prefix+r"[a-f0-9]{24}",unit):
        raise ValueError("Wrong native catalogue version")
    matches = [r for r in rows if r["lesson_id"] == lesson]
    if len(matches) != 1:
        raise ValueError("Unknown lesson")
    row = matches[0]
    groups = list(dict.fromkeys(r["unit"] for r in rows))
    units = native.list_native_units(year,"SCIENCE")
    if ([u["label"] for u in units] != groups
            or len({u["value"] for u in units}) != len(groups)
            or any(not re.fullmatch(prefix+r"[a-f0-9]{24}",u["value"]) for u in units)):
        raise ValueError("Native unit catalogue drift")
    expected_token = units[groups.index(row["unit"])]["value"]
    if expected_token != unit:
        raise ValueError("Wrong native unit")
    members = [r for r in rows if r["unit"] == row["unit"]]
    actual = native.list_native_lessons(year,"SCIENCE",unit)
    expected = [{"value":r["lesson_id"],
                 "label":f"PdP {int(r['lesson_id'].rsplit('-',1)[-1]):03d} • {r['title']}",
                 "textbook_ref":f"Buku Teks m/s {r['textbook_pages']}"} for r in members]
    if [{k:x.get(k) for k in ("value","label","textbook_ref")} for x in actual] != expected:
        raise ValueError("Native lesson catalogue drift")
    if not native.verified_native_sequence_available(year,"SCIENCE",unit,lesson):
        raise ValueError("Native RPH unavailable")
    return row

def create_blueprint(*, published=False):
    from web import science_5p_release as release
    bp = Blueprint("science_5p_release" if published else "science_5p_candidate",__name__)
    status="INTERNAL-REVIEWED" if published else "DRAFT-NOT-FOR-TEACHING"
    def route_enabled():
        return os.getenv(release.FLAG)=="1" if published else enabled()
    def lesson_enabled(y,cid):
        return release.is_released(y,cid) if published else enabled()
    def error(status,code):
        return jsonify(error=code,code=code),status
    @bp.after_request
    def private(resp):
        resp.headers["Cache-Control"]="no-store, private"
        resp.headers["X-Content-Type-Options"]="nosniff"
        resp.headers["Vary"]="Cookie"
        return resp
    def account_for_request():
        config=_config()
        if not config or config.get("account_backend")!="supabase":
            return None,None,None,error(503,"LOGIN_BACKEND_UNAVAILABLE")
        uid=verify_session_ticket(request.cookies.get(COOKIE),config["CIKGULAJU_WEB_SESSION_SECRET"])
        if type(uid) is not int or uid<=0:
            return None,None,None,error(401,"AUTH_REQUIRED")
        try:
            account=_lookup(config,uid)
        except Exception:
            return None,None,None,error(503,"ACCOUNT_LOOKUP_FAILED")
        if (not isinstance(account,dict) or account.get("authenticated") is not True
                or account.get("telegram_user_id")!=uid):
            return None,None,None,error(403,"ACCOUNT_NOT_VERIFIED")
        return config,uid,account,None

    @bp.get("/api/kssr/sk/science/5p/available" if published else AVAILABILITY_URL)
    def availability():
        if not route_enabled():
            return error(404,"SCIENCE_5P_UNAVAILABLE")
        config,uid,account,denied=account_for_request()
        if denied is not None:
            return denied
        if set(request.args) != {"year","subject","unit","lesson"} or any(len(request.args.getlist(k))!=1 for k in request.args):
            return error(400,"INVALID_SELECTION")
        y=request.args.get("year")
        if y not in ("5","6") or request.args.get("subject")!="SCIENCE":
            return error(404,"UNSUPPORTED_SELECTION")
        if not has_active_paid_access(account):
            remaining=account.get("free_remaining")
            if type(remaining) is not int or not 0<=remaining<=10:
                return error(503,"TRIAL_UNVERIFIED")
            if remaining==0:
                return error(403,"FREE_TRIAL_EXHAUSTED")
        if not lesson_enabled(int(y),request.args["lesson"]):
            return error(404,"SCIENCE_5P_UNAVAILABLE")
        try:
            rows,_=_inventory(int(y))
            verified_selection(int(y),request.args["unit"],request.args["lesson"],rows)
        except Exception:
            return error(503,"RPH_SOURCE_UNAVAILABLE")
        return jsonify(available=True,formats=["word","pdf"],status=status)
    @bp.post("/api/kssr/sk/science/5p/download" if published else URL)
    def download():
        if not route_enabled():
            return error(404,"SCIENCE_5P_UNAVAILABLE")
        if request.headers.get("Origin")!=ORIGIN:
            return error(403,"ORIGIN_REQUIRED")
        if not request.is_json or not 0<(request.content_length or 0)<=4096:
            return error(400,"INVALID_REQUEST")
        payload=request.get_json(silent=True)
        required={"year","subject","unit","lesson","format","rph_variant"}
        if (not isinstance(payload,dict) or not required.issubset(payload)
                or set(payload)-required-EXTRA_FIELDS):
            return error(400,"INVALID_REQUEST")
        year,fmt=payload["year"],payload["format"]
        if (type(year) is not int or year not in (5,6) or payload["subject"]!="SCIENCE"
                or payload["rph_variant"]!="5p" or fmt not in ("word","pdf")
                or not isinstance(payload["unit"],str) or not isinstance(payload["lesson"],str)):
            return error(404,"UNSUPPORTED_SELECTION")
        config,uid,account,denied=account_for_request()
        if denied is not None:
            return denied
        if not has_active_paid_access(account):
            balance=account.get("free_remaining")
            if type(balance) is not int or not 0<=balance<=10:
                return error(503,"TRIAL_UNVERIFIED")
            if balance==0:
                return error(403,"FREE_TRIAL_EXHAUSTED")
        if not lesson_enabled(year,payload["lesson"]):
            return error(404,"SCIENCE_5P_UNAVAILABLE")
        try:
            rows,support=_inventory(year)
            row=verified_selection(year,payload["unit"],payload["lesson"],rows)
            # Keep exact audited renderer and QA watermark in the candidate.
            from tools.science_5p_web_integration_qa_20261128 import render_selected
            output=render_selected(year,row,support[row["lesson_id"]],fmt,
                                   {k:payload[k] for k in EXTRA_FIELDS if k in payload},published=published)
            if not isinstance(output,bytes) or not output:
                raise ValueError("Empty document")
        except TeacherFieldError:
            return error(400,"INVALID_TEACHER_FIELDS")
        except Exception:
            return error(503,"RPH_RENDER_UNAVAILABLE")
        try:
            result=authorize_rendered_document(account,uid,output,config["supabase_url"],
                       config["supabase_key"],debit=debit_shared_trial)
        except Exception:
            return error(503,"TRIAL_CHARGE_UNCONFIRMED")
        if not result["allowed"]:
            return error(403,"FREE_TRIAL_EXHAUSTED")
        ext,mime=("docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document") if fmt=="word" else ("pdf","application/pdf")
        resp=send_file(BytesIO(output),mimetype=mime,as_attachment=True,
                       download_name=f"CIKGULAJU_{row['lesson_id']}_5P{'' if published else '_DRAF_QA'}.{ext}",conditional=False)
        resp.headers["X-RPH-QA-Status"]=status
        if result["remaining"] is not None:
            resp.headers["X-RPH-Trial-Remaining"]=str(result["remaining"])
        return resp
    return bp
