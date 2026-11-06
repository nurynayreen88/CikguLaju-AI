"""Authenticated Web gateway for Telegram's 59 draft Special Activity RPHs.

Web never loads the draft catalogue locally, invents SK/SP or makes a second
RPH engine.  A single Telegram-private API resolves the selected year, activity,
subject, digest and Word/PDF.  Free-trial authorization uses the same atomic
post-render quota RPC as ordinary RPH; failures do not claim to be free.
"""
from __future__ import annotations

import io
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPSHandler
from zipfile import ZipFile, BadZipFile

from flask import Blueprint, jsonify, request, send_file
from web.english_rpt_2027_http import _account, _has_paid_access
from web.native_verified_rpt_rph_client import _backend
from web.native_telegram_rph_client import BlockRedirects
from web.unified_rph_web import _teacher_context

bp = Blueprint("special_activity_web", __name__)
PREFIX = "/internal/rph/v1/aktiviti-khas/"
TRANSISI = "TRANSISI_TAHUN_1"
SELEPAS = "SELEPAS_TAMAT_SUKATAN"
SUBJECTS = frozenset((
    "Bahasa Melayu", "Bahasa Inggeris", "Matematik", "Sains",
    "Pendidikan Islam", "Pendidikan Moral", "Pendidikan Seni Visual",
    "Pendidikan Jasmani", "Pendidikan Kesihatan", "Pendidikan Muzik",
    "Bahasa Arab", "Sejarah", "Reka Bentuk dan Teknologi",
))
ID = re.compile(r"(?:K(?:0[1-9]|1\d|20)|S(?:0[1-9]|1[0-3])[ABC])")
DIGEST = re.compile(r"[a-f0-9]{64}")
MIMES = {
    "word":"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf":"application/pdf",
}
MAX_JSON = 180_000
MAX_DOC = 15 * 1024 * 1024


class SourceUnavailable(ValueError):
    pass


@bp.after_request
def private_no_cache(response):
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Vary"] = "Cookie"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _get_authenticated():
    account, err = _account()
    return account, err


def _selection(*, extra=False):
    params = request.args
    allowed = {"kind", "year", "phase", "subject"}
    if extra:
        allowed |= {"activity_id", "source_digest", "teacher_class", "teacher_date",
                    "teacher_start", "teacher_end", "teacher_students"}
    if any(key not in allowed or len(params.getlist(key)) != 1 for key in params):
        raise ValueError("Unknown or repeated selection field")
    kind, year = params.get("kind"), params.get("year")
    if kind not in (TRANSISI, SELEPAS) or not year or not re.fullmatch("[1-6]", year):
        raise ValueError("Invalid category or year")
    year = int(year)
    phase, subject = params.get("phase"), params.get("subject")
    if kind == TRANSISI:
        if year != 1 or subject is not None or (phase is not None and
            phase not in ("Fasa Penyesuaian", "Fasa Kesediaan")):
            raise ValueError("Transition only for Year 1")
    elif phase is not None or (subject is not None and subject not in SUBJECTS):
        raise ValueError("Invalid post-syllabus subject")
    result = {"kind":kind, "year":year}
    if phase is not None:
        result["phase"] = phase
    if subject is not None:
        result["subject"] = subject
    return result


def _private_request(endpoint, *, query=None, payload=None, fmt=None, opener=None):
    base, token = _backend()  # exact configured Telegram URL; no public fallback
    if endpoint not in ("subjects", "options", "preview", "render"):
        raise ValueError("Unapproved native endpoint")
    query_string = ("?" + urlencode(query)) if query else ""
    body = (json.dumps(payload, separators=(",",":"), ensure_ascii=False).encode("utf-8")
            if payload is not None else None)
    if body and len(body) > 3300:
        raise ValueError("Oversized selection")
    headers = {
        "Authorization":"Bearer " + token,
        "Accept":MIMES[fmt] if fmt else "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    req=Request(base + PREFIX + endpoint + query_string, data=body,
                headers=headers, method="POST" if body else "GET")
    transport=opener or build_opener(HTTPSHandler(), BlockRedirects())
    try:
        with transport.open(req, timeout=45 if fmt else 15) as response:
            if response.status != 200:
                raise SourceUnavailable("Native activity source unavailable")
            actual=response.headers.get("Content-Type","").split(";",1)[0].lower().strip()
            if actual != (MIMES[fmt] if fmt else "application/json"):
                raise SourceUnavailable("Native activity media type mismatch")
            data=response.read((MAX_DOC if fmt else MAX_JSON)+1)
        if len(data) > (MAX_DOC if fmt else MAX_JSON):
            raise SourceUnavailable("Oversized native activity response")
    except (HTTPError,URLError,OSError,TimeoutError) as exc:
        raise SourceUnavailable("Telegram special RPH source not reachable") from None
    if fmt:
        if fmt == "pdf" and not data.startswith(b"%PDF-"):
            raise SourceUnavailable("Invalid native PDF")
        if fmt == "word":
            if not data.startswith(b"PK"):
                raise SourceUnavailable("Invalid native DOCX")
            try:
                with ZipFile(io.BytesIO(data)) as archive:
                    if archive.testzip() or "word/document.xml" not in archive.namelist():
                        raise SourceUnavailable("Incomplete native DOCX")
            except (BadZipFile,OSError,ValueError):
                raise SourceUnavailable("Corrupt native DOCX") from None
        if len(data) < 900:
            raise SourceUnavailable("Empty native document")
        return data
    try:
        output=json.loads(data)
    except (ValueError,UnicodeError):
        raise SourceUnavailable("Invalid native JSON") from None
    if not isinstance(output,dict) or output.get("status")!="DRAFT_REVIEW":
        raise SourceUnavailable("Draft source status mismatch")
    return output


def _digest(response):
    digest=response.get("source_digest")
    if type(digest) is not str or not DIGEST.fullmatch(digest):
        raise SourceUnavailable("Native source signature unavailable")
    return digest


def _option_rows(result):
    digest=_digest(result)
    rows=result.get("items")
    if type(rows) is not list or not 0 < len(rows) <= 20:
        raise SourceUnavailable("No valid activity choices")
    ids=[]
    cleaned=[]
    for item in rows:
        if (type(item) is not dict or type(item.get("id")) is not str or
            not ID.fullmatch(item["id"]) or type(item.get("label")) is not str or
            not 0 < len(item["label"]) <= 170):
            raise SourceUnavailable("Untrusted activity choice")
        ids.append(item["id"])
        cleaned.append({"id":item["id"],"label":item["label"],
                        "phase":item.get("phase")})
    if len(set(ids)) != len(ids):
        raise SourceUnavailable("Duplicate activity choice")
    return cleaned, digest


@bp.get("/api/web/aktiviti-khas/subjects")
def subjects():
    account,err=_get_authenticated()
    if err is not None:
        return err
    try:
        selection=_selection()
        if selection["kind"]!=SELEPAS or set(selection)!={"kind","year"}:
            raise ValueError("Subjects selection must specify post-syllabus and year")
        payload=_private_request("subjects",query=selection)
        digest=_digest(payload)
        items=payload.get("items")
        if (type(items) is not list or len(items)!=len(SUBJECTS) or
            {x.get("value") for x in items if type(x) is dict}!=SUBJECTS):
            raise SourceUnavailable("Incomplete subject list")
        return jsonify({"items":items,"source_digest":digest,"status":"DRAF"})
    except ValueError as exc:
        if isinstance(exc,SourceUnavailable):
            return jsonify({"error":"Sumber aktiviti khas Telegram belum tersedia."}),503
        return jsonify({"error":"Pilihan aktiviti tidak sah."}),400


@bp.get("/api/web/aktiviti-khas/options")
def options():
    account,err=_get_authenticated()
    if err is not None:
        return err
    try:
        selected=_selection()
        if (selected["kind"]==TRANSISI and "phase" not in selected or
            selected["kind"]==SELEPAS and "subject" not in selected):
            raise ValueError("Choose phase/subject before activity")
        data=_private_request("options",query=selected)
        rows,digest=_option_rows(data)
        return jsonify({"items":rows,"source_digest":digest,"status":"DRAF",
                        "formats":["word","pdf"]})
    except ValueError as exc:
        if isinstance(exc,SourceUnavailable):
            return jsonify({"error":"Sumber aktiviti khas Telegram belum tersedia."}),503
        return jsonify({"error":"Pilihan aktiviti tidak sah."}),400


def _selected_render():
    selected=_selection(extra=True)
    ident=request.args.get("activity_id")
    digest=request.args.get("source_digest")
    if (type(ident) is not str or not ID.fullmatch(ident) or
        type(digest) is not str or not DIGEST.fullmatch(digest)):
        raise ValueError("Invalid source identity")
    if (selected["kind"]==TRANSISI and "phase" not in selected or
        selected["kind"]==SELEPAS and "subject" not in selected):
        raise ValueError("Missing activity category")
    selected_fields={k:v for k,v in selected.items()
                     if k in ("kind","year","phase","subject")}
    verified=_private_request("options",query=selected_fields)
    items,source_digest=_option_rows(verified)
    if digest!=source_digest or not any(i["id"]==ident for i in items):
        raise SourceUnavailable("Source changed or invalid activity")
    teacher=_teacher_context()
    subject=selected.get("subject")
    return ({"kind":selected["kind"],"year":selected["year"],
             "activity_id":ident,"subject":subject},teacher,digest)


@bp.get("/api/web/aktiviti-khas/<fmt>")
def document(fmt):
    if fmt not in MIMES:
        return jsonify({"error":"Format dokumen tidak sah."}),404
    account,err=_get_authenticated()
    if err is not None:
        return err
    paid=_has_paid_access(account)
    balance=account.get("free_remaining") if isinstance(account,dict) else None
    if not paid and (type(balance) is not int or not 0 <= balance <= 10):
        return jsonify({"error":"Baki janaan percuma tidak dapat disahkan."}),503
    if not paid and balance == 0:
        return jsonify({"error":"10 janaan percuma telah habis. Aktifkan langganan."}),403
    try:
        selection,teacher,digest=_selected_render()
        content=_private_request("render",payload={
            "selection":selection, "teacher":teacher, "format":fmt,
            "source_digest":digest,
        },fmt=fmt)
    except ValueError as exc:
        if isinstance(exc,SourceUnavailable):
            return jsonify({"error":"RPH Aktiviti Khas tidak dapat dijana melalui sumber Telegram."}),503
        return jsonify({"error":"Pilihan dan maklumat kelas RPH tidak sah."}),400
    trial_remaining=None
    if not paid:
        from web.rph_delivery_quota import authorize_rendered_document
        from web_v1_telegram_auth_routes import _config
        config=_config()
        if not config or config.get("account_backend")!="supabase":
            return jsonify({"error":"Sambungan kuota janaan tidak tersedia."}),503
        try:
            charged=authorize_rendered_document(
                account,account["telegram_user_id"],content,
                config["supabase_url"],config["supabase_key"])
        except Exception:
            return jsonify({"error":"Pengesahan kuota tidak berjaya; semak baki sebelum cuba semula."}),503
        if not charged["allowed"]:
            return jsonify({"error":"Baki janaan percuma telah habis.",
                            "remaining":charged["remaining"]}),403
        trial_remaining=charged["remaining"]
    result=send_file(io.BytesIO(content), mimetype=MIMES[fmt],
        as_attachment=True,
        download_name=("CIKGULAJU_RPH_AKTIVITI_KHAS_" +
                       selection["activity_id"] + "_TAHUN_" +
                       str(selection["year"]) + "_DRAF." +
                       ("docx" if fmt=="word" else "pdf")),
        conditional=False)
    result.headers["X-CikguLaju-Source-Status"]="DRAFT_REVIEW"
    result.headers["X-RPH-Generator"]="telegram-native"
    result.headers["X-RPH-Access-Mode"]="paid" if paid else "trial"
    if trial_remaining is not None:
        result.headers["X-RPH-Trial-Remaining"]=str(trial_remaining)
    return result
