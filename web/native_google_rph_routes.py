"""Flag-off Google-only native RPH endpoints on CikguLaju's ORIGINAL Web.

Uses the same verified curriculum and Telegram-native renderer, with one
production-Supabase UUID account + private Word/PDF bundle ledger. New Google
users do NOT require a Telegram ID or a staging paid-status bridge.

Requires reviewed canonical principal + private RPH migrations and a separate
CIKGULAJU_NATIVE_GOOGLE_RPH_ENABLED=1 rollout. No live registration today.
"""
from io import BytesIO
import hashlib
import hmac
import os
import re
import time
import uuid
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, request, send_file

from web.google_native_canonical_login_routes import _config as login_config
from web.native_google_principal_store import (
    read_google_principal,canonical_rph_access,CanonicalAccountUnavailable)
from web_v1_canonical_sessions import COOKIE as GOOGLE_COOKIE,verify_google_principal_ticket
from web.native_google_rph_bundle_store import (
    prepare,publish,owned_job,ready_download,NativeBundleUnavailable)
from web.google_native_rph_bundle import (
    render_native_google_rph_bundle, NativeGoogleRPHNotReady, _teacher_fields)
from web.google_rph_bundle_job_store import selection_fingerprint

bp=Blueprint("cikgulaju_native_google_rph",__name__)
SUBJECTS={"ENGLISH":"English","MORAL":"Pendidikan Moral",
          "PJPK":"PJPK","PSV":"Pendidikan Seni Visual"}


def _config():
    if os.environ.get("CIKGULAJU_NATIVE_GOOGLE_RPH_ENABLED")!="1":
        return None
    cfg=login_config()
    if cfg is None:
        return None
    u=urlsplit(os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL",""))
    token=os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN","")
    if (u.scheme!="https" or u.hostname is None or u.port is not None
            or u.username or u.password or u.path not in ("","/")
            or u.query or u.fragment or u.hostname=="cikgulaju-web.onrender.com"
            or not isinstance(token,str) or len(token)<32):
        return None
    return cfg


def _actor():
    cfg=_config()
    if cfg is None:
        return None,None,(jsonify({"error":"Google RPH belum dibuka"}),503)
    account_id=verify_google_principal_ticket(
        request.cookies.get(GOOGLE_COOKIE),cfg["secret"])
    if account_id is None:
        return None,None,(jsonify({"error":"Login Google diperlukan"}),401)
    try:
        principal=read_google_principal(cfg,account_id)
        if principal["legacy_telegram_user_id"] is not None:
            # Linked users keep the existing Telegram Web RPH/credit path.
            return None,None,(jsonify({"error":
              "Akaun dipautkan menggunakan aliran RPH Telegram sedia ada"}),409)
        access=canonical_rph_access(cfg,principal)
        return cfg,{"principal":principal,"access":access},None
    except CanonicalAccountUnavailable:
        return None,None,(jsonify({"error":"Semakan akaun Google belum tersedia"}),503)


def _same_origin(cfg):
    return (request.headers.get("Origin")==cfg["origin"]
            and request.headers.get("Sec-Fetch-Site","same-origin")
            in ("same-origin","none"))


def _pick(payload):
    if not isinstance(payload,dict) or set(payload)!={"selection","teacher"}:
        raise ValueError("Invalid request")
    select=payload["selection"]
    teacher=_teacher_fields(payload["teacher"])
    if not isinstance(select,dict) or set(select)!={
            "year","subject","unit","lesson","component"}:
        raise ValueError("Invalid selection")
    year,subject,unit,lesson,comp=(select.get(k) for k in
                                  ("year","subject","unit","lesson","component"))
    if (type(year) is not int or year not in range(2,7)
            or subject not in SUBJECTS or not isinstance(unit,str)
            or not 0<len(unit)<=300 or not isinstance(lesson,str)
            or not 0<len(lesson)<=120
            or (subject=="PJPK" and comp not in ("PJ","PK"))
            or (subject!="PJPK" and comp is not None)):
        raise ValueError("Invalid source")
    from web.unified_rph_web import pdp_options
    rows=pdp_options(year,subject,unit,component=comp)
    if len([x for x in rows if x.get("value")==lesson])!=1:
        raise ValueError("Unverified curriculum lesson")
    return select,teacher


def _ticket(principal,job,digest,secret,*,now=None):
    at=int(time.time() if now is None else now)
    body="rphv2."+principal+"."+job+"."+digest+"."+str(at)
    mac=hmac.new(secret.encode(),body.encode("ascii"),hashlib.sha256).hexdigest()
    return body+"."+mac


def _verify(ticket,principal,digest,secret,*,now=None):
    if not isinstance(ticket,str) or len(ticket)>400:
        return None
    p=ticket.split(".")
    if len(p)!=6 or p[0]!="rphv2" or p[1]!=principal or p[3]!=digest:
        return None
    try:
        job=str(uuid.UUID(p[2]))
        at=int(p[4])
        now_at=int(time.time() if now is None else now)
    except (ValueError,TypeError,AttributeError):
        return None
    if (job!=p[2] or at<=0 or str(at)!=p[4] or at>now_at or now_at-at>3600
            or not re.fullmatch("[0-9a-f]{64}",p[5])):
        return None
    expected=hmac.new(secret.encode(),".".join(p[:-1]).encode("ascii"),
                      hashlib.sha256).hexdigest()
    return job if hmac.compare_digest(expected,p[5]) else None


def _links(job):
    base="/api/auth/google-native/rph/jobs/"+job
    return {"word":base+"/download/word","pdf":base+"/download/pdf"}


@bp.after_request
def _private(res):
    res.headers["Cache-Control"]="no-store, private"
    res.headers["Vary"]="Cookie"
    res.headers["X-Content-Type-Options"]="nosniff"
    return res


@bp.get("/api/auth/google-native/rph/capabilities")
def capabilities():
    cfg,actor,error=_actor()
    if error is not None:return error
    return jsonify({"enabled":True,"subjects":list(SUBJECTS),
                    "years":[2,3,4,5,6],
                    "access_mode":actor["access"]["rph_access_mode"],
                    "remaining":actor["access"]["rph_trial_remaining"]})


@bp.get("/api/auth/google-native/rph/catalog")
def catalog():
    cfg,actor,error=_actor()
    if error is not None:return error
    q=request.args
    if any(k not in ("year","subject","component","unit") for k in q):
        return jsonify({"error":"Parameter tidak sah"}),400
    if any(len(q.getlist(k))!=1 for k in q):
        return jsonify({"error":"Parameter berulang"}),400
    if not q:
        return jsonify({"years":[2,3,4,5,6],
                        "subjects":[{"value":k,"label":v} for k,v in SUBJECTS.items()]})
    year,subject,unit,comp=(q.get(k) for k in ("year","subject","unit","component"))
    if (not year or not year.isdigit() or int(year) not in range(2,7)
            or subject not in SUBJECTS
            or (subject=="PJPK" and comp not in ("PJ","PK"))
            or (subject!="PJPK" and comp is not None)
            or (unit is not None and (not unit.strip() or len(unit)>300))):
        return jsonify({"error":"Pilihan kurikulum tidak sah"}),400
    from web.unified_rph_web import pdp_options,unit_options
    try:
        rows=(unit_options(int(year),subject,component=comp) if unit is None
              else pdp_options(int(year),subject,unit,component=comp))
    except (ValueError,TypeError,OSError):
        return jsonify({"error":"Sumber kurikulum tidak tersedia"}),503
    if not isinstance(rows,list) or len(rows)>500:
        return jsonify({"error":"Pilihan kurikulum tidak disahkan"}),503
    return jsonify({"level":"lessons" if unit is not None else "units",
                    "items":[{"value":r["value"],"label":r["label"]}
                             for r in rows]})


@bp.post("/api/auth/google-native/rph/issue")
def issue():
    cfg,actor,error=_actor()
    if error is not None:return error
    if not _same_origin(cfg):return jsonify({"error":"Asal permintaan tidak sah"}),403
    if not request.is_json or not request.content_length or request.content_length>6000:
        return jsonify({"error":"Permintaan tidak sah"}),400
    try:
        selection,teacher=_pick(request.get_json(silent=True))
    except (ValueError,TypeError,KeyError,OSError):
        return jsonify({"error":"PdP atau maklumat guru tidak sah"}),400
    if actor["access"]["rph_access_mode"]=="exhausted":
        return jsonify({"error":"10 janaan percuma sudah habis","remaining":0}),403
    principal=actor["principal"]["account_id"]
    digest=selection_fingerprint(selection,teacher)
    job=str(uuid.uuid4())
    try:
        prepared=prepare(cfg,principal,job,digest)
    except (NativeBundleUnavailable,ValueError,CanonicalAccountUnavailable):
        return jsonify({"error":"Rekod janaan belum boleh disahkan"}),503
    return jsonify({"status":prepared["status"],"job_id":job,
                    "ticket":_ticket(principal,job,digest,cfg["secret"]),
                    "charged":False})


@bp.post("/api/auth/google-native/rph/generate")
def generate():
    cfg,actor,error=_actor()
    if error is not None:return error
    if not _same_origin(cfg):return jsonify({"error":"Asal permintaan tidak sah"}),403
    if not request.is_json or not request.content_length or request.content_length>7000:
        return jsonify({"error":"Permintaan tidak sah"}),400
    payload=request.get_json(silent=True)
    if not isinstance(payload,dict) or set(payload)!={"selection","teacher","ticket"}:
        return jsonify({"error":"Tiket dan PdP diperlukan"}),400
    try:
        selection,teacher=_pick({"selection":payload["selection"],
                                 "teacher":payload["teacher"]})
        digest=selection_fingerprint(selection,teacher)
        account=actor["principal"]["account_id"]
        job=_verify(payload["ticket"],account,digest,cfg["secret"])
        if job is None:return jsonify({"error":"Tiket janaan tamat atau tidak sah"}),403
        existing=owned_job(cfg,account,job)
        if existing is None:return jsonify({"error":"Rekod janaan tiada"}),404
        if existing["selection_sha256"]!=digest:
            return jsonify({"error":"Pilihan PdP tidak sepadan"}),403
        if existing["status"]=="ready":
            return jsonify({"status":"ready","already_ready":True,"job_id":job,
                            "downloads":_links(job),
                            "remaining":existing["remaining_after"]})
        output=render_native_google_rph_bundle(
            selection["year"],selection["subject"],selection["unit"],
            selection["lesson"],teacher,component=selection["component"])
        result=publish(cfg,account,job,digest,output["word"],output["pdf"])
    except (NativeBundleUnavailable,NativeGoogleRPHNotReady,
            CanonicalAccountUnavailable,ValueError,TypeError,KeyError,OSError):
        return jsonify({"error":"Janaan belum dapat disahkan. Semak job asal, jangan tekan berkali-kali."}),503
    if result.get("status")=="ready":
        return jsonify({"status":"ready","already_ready":bool(result.get("already_ready")),
                        "job_id":job,"downloads":_links(job),
                        "remaining":result.get("remaining")})
    if result.get("allowed") is False:
        return jsonify({"error":"10 janaan percuma sudah habis","remaining":0}),403
    return jsonify({"error":"Status janaan belum pasti. Semak job asal."}),503


@bp.get("/api/auth/google-native/rph/jobs/<job_id>/status")
def job_status(job_id):
    cfg,actor,error=_actor()
    if error is not None:return error
    if request.args:return jsonify({"error":"Parameter tidak dibenarkan"}),400
    try:
        job=owned_job(cfg,actor["principal"]["account_id"],job_id)
    except ValueError:return jsonify({"error":"ID janaan tidak sah"}),400
    except (NativeBundleUnavailable,CanonicalAccountUnavailable):
        return jsonify({"error":"Status belum tersedia"}),503
    if job is None:return jsonify({"error":"Janaan tiada"}),404
    ready=job["status"]=="ready"
    return jsonify({"status":job["status"],"ready":ready,
                    "downloads":_links(job_id) if ready else {}})


@bp.get("/api/auth/google-native/rph/jobs/<job_id>/download/<fmt>")
def download(job_id,fmt):
    cfg,actor,error=_actor()
    if error is not None:return error
    if request.args or fmt not in ("word","pdf"):
        return jsonify({"error":"Fail tidak sah"}),400
    try:
        result=ready_download(cfg,actor["principal"]["account_id"],job_id,fmt)
    except ValueError:return jsonify({"error":"ID janaan tidak sah"}),400
    except (NativeBundleUnavailable,CanonicalAccountUnavailable):
        return jsonify({"error":"Fail peribadi belum tersedia"}),503
    if result is None:return jsonify({"error":"RPH belum siap"}),404
    raw,mime=result
    return send_file(BytesIO(raw),mimetype=mime,as_attachment=True,
                     download_name="RPH_CikguLaju."+
                       ("docx" if fmt=="word" else "pdf"),max_age=0)
