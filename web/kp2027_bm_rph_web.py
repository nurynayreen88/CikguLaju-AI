"""Private Word/PDF RPH download for BM SK KP2027 Year 1: 353 RPT-aligned PdP.

The source is SHA-pinned and labelled SEMAKAN PELAKSANAAN, not academic final.
Reuse existing session and atomic trial quota. Never expose server credentials.
"""
from __future__ import annotations

from io import BytesIO
import os
from flask import Blueprint, jsonify, request, send_file

from web import kp2027_bm_rpt_aligned as bm


def five_p_enabled():
    return os.environ.get("CIKGULAJU_BM_KP2027_5P_ENABLED") == "1"
from web.kp2027_math_canary_web import ORIGIN, debit_shared_trial
from web.kp2027_pilot_teacher_fields import EXTRA_FIELDS, TeacherFieldError
from web.rph_delivery_quota import authorize_rendered_document, has_active_paid_access
from web_v1_telegram_auth_routes import COOKIE, _config, _lookup
from web_v1_sessions import verify_session_ticket


def create_blueprint():
    bp=Blueprint("kp2027_bm_sk_rpt_aligned",__name__)

    @bp.after_request
    def private_headers(resp):
        resp.headers["Cache-Control"]="no-store, private"
        resp.headers["X-Content-Type-Options"]="nosniff"
        resp.headers["Vary"]="Cookie"
        return resp

    def error(message,status,code):
        return jsonify({"error":message,"code":code}),status

    def account_for_request():
        config=_config()
        if not config or config.get("account_backend")!="supabase":
            return None,None,error("Semakan akses Web belum tersedia.",503,"LOGIN_BACKEND_UNAVAILABLE")
        uid=verify_session_ticket(request.cookies.get(COOKIE),config["CIKGULAJU_WEB_SESSION_SECRET"])
        if type(uid) is not int or uid<=0:
            return None,None,error("Sila log masuk terlebih dahulu.",401,"AUTH_REQUIRED")
        try:account=_lookup(config,uid)
        except Exception:
            return None,None,error("Semakan akaun belum tersedia.",503,"ACCOUNT_LOOKUP_FAILED")
        if (not isinstance(account,dict) or account.get("authenticated") is not True
                or account.get("telegram_user_id")!=uid):
            return None,None,error("Akaun belum disahkan.",403,"ACCOUNT_NOT_VERIFIED")
        return config,account,None

    @bp.get("/api/kp2027/sk/tahun-1/bahasa-melayu-sk/available")
    def available():
        _,_,denied=account_for_request()
        if denied is not None:return denied
        if not bm.ready():
            return error("Sumber RPH Bahasa Melayu SK masih dalam semakan.",503,"BM_SOURCE_UNAVAILABLE")
        records=bm.approved_source()
        return jsonify({
            "groups":{g:list(range(1,bm.COUNTS[g]+1)) for g in ("A","B")},
            "items":{g:[
                {"no":n,"unit":records[g][str(n)]["unit"],
                 "tajuk":records[g][str(n)]["title"],
                 "sp":records[g][str(n)]["sp_code"]}
                for n in range(1,bm.COUNTS[g]+1)
            ] for g in ("A","B")},
            "source":"kp2027-bm-sk-rpt2027-353-verified",
            "academic_status":"SEMAKAN PELAKSANAAN",
            "rph_variants":["lengkap","5p"] if five_p_enabled() else ["lengkap"],
        })

    @bp.post("/api/kp2027/sk/tahun-1/bahasa-melayu-sk/download")
    def download():
        if request.headers.get("Origin")!=ORIGIN:
            return error("Permintaan mesti daripada Web CikguLaju.",403,"ORIGIN_REQUIRED")
        if not request.is_json or not 0<(request.content_length or 0)<=1024:
            return error("Maklumat RPH tidak sah.",400,"INVALID_REQUEST")
        payload=request.get_json(silent=True)
        if (not isinstance(payload,dict) or not {"group","lesson","format"}.issubset(payload)
                or set(payload)-{"group","lesson","format","rph_variant"}-EXTRA_FIELDS):
            return error("Pilihan PdP atau maklumat RPH tidak lengkap.",400,"INVALID_SELECTION")
        group,number,fmt=payload["group"],payload["lesson"],payload["format"]
        variant=payload.get("rph_variant","lengkap")
        if variant not in ("lengkap","5p") or (variant=="5p" and not five_p_enabled()):
            return error("Pilihan format RPH belum tersedia.",404,"RPH_VARIANT_UNAVAILABLE")
        try:
            if fmt not in bm.FMTS:raise bm.Unavailable("Format tidak sah")
            bm.lesson(group,number)
        except (bm.Unavailable,TypeError,ValueError):
            return error("PdP yang dipilih belum tersedia.",404,"LESSON_NOT_AVAILABLE")
        config,account,denied=account_for_request()
        if denied is not None:return denied
        paid=has_active_paid_access(account)
        if not paid:
            remaining=account.get("free_remaining")
            if type(remaining) is not int or not 0<=remaining<=10:
                return error("Baki janaan tidak dapat disahkan.",503,"TRIAL_UNVERIFIED")
            if remaining==0:
                return error("10 janaan percuma telah habis. Aktifkan langganan.",403,"FREE_TRIAL_EXHAUSTED")
        try:
            fields={k:payload[k] for k in EXTRA_FIELDS if k in payload}
            if variant=="5p":
                from web import kp2027_bm_5p
                output=kp2027_bm_5p.render(group,number,fmt,fields)
            else:
                output=bm.render(group,number,fmt,fields)
        except TeacherFieldError as exc:
            return error(str(exc),400,"INVALID_TEACHER_FIELDS")
        except (bm.Unavailable,RuntimeError,OSError,ValueError,TypeError,KeyError,ImportError):
            return error("RPH belum berjaya disediakan. Kuota tidak ditolak.",503,"RPH_RENDER_UNAVAILABLE")
        trial_remaining=None
        if not paid:
            try:
                result=authorize_rendered_document(
                    account,account["telegram_user_id"],output,
                    config["supabase_url"],config["supabase_key"],debit=debit_shared_trial)
            except Exception:
                return error("Status kuota belum dapat disahkan. Sila semak baki akaun.",503,"TRIAL_CHARGE_UNCONFIRMED")
            if not result["allowed"]:
                return error("Baki janaan RPH telah habis.",403,"FREE_TRIAL_EXHAUSTED")
            trial_remaining=result["remaining"]
        ext,mime=bm.FMTS[fmt]
        resp=send_file(BytesIO(output),mimetype=mime,as_attachment=True,
            download_name=f"CIKGULAJU_RPH_BM_SK_KP2027_T1_{group}_PDP{number:03d}{'_5P' if variant=='5p' else ''}_SEMAKAN.{ext}",
            conditional=False)
        resp.headers["X-RPH-Curriculum"]="KP2027-Year1-BM-SK"
        resp.headers["X-RPH-QA-Status"]="SEMAKAN-PELAKSANAAN"
        resp.headers["X-RPH-Variant"]=variant
        if trial_remaining is not None:
            resp.headers["X-RPH-Trial-Remaining"]=str(trial_remaining)
        return resp
    return bp
