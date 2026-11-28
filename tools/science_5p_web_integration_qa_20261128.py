"""Isolated Flask integration harness for Science 5P drafts.

Never registered by the production launcher. All account, mapping and
debit dependencies MUST be explicitly injected by test callers. Refuse
non-testing Flask apps and production Render services.
"""
import os
from io import BytesIO
from hashlib import sha256
import json
from flask import Blueprint, current_app, jsonify, request, send_file
from web.kp2027_pilot_teacher_fields import EXTRA_FIELDS, TeacherFieldError, parse_teacher_fields
from web.rph_delivery_quota import authorize_rendered_document, has_active_paid_access
from web.rph_5p_v5_layout import Palette, render_word
from tools.audit_science_native_5p_documents_20261128 import ROOT, DRAFT, fields, display_fields, read
from tools.audit_science_5p_native_pdf_20261128 import render_pdf
from tools.science_5p_native_selection_preflight_20261128 import verify_selection

ORIGIN = "https://cikgulaju-web.onrender.com"
URL = "/qa/science-5p/download"
FMTS = {"word":("docx","application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "pdf":("pdf","application/pdf")}

def render_selected(year, row, support, fmt, teacher, *, published=False):
    if published:
        from web.science_5p_release import is_released
        if not is_released(year,row['lesson_id']):
            raise ValueError('Science lesson not approved for publication')
    parsed = parse_teacher_fields(teacher)
    profile = dict(zip(("class","date","time","students"),
                       (parsed[k] for k in ("Kelas:","Tarikh:","Masa:","Bil. Murid:"))))
    s,c,raw=fields(year,row,support)
    s,c,raw=display_fields(s,c,raw)
    # QA personalization: never invent the number of pupils who have mastered.
    if parsed["_reflection_mode"] == "manual":
        s["reflection"] = parsed["_reflection"]
    else:
        s["reflection"] = ("Bil. murid menguasai:    Belum menguasai:\nKriteria: "+s["criteria"]
                           +"\nTindakan: Pemulihan seperti di atas dan pentaksiran semula.")
    raw=json.dumps(s,ensure_ascii=False,sort_keys=True).encode("utf-8")
    c["source_sha256"]=sha256(raw).hexdigest()
    colors=[r for r in read(ROOT/"web/rph_login_canonical_layout_20261121.json")["subjects"] if r["subject_code"]=="SCIENCE"]
    if len(colors)!=1:
        raise ValueError("Science palette unavailable")
    color=colors[0]
    palette=Palette(color["strong"].lstrip("#"),color["tone"].lstrip("#"),color["tone"].lstrip("#"),"9AB2B7")
    heading=f"SAINS SK\nTAHUN {year}" if published else f"SAINS SK\nTAHUN {year}\n{DRAFT}"
    if fmt=="word":
        return render_word(s,c,source_bytes=raw,palette=palette,subject_heading=heading,profile=profile)
    if fmt=="pdf":
        return render_pdf(s,c,raw,profile,palette,heading)
    raise ValueError("Unsupported format")

def create_test_blueprint(*, account_for_request, mapping_for_year, rows, support, debit, renderer=render_selected):
    if not all(callable(x) for x in (account_for_request,mapping_for_year,debit,renderer)):
        raise ValueError("Explicit test dependencies required")
    bp=Blueprint("science_5p_qa",__name__)

    @bp.before_request
    def guard():
        if not current_app.testing or os.getenv("RENDER_SERVICE_ID") in {
                "srv-dbm5go8u01pc738f40cg","srv-dah3b8lbedkc738ugqt0"}:
            return jsonify(error="QA route unavailable"),404

    @bp.after_request
    def headers(response):
        response.headers["Cache-Control"]="no-store, private"
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Vary"]="Cookie"
        return response

    @bp.post(URL)
    def download():
        def err(status,code):
            return jsonify(error=code),status
        if request.headers.get("Origin")!=ORIGIN:
            return err(403,"ORIGIN_REQUIRED")
        if not request.is_json or not 0<(request.content_length or 0)<=4096:
            return err(400,"INVALID_REQUEST")
        payload=request.get_json(silent=True)
        required={"year","subject","unit","lesson","format","rph_variant"}
        if (not isinstance(payload,dict) or not required.issubset(payload)
            or set(payload)-required-EXTRA_FIELDS):
            return err(400,"INVALID_REQUEST")
        year=payload["year"]; fmt=payload["format"]
        if (type(year) is not int or year not in (5,6) or payload["subject"]!="SCIENCE"
            or payload["rph_variant"]!="5p" or not isinstance(fmt,str) or fmt not in FMTS):
            return err(404,"UNSUPPORTED_SELECTION")
        uid, account=account_for_request(request)
        if type(uid) is not int or uid<=0:
            return err(401,"AUTH_REQUIRED")
        if (not isinstance(account,dict) or account.get("authenticated") is not True
            or account.get("telegram_user_id")!=uid):
            return err(403,"ACCOUNT_NOT_VERIFIED")
        if not has_active_paid_access(account):
            balance=account.get("free_remaining")
            if type(balance) is not int or not 0<=balance<=10:
                return err(503,"TRIAL_UNVERIFIED")
            if balance==0:
                return err(403,"FREE_TRIAL_EXHAUSTED")
        try:
            selected=verify_selection(mapping_for_year(year),year,payload["unit"],payload["lesson"])
        except (ValueError,KeyError,TypeError):
            return err(404,"UNMAPPED_SELECTION")
        try:
            cid=selected["lesson"]
            output=renderer(year,rows[cid],support[cid],fmt,{k:payload[k] for k in EXTRA_FIELDS if k in payload})
            if not isinstance(output,bytes) or not output:
                raise ValueError("Empty document")
        except TeacherFieldError:
            return err(400,"INVALID_TEACHER_FIELDS")
        except (RuntimeError,OSError,ValueError,TypeError,KeyError,ImportError):
            return err(503,"RENDER_FAILED")
        try:
            result=authorize_rendered_document(account,uid,output,"https://example.invalid","qa-only",debit=debit)
        except Exception:
            return err(503,"QUOTA_UNCONFIRMED")
        if not result["allowed"]:
            return err(403,"FREE_TRIAL_EXHAUSTED")
        ext,mime=FMTS[fmt]
        response=send_file(BytesIO(output),mimetype=mime,as_attachment=True,
                           download_name=f"CIKGULAJU_{cid}_5P_DRAF_QA.{ext}",conditional=False)
        response.headers["X-RPH-QA-Status"]="DRAFT-NOT-FOR-TEACHING"
        if result["remaining"] is not None:
            response.headers["X-RPH-Trial-Remaining"]=str(result["remaining"])
        return response
    return bp
