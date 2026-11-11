"""CikguLaju Web payments backed by the SAME Telegram Supabase approval queue.

The server authenticates signed Telegram sessions, uses Telegram's configured
payment QR and plan catalog, and inserts a pending request ONLY AFTER receipt
bytes were accepted by Telegram. Admin confirmation and entitlement assignment
remain in Telegram's existing payment workflow.

No anonymous user IDs, public Storage links, duplicate pending rows, automatic
approval, paywall bypass, or new database columns.
"""
import json
import mimetypes
import os
import re
import uuid
from datetime import datetime, timezone
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPSHandler
from flask import Blueprint, Response, jsonify, request

from web.teacher_profile_routes import _auth
from web.teacher_profile_store import ProfileUnavailable, NoRedirect

bp = Blueprint("cikgulaju_web_payments", __name__)
MAX_RECEIPT = 4 * 1024 * 1024
MAX_REPLY = 32768
CONTENT_TYPES = {"application/pdf": ".pdf", "image/png": ".png",
                 "image/jpeg": ".jpg", "image/webp": ".webp"}


@bp.after_request
def private_response(resp):
    resp.headers["Cache-Control"] = "no-store, private"
    resp.headers["Vary"] = "Cookie"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


def _safe_host(value):
    parsed = urlsplit(value or "")
    if (parsed.scheme != "https" or not parsed.hostname or parsed.port is not None
            or parsed.username or parsed.password or parsed.path not in ("", "/")
            or parsed.query or parsed.fragment):
        raise ProfileUnavailable("Sambungan bayaran tidak disahkan")
    return value.rstrip("/")


def _source(path, *, expect="json", opener=None):
    base = _safe_host(os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", ""))
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    if len(token) < 32:
        raise ProfileUnavailable("Sumber bayaran belum disambungkan")
    req = Request(base + path,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/json" if expect == "json" else "image/*"},
        method="GET")
    try:
        with (opener or build_opener(HTTPSHandler(), NoRedirect())).open(req, timeout=12) as resp:
            if resp.status != 200:
                raise ProfileUnavailable("Sumber bayaran tidak tersedia")
            mime = resp.headers.get("Content-Type", "").split(";")[0].lower()
            length = 16384 if expect == "json" else 2 * 1024 * 1024
            data = resp.read(length + 1)
            if len(data) > length:
                raise ProfileUnavailable("Respons bayaran terlalu besar")
            if expect == "json":
                if mime != "application/json":
                    raise ProfileUnavailable("Jenis katalog bayaran tidak sah")
                return json.loads(data)
            if mime not in ("image/png", "image/jpeg"):
                raise ProfileUnavailable("Format QR tidak sah")
            if not data.startswith(b"\x89PNG\r\n\x1a\n") and not data.startswith(b"\xff\xd8\xff"):
                raise ProfileUnavailable("Fail QR tidak sah")
            return data, mime
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        raise ProfileUnavailable("Sumber bayaran Telegram belum tersedia") from None


def validated_plans(catalog):
    if not isinstance(catalog, dict) or catalog.get("mode") != "manual_receipt_review":
        raise ProfileUnavailable("Katalog bayaran tidak disahkan")
    # A proof file_id is only readable by the bot that originally uploaded
    # the file. Refuse any Web payment if the widget bot is not the real
    # Telegram production bot that owns the QR/admin payment queue.
    web_token=os.environ.get("CIKGULAJU_WEB_BOT_TOKEN","")
    match=re.fullmatch(r"([0-9]{5,15}):[A-Za-z0-9_-]{20,}",web_token)
    if not match or catalog.get("telegram_bot_id") != match.group(1):
        raise ProfileUnavailable("Bot Web dan Telegram tidak sepadan")
    items = catalog.get("plans")
    if not isinstance(items, list) or len(items) != 1:
        raise ProfileUnavailable("Hanya Rakan Pembangun RM20 ditawarkan")
    expected = {"rakan_pembangun": "20.00"}
    result = {}
    for entry in items:
        if (not isinstance(entry, dict) or entry.get("code") not in expected
                or entry.get("amount") != expected[entry.get("code")]
                or entry.get("code") in result):
            raise ProfileUnavailable("Pakej bayaran tidak sepadan dengan Telegram")
        result[entry["code"]] = {"code":entry["code"], "amount":entry["amount"],
                                  "label":str(entry.get("label") or "")[:90],
                                  "description":str(entry.get("description") or "")[:160]}
    if set(result) != set(expected):
        raise ProfileUnavailable("Pakej bayaran tidak lengkap")
    return result


def validated_rakan_status(catalog):
    """Only expose Telegram's verified one-decimal percentage, not capacity."""
    percent = catalog.get("progress_percentage") if isinstance(catalog, dict) else None
    open_enrollment = catalog.get("rakan_open") if isinstance(catalog, dict) else None
    if (not isinstance(percent, str) or not re.fullmatch(r"(?:[0-9]{1,2}\.[0-9]|100\.0)%", percent)
            or type(open_enrollment) is not bool):
        raise ProfileUnavailable("Peratus Rakan Pembangun belum dapat disahkan")
    value = float(percent[:-1])
    if (value < 0 or value > 100
            or (value == 100.0 and open_enrollment)):
        raise ProfileUnavailable("Status penyertaan tidak sepadan")
    return percent, open_enrollment


def _is_member(conf, uid):
    """Recheck the authenticated, paid lifetime entitlement before charging."""
    from web_v1_telegram_auth_routes import _lookup
    try:
        account = _lookup(conf, uid)
    except Exception:
        raise ProfileUnavailable("Status keahlian tidak dapat disemak") from None
    if not isinstance(account, dict) or account.get("telegram_user_id") != uid:
        raise ProfileUnavailable("Akaun berdaftar tidak dapat disahkan")
    return account.get("rakan_pembangun") is True


def _payment_rest(conf, method, *, query="", body=None, opener=None):
    base = _safe_host(conf["supabase_url"])
    token = conf["supabase_key"]
    if not isinstance(token, str) or len(token) < 20:
        raise ProfileUnavailable("Sambungan rekod bayaran tidak sah")
    url = base + "/rest/v1/bot_payment_requests"
    if query:
        url += "?" + query
    headers = {"apikey":token, "Authorization":"Bearer "+token,
               "Accept":"application/json", "Content-Type":"application/json"}
    if method == "POST":
        headers["Prefer"]="return=representation"
    payload=json.dumps(body,separators=(",",":"),ensure_ascii=False).encode("utf-8") if body is not None else None
    req=Request(url,data=payload,method=method,headers=headers)
    try:
        with (opener or build_opener(HTTPSHandler(),NoRedirect())).open(req,timeout=12) as resp:
            raw=resp.read(MAX_REPLY+1)
            if len(raw)>MAX_REPLY or resp.status not in (200,201):
                raise ProfileUnavailable("Rekod pembayaran tidak tersedia")
            rows=json.loads(raw)
            if not isinstance(rows,list):
                raise ProfileUnavailable("Rekod pembayaran tidak sah")
            return rows
    except HTTPError as exc:
        if exc.code in (409,412):
            raise PaymentConflict("Permohonan bayaran lain masih Pending") from None
        raise ProfileUnavailable("Rekod pembayaran tidak dapat dikemaskini") from None
    except (OSError,ValueError,TypeError):
        raise ProfileUnavailable("Sambungan rekod pembayaran tidak tersedia") from None


class PaymentConflict(Exception):
    pass


def _existing(conf, uid, *, opener=None):
    if type(uid) is not int or uid < 1:
        raise ProfileUnavailable("Akaun tidak sah")
    # The partial unique DB index guarantees at most one Pending per user;
    # read it directly, never miss an old Pending behind newer history rows.
    query=urlencode({
        "select":"id,chat_id,amount,status,submitted_at,proof_received_at",
        "chat_id":"eq."+str(uid),
        "status":"eq.pending","order":"id.desc", "limit":"2"})
    rows=_payment_rest(conf,"GET",query=query,opener=opener)
    if any(not isinstance(r,dict) or r.get("chat_id") != str(uid) for r in rows):
        raise ProfileUnavailable("Padanan rekod pembayaran tidak sah")
    return rows


def _validate_receipt(content, mime):
    if mime not in CONTENT_TYPES or not isinstance(content,bytes) or not 700<=len(content)<=MAX_RECEIPT:
        raise ValueError("Resit mestilah gambar atau PDF berukuran maksimum 4 MB")
    if mime=="application/pdf" and content.startswith(b"%PDF-"):
        return ".pdf"
    if mime=="image/jpeg" and content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if mime=="image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if mime=="image/webp" and content.startswith(b"RIFF") and content[8:12]==b"WEBP":
        return ".webp"
    raise ValueError("Fail resit tidak sepadan dengan formatnya")


def _telegram_document(conf, uid, raw, ext, *, opener=None):
    """Telegram stores the proof as its own immutable file_id, not public Storage."""
    token=os.environ.get("CIKGULAJU_WEB_BOT_TOKEN","")
    if not isinstance(token,str) or not re.fullmatch(r"[0-9]{5,15}:[A-Za-z0-9_-]{20,}",token):
        raise ProfileUnavailable("Sambungan resit ke bot tidak disahkan")
    if type(uid) is not int or uid<1:
        raise ProfileUnavailable("Akaun tidak sah")
    boundary="cikgulajuweb"+uuid.uuid4().hex
    filename="CikguLaju_Resit_Web"+ext
    mime=next(k for k,v in CONTENT_TYPES.items() if v==ext)
    def field(name,value):
        return (("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+
            name+"\"\r\n\r\n"+value+"\r\n").encode("utf-8"))
    header=(("--"+boundary+"\r\nContent-Disposition: form-data; name=\"document\"; filename=\""+
        filename+"\"\r\nContent-Type: "+mime+"\r\n\r\n").encode("utf-8"))
    data=(field("chat_id",str(uid))
          +field("caption","Resit bayaran melalui Web CikguLaju. Permohonan masih perlu pengesahan admin.")
          +header+raw+b"\r\n"+("--"+boundary+"--\r\n").encode())
    url="https://api.telegram.org/bot"+token+"/sendDocument"
    req=Request(url,method="POST",data=data,headers={
        "Content-Type":"multipart/form-data; boundary="+boundary,
        "Content-Length":str(len(data)), "Accept":"application/json"})
    try:
        with (opener or build_opener(HTTPSHandler(),NoRedirect())).open(req,timeout=28) as resp:
            if resp.status != 200:
                raise ProfileUnavailable("Resit gagal dihantar ke Telegram")
            reply=json.loads(resp.read(MAX_REPLY+1))
    except (HTTPError,URLError,OSError,ValueError,TypeError):
        raise ProfileUnavailable("Resit tidak dapat disimpan oleh Telegram. Pastikan bot pernah dibuka.") from None
    item=reply.get("result") if isinstance(reply,dict) and reply.get("ok") is True else None
    document=item.get("document") if isinstance(item,dict) else None
    if (not isinstance(document,dict) or not document.get("file_id")
            or type(item.get("message_id")) is not int or item.get("chat",{}).get("id")!=uid):
        raise ProfileUnavailable("Telegram belum mengesahkan penyimpanan resit")
    return {
        "file_id":str(document["file_id"]),
        "unique_id":str(document.get("file_unique_id") or ""),
        "message_id":item["message_id"],"mime":str(document.get("mime_type") or mime)[:100],
    }


def _notify_telegram_admin_review(uid, request_id, *, opener=None):
    """Notify admin only *after* the durable Web proof and Pending row exist.

    Telegram independently reloads and verifies the precise payment, user,
    receipt file_id and Pending status. No approval or entitlement mutation.
    This private API uses the same token as the already-protected catalog API.
    """
    if (type(uid) is not int or not 0 < uid < 10**18
            or type(request_id) is not int or not 0 < request_id < 10**18):
        raise ProfileUnavailable("Identiti bayaran belum disahkan")
    base = _safe_host(os.environ.get("CIKGULAJU_AUTHORITATIVE_API_URL", ""))
    token = os.environ.get("CIKGULAJU_AUTHORITATIVE_API_TOKEN", "")
    if not isinstance(token, str) or len(token) < 32:
        raise ProfileUnavailable("Sambungan notifikasi admin belum tersedia")
    body = json.dumps({"request_id": request_id, "telegram_user_id": uid},
                      separators=(",", ":")).encode("utf-8")
    req = Request(base + "/internal/payment/v1/admin-review-notify",
                  method="POST", data=body,
                  headers={"Authorization": "Bearer " + token,
                           "Content-Type": "application/json",
                           "Accept": "application/json"})
    try:
        with (opener or build_opener(HTTPSHandler(), NoRedirect())).open(req, timeout=25) as resp:
            if resp.status != 200 or resp.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                raise ProfileUnavailable("Telegram tidak mengesahkan penghantaran notifikasi")
            raw = resp.read(4097)
        if len(raw) > 4096:
            raise ProfileUnavailable("Respons notifikasi terlalu besar")
        data = json.loads(raw)
        if (not isinstance(data, dict) or data.get("notified") is not True
                or data.get("request_id") != request_id
                or data.get("review") != "admin_only"):
            raise ProfileUnavailable("Telegram tidak mengesahkan notifikasi admin")
        return True
    except (HTTPError, URLError, OSError, TypeError, ValueError):
        raise ProfileUnavailable("Makluman Telegram admin belum dihantar") from None


def _status_rows(rows):
    for item in rows:
        if item.get("status") == "pending":
            return {"pending": True, "id": item["id"],
                    "amount": str(item["amount"]),
                    "submitted_at": item.get("submitted_at"),
                    "proof_received_at":item.get("proof_received_at")}
    return {"pending": False}


@bp.get("/api/web/payment/catalog")
def payment_catalog():
    conf,uid,err=_auth()
    if err is not None:
        return err
    try:
        catalog=_source("/internal/payment/v1/catalog")
        plans=validated_plans(catalog)
        percentage,rakan_open=validated_rakan_status(catalog)
        rows=_existing(conf,uid)
        member=_is_member(conf,uid)
    except (ProfileUnavailable,PaymentConflict):
        return jsonify({"error":"Sumber atau status Rakan Pembangun belum tersedia"}),503
    return jsonify({"plans":list(plans.values()),"status":_status_rows(rows),
                    "progress_percentage":percentage,"rakan_open":rakan_open,
                    "already_member":member,
                    "qr_available":rakan_open and not member and not _status_rows(rows)["pending"],
                    "note":"Pending hanya selepas resit sebenar. Kelulusan admin diperlukan."})


@bp.get("/api/web/payment/qr")
def payment_qr():
    conf,uid,err=_auth()
    if err is not None:
        return err
    try:
        rows=_existing(conf,uid)
        if _status_rows(rows)["pending"]:
            return jsonify({"error":"Resit sedang disemak. Jangan bayar lagi."}),409
        if _is_member(conf,uid):
            return jsonify({"error":"Rakan Pembangun sudah aktif. Jangan bayar lagi."}),409
        catalog=_source("/internal/payment/v1/catalog")
        validated_plans(catalog)
        percentage,rakan_open=validated_rakan_status(catalog)
        if not rakan_open:
            return jsonify({"error":"Pendaftaran Rakan Pembangun telah penuh"}),409
        image,mime=_source("/internal/payment/v1/qr",expect="image")
    except (ProfileUnavailable,PaymentConflict):
        return jsonify({"error":"QR pembayaran belum tersedia"}),503
    return Response(image,mimetype=mime)


@bp.post("/api/web/payment/receipt")
def payment_submit():
    conf,uid,err=_auth()
    if err is not None:
        return err
    if request.headers.get("Origin") != "https://"+request.host:
        return jsonify({"error":"Asal permintaan tidak sah"}),400
    if (request.content_length is None or request.content_length>MAX_RECEIPT+12000
            or request.mimetype!="multipart/form-data" or
            set(request.form)!={"plan"} or set(request.files)!={"receipt"}):
        return jsonify({"error":"Permintaan resit tidak sah atau terlalu besar"}),400
    code=request.form.get("plan")
    upload=request.files.get("receipt")
    mime=upload.mimetype if upload is not None else None
    raw=upload.stream.read(MAX_RECEIPT+1) if upload is not None else b""
    try:
        ext=_validate_receipt(raw,mime)
        catalog=_source("/internal/payment/v1/catalog")
        plans=validated_plans(catalog)
        if code not in plans:
            raise ValueError("Hanya pakej Rakan Pembangun ditawarkan")
        _,rakan_open=validated_rakan_status(catalog)
        if _status_rows(_existing(conf,uid))["pending"]:
            return jsonify({"error":"Resit lain sedang disemak. Jangan bayar lagi."}),409
        if _is_member(conf,uid):
            return jsonify({"error":"Rakan Pembangun sudah aktif. Jangan bayar sekali lagi."}),409
        if not rakan_open:
            return jsonify({"error":"Pendaftaran Rakan Pembangun telah penuh"}),409
        proof=_telegram_document(conf,uid,raw,ext)
        amount=plans[code]["amount"]
        data={
            "chat_id":str(uid), "amount":amount,"status":"pending",
            "telegram_message_id":proof["message_id"],
            "proof_telegram_file_id":proof["file_id"],
            "proof_file_unique_id":proof["unique_id"],
            "proof_telegram_message_id":proof["message_id"],
            "proof_mime_type":proof["mime"],
            "proof_received_at":datetime.now(timezone.utc).isoformat(),
            "notes":"proof_received_web",
        }
        saved=_payment_rest(conf,"POST",body=data)
        if (len(saved)!=1 or saved[0].get("chat_id")!=str(uid)
                or saved[0].get("status")!="pending"
                or type(saved[0].get("id")) is not int or saved[0]["id"] <= 0):
            raise ProfileUnavailable("Permohonan bayaran belum disahkan")
        rid = saved[0]["id"]
        # NEVER change a successfully saved Pending receipt into HTTP 503
        # just because the subsequent admin Telegram notification failed.
        # Otherwise the user could assume the receipt was lost and pay again.
        notified = False
        try:
            notified = _notify_telegram_admin_review(uid, rid)
        except Exception as exc:
            print("WEB PAYMENT ADMIN NOTIFICATION unavailable:",
                  type(exc).__name__, flush=True)
        message = ("Resit diterima, permohonan Pending dan menunggu pengesahan admin."
                   if notified else
                   "Resit diterima dan direkod sebagai Pending. Makluman admin belum "
                   "dapat disahkan; admin boleh semak melalui Panel Admin → Pending Bayaran. "
                   "Jangan bayar atau hantar resit sekali lagi.")
        return jsonify({"submitted":True,"id":rid,"status":"pending",
                        "admin_notification":"sent" if notified else "unconfirmed",
                        "message":message}),201
    except PaymentConflict:
        return jsonify({"error":"Permohonan Pending sudah wujud. Jangan bayar dua kali."}),409
    except ValueError as exc:
        return jsonify({"error":str(exc)}),400
    except ProfileUnavailable:
        return jsonify({"error":"Resit tidak dapat direkodkan dengan selamat. Semak status pembayaran sebelum cuba lagi; jangan bayar sekali lagi."}),503
