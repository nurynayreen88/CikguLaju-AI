"""CikguLaju KP2027 SK Year 1 Matematik: quota-gated private staged batch.

This route is OFF by default. Only explicitly approved small pilot items can be
served, from service-role-only Supabase rows. Login, entitlement/trial charging,
and integrity are checked per POST. No user-supplied file path or remote URL.
"""
from __future__ import annotations

import base64
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from zipfile import BadZipFile, ZipFile

HOST = "soxakntcanbycjoygrcx.supabase.co"
SOURCE_SHA = "07003ed9b0037359ff30a8956ba328d3d5eb76ad44417bf1be5be18d74fe50cf"
ORIGIN = "https://cikgulaju-web.onrender.com"
FEATURE_FLAG = "CIKGULAJU_KP2027_MATH_CANARY_ENABLED"
FORMATS = {"word": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
           "pdf": ("pdf", "application/pdf")}
# Curriculum-only catalog: exact Lesson/SP and digest mapping from immutable QA V11.
# Binary files never enter the public GitHub repository.
_CATALOG = json.loads(Path(__file__).with_name("kp2027_math_v11_catalog.json").read_text(encoding="utf-8"))
if _CATALOG.get("source_archive_sha256") != SOURCE_SHA:
    raise RuntimeError("KP2027 Mathematics source catalog mismatch")
MAX_LESSON = 125


def expected_entry(group, lesson):
    if group not in ("A", "B") or type(lesson) is not int or not 1 <= lesson <= MAX_LESSON:
        raise ValueError("Invalid KP2027 Math lesson")
    row = _CATALOG[group].get(str(lesson))
    if not isinstance(row, dict):
        raise ValueError("Lesson has no verified curriculum mapping")
    return row



class PilotUnavailable(Exception):
    """Fail closed without disclosing private source material."""


def valid_selection(group, lesson, fmt):
    if fmt not in FORMATS:
        raise ValueError("Pilihan KP2027 Tahun 1 belum tersedia")
    expected_entry(group, lesson)
    return group, lesson, fmt


def _settings(config):
    if not isinstance(config, dict) or config.get("account_backend") != "supabase":
        raise PilotUnavailable("Private document backend not configured")
    url, key = config.get("supabase_url"), config.get("supabase_key")
    parts = urlsplit(url if isinstance(url, str) else "")
    if (parts.scheme != "https" or parts.hostname != HOST or parts.path not in ("", "/")
            or parts.port is not None or parts.username or parts.password or parts.query or parts.fragment
            or not isinstance(key, str) or len(key) < 30):
        raise PilotUnavailable("Private document configuration unavailable")
    return url.rstrip("/"), key


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _headers(key):
    headers = {"apikey": key, "Accept": "application/json"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    return headers


def _document(blob, fmt):
    if not isinstance(blob, bytes) or not 1000 <= len(blob) <= 300000:
        raise PilotUnavailable("Document size unverified")
    if fmt == "pdf":
        if not blob.startswith(b"%PDF-"):
            raise PilotUnavailable("PDF format unverified")
    else:
        try:
            with ZipFile(BytesIO(blob)) as z:
                if z.testzip() is not None or "word/document.xml" not in z.namelist():
                    raise PilotUnavailable("Word format unverified")
        except (OSError, BadZipFile, ValueError) as exc:
            raise PilotUnavailable("Word format unverified") from exc
    return blob


def verify_private_row(row, group, lesson, fmt):
    """Do not trust database contents or client selection without revalidation."""
    valid_selection(group, lesson, fmt)
    if (not isinstance(row, dict) or row.get("subject") != "MATH" or row.get("kumpulan") != group
            or type(row.get("lesson")) is not int or row["lesson"] != lesson
            or row.get("format") != fmt or row.get("approval_status") != "CANARY_APPROVED"
            or row.get("source_archive_sha256") != SOURCE_SHA
            or row.get("sp_code") != expected_entry(group, lesson)["sp"]):
        raise PilotUnavailable("RPH belum diluluskan untuk muat turun")
    try:
        data = base64.b64decode(row["content_base64"], validate=True)
    except (TypeError, ValueError, base64.binascii.Error) as exc:
        raise PilotUnavailable("RPH tidak dapat disahkan") from exc
    if type(row.get("byte_size")) is not int or row["byte_size"] != len(data):
        raise PilotUnavailable("RPH saiz tidak sepadan")
    digest = row.get("sha256_hex")
    if (not isinstance(digest, str) or len(digest) != 64 or not re.fullmatch("[0-9a-f]{64}", digest)
            or digest != expected_entry(group, lesson)[fmt] or sha256(data).hexdigest() != digest):
        raise PilotUnavailable("RPH integriti gagal")
    return _document(data, fmt)


def fetch_private_document(config, group, lesson, fmt, *, opener=None):
    group, lesson, fmt = valid_selection(group, lesson, fmt)
    base, key = _settings(config)
    args = urlencode({"select": "subject,kumpulan,lesson,format,content_base64,byte_size,sha256_hex,sp_code,approval_status,source_archive_sha256",
                      "subject": "eq.MATH", "kumpulan": "eq." + group, "lesson": "eq." + str(lesson),
                      "format": "eq." + fmt, "limit": "2"})
    request = Request(base + "/rest/v1/kp2027_private_pilot_assets?" + args, headers=_headers(key), method="GET")
    open_request = opener or build_opener(_NoRedirects()).open
    try:
        with open_request(request, timeout=12) as response:
            if getattr(response, "status", None) != 200:
                raise PilotUnavailable("Private RPH source unavailable")
            raw = response.read(450001)
        if len(raw) > 450000:
            raise PilotUnavailable("Private RPH source too large")
        rows = json.loads(raw)
    except (HTTPError, URLError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise PilotUnavailable("Private RPH source unavailable") from exc
    if not isinstance(rows, list) or len(rows) != 1:
        raise PilotUnavailable("Approved RPH not found")
    return verify_private_row(rows[0], group, lesson, fmt)


def fetch_approved_catalog(config, *, opener=None):
    """Read verified *metadata* only; never send RPH bytes to availability clients.

    Release is data-driven: approve a complete verified Word/PDF pair in the
    private table and it becomes selectable without a new Web deployment.
    """
    base, key = _settings(config)
    params = urlencode({
        "select": "kumpulan,lesson,format,sha256_hex,sp_code,source_archive_sha256,approval_status",
        "subject": "eq.MATH", "approval_status": "eq.CANARY_APPROVED", "limit": "600",
    })
    req = Request(base + "/rest/v1/kp2027_private_pilot_assets?" + params,
                  headers=_headers(key), method="GET")
    open_request = opener or build_opener(_NoRedirects()).open
    try:
        with open_request(req, timeout=12) as response:
            if getattr(response, "status", None) != 200:
                raise PilotUnavailable("Curriculum inventory unavailable")
            raw = response.read(200001)
        if len(raw) > 200000:
            raise PilotUnavailable("Inventory too large")
        records = json.loads(raw)
    except (HTTPError, URLError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise PilotUnavailable("Curriculum inventory unavailable") from exc
    if not isinstance(records, list) or len(records) > 600:
        raise PilotUnavailable("Invalid curriculum inventory")
    seen = {}
    for item in records:
        if not isinstance(item, dict):
            raise PilotUnavailable("Invalid curriculum inventory")
        group, lesson, fmt = item.get("kumpulan"), item.get("lesson"), item.get("format")
        try:
            valid_selection(group, lesson, fmt)
        except ValueError:
            raise PilotUnavailable("Invalid lesson in curriculum inventory") from None
        expected = expected_entry(group, lesson)
        if (item.get("sp_code") != expected["sp"] or item.get("sha256_hex") != expected[fmt]
                or item.get("source_archive_sha256") != SOURCE_SHA
                or item.get("approval_status") != "CANARY_APPROVED"):
            raise PilotUnavailable("Unverified material in curriculum inventory")
        key_ = (group, lesson)
        formats = seen.setdefault(key_, set())
        if fmt in formats:
            raise PilotUnavailable("Duplicate curriculum asset")
        formats.add(fmt)
    result = {"A": [], "B": []}
    for (group, lesson), formats in seen.items():
        if formats == set(FORMATS):
            result[group].append(lesson)
    for group in result:
        result[group].sort()
    return result


def debit_shared_trial(url, key, uid, reference):
    """Respect existing atomic CikguLaju RPC, including modern sb_secret_ keys.

    The shared helper always attaches a legacy JWT Bearer. Keep it unchanged for
    existing RPH routes; adapt only this pilot's new opaque-server-key path.
    """
    from web.shared_trial_rpc import consume_successful_generation
    if not isinstance(key, str) or not key.startswith("sb_secret_"):
        return consume_successful_generation(url, key, uid, reference)
    from uuid import UUID
    try:
        check = UUID(reference.removeprefix("web-rph:"))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Invalid server-issued trial reference") from exc
    if not reference.startswith("web-rph:") or check.version != 4 or str(check) != reference[8:]:
        raise ValueError("Invalid server-issued trial reference")
    from urllib.request import urlopen
    body = json.dumps({"p_telegram_user_id": uid, "p_reference_id": reference,
                       "p_reason": "web_rph_generation"}, separators=(",", ":")).encode()
    req = Request(url.rstrip("/") + "/rest/v1/rpc/cikgulaju_use_trial", data=body, method="POST",
                  headers={"apikey": key, "Accept": "application/json", "Content-Type": "application/json"})
    with urlopen(req, timeout=8) as response:
        value = json.load(response)
    if not isinstance(value, list) or len(value) != 1 or type(value[0].get("ok")) is not bool or type(value[0].get("remaining")) is not int:
        raise RuntimeError("Unconfirmed trial RPC response")
    return {"ok": value[0]["ok"], "remaining": value[0]["remaining"]}


_PAGE = '''<!doctype html><html lang="ms"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KP2027 Matematik Tahun 1 | CikguLaju</title>
<style>body{margin:0;font:16px system-ui,sans-serif;background:#f5f7fa;color:#1a2735}.wrap{max-width:560px;margin:36px auto;background:white;border-radius:12px;padding:28px;box-shadow:0 6px 22px #19324916}h1{font-size:24px;margin:0 0 10px}p{line-height:1.55}label{display:block;margin:17px 0 7px;font-weight:600}select,button{width:100%;padding:13px;border-radius:7px;font:inherit}select{border:1px solid #bac6d2;background:#fff}button{margin-top:24px;border:0;background:#193755;color:white;font-weight:700;cursor:pointer}button:disabled{opacity:.55}small{color:#586779}.status{min-height:26px;margin-top:18px}a{color:#1c528e}</style></head>
<body><main class="wrap"><h1>Matematik â¢ KP2027 Tahun 1</h1><p>RPH Lesson awal, format Word dan PDF. Sila log masuk menggunakan akaun CikguLaju. Setiap muat turun pengguna percubaan menggunakan kuota janaan sedia ada.</p>
<label for="group">Kumpulan sekolah</label><select id="group"><option value="A">Kumpulan A</option><option value="B">Kumpulan B</option></select>
<label for="lesson">Lesson</label><select id="lesson" disabled><option value="">Semak senarai Lesson...</option></select>
<label for="fmt">Format bahan</label><select id="fmt"><option value="pdf">PDF</option><option value="word">Word (.docx)</option></select>
<button id="download" type="button">Download RPH</button><p class="status" id="message" role="status" aria-live="polite"></p>
<small>Hanya Lesson yang telah lulus akan dibenarkan. <a href="/">Kembali ke CikguLaju / Log masuk</a>.</small></main>
<script>
const g=document.getElementById('group'),l=document.getElementById('lesson'),f=document.getElementById('fmt'),b=document.getElementById('download'),m=document.getElementById('message');
let choices={A:[],B:[]};b.disabled=true;
function refresh(){l.replaceChildren();const list=choices[g.value]||[];for(const n of list){const o=document.createElement('option');o.value=String(n);o.textContent='Lesson '+String(n).padStart(3,'0');l.appendChild(o)}l.disabled=list.length===0;b.disabled=list.length===0;if(!list.length)m.textContent='Tiada Lesson yang diluluskan untuk kumpulan ini.';else m.textContent=list.length+' Lesson tersedia untuk Kumpulan '+g.value+'.'}
g.addEventListener('change',refresh);
(async()=>{try{const r=await fetch('/api/kp2027/sk/tahun-1/matematik/available',{credentials:'same-origin',headers:{Accept:'application/json'}});const j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.error||'Senarai Lesson belum tersedia ('+r.status+')');if(!j.groups||!Array.isArray(j.groups.A)||!Array.isArray(j.groups.B))throw Error('Senarai Lesson tidak sah');choices=j.groups;refresh()}catch(e){m.textContent=e.message}})();
b.addEventListener('click',async()=>{if(l.disabled||!l.value)return;b.disabled=true;m.textContent='Menyediakan fail...';const group=g.value,lesson=Number(l.value),format=f.value;try{const r=await fetch('/api/kp2027/sk/tahun-1/matematik/download',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','Accept':'application/octet-stream'},body:JSON.stringify({group,lesson,format})});if(!r.ok){const j=await r.json().catch(()=>({}));throw Error(j.error||'Muat turun belum tersedia ('+r.status+')')}const blob=await r.blob();const ext=format==='pdf'?'pdf':'docx',name='CIKGULAJU_KP2027_MATH_T1_'+group+'_LESSON'+String(lesson).padStart(3,'0')+'.'+ext;const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),30000);m.textContent='Fail disediakan. Semak folder Downloads.';}catch(e){m.textContent=e.message}finally{b.disabled=l.disabled}})
</script></body></html>'''


def create_blueprint():
    from flask import Blueprint, current_app, jsonify, make_response, request, send_file
    from web.rph_delivery_quota import authorize_rendered_document, has_active_paid_access
    from web_v1_telegram_auth_routes import COOKIE, _config, _lookup
    from web_v1_sessions import verify_session_ticket

    bp = Blueprint("kp2027_math_pilot", __name__)

    @bp.after_request
    def secure_headers(response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Vary"] = "Cookie"
        return response

    def denied(message, status, code):
        return jsonify({"error": message, "code": code}), status

    def account_for_request():
        config = _config()
        if not config or config.get("account_backend") != "supabase":
            return None, None, denied("Akses akaun Web belum tersedia.", 503, "LOGIN_BACKEND_UNAVAILABLE")
        uid = verify_session_ticket(request.cookies.get(COOKIE), config["CIKGULAJU_WEB_SESSION_SECRET"])
        if type(uid) is not int or uid <= 0:
            return None, None, denied("Sila log masuk terlebih dahulu.", 401, "AUTH_REQUIRED")
        try:
            account = _lookup(config, uid)
        except Exception:
            return None, None, denied("Semakan akaun belum tersedia.", 503, "ACCOUNT_LOOKUP_FAILED")
        if (not isinstance(account, dict) or account.get("authenticated") is not True
                or account.get("telegram_user_id") != uid):
            return None, None, denied("Akaun belum disahkan.", 403, "ACCOUNT_NOT_VERIFIED")
        return config, account, None

    @bp.get("/kp2027/tahun-1/matematik")
    def page():
        response = make_response(_PAGE)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.headers["Content-Security-Policy"] = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                                                        "connect-src 'self'; img-src 'self' blob:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        return response

    @bp.get("/api/kp2027/sk/tahun-1/matematik/available")
    def available():
        if os.environ.get(FEATURE_FLAG) != "1":
            return denied("Bahan KP2027 belum diaktifkan.", 503, "KP2027_PILOT_DISABLED")
        config, account, error = account_for_request()
        if error is not None:
            return error
        try:
            groups = fetch_approved_catalog(config)
        except PilotUnavailable:
            return denied("Senarai RPH belum tersedia. Sila cuba lagi.", 503, "INVENTORY_UNAVAILABLE")
        return jsonify({"groups": groups, "source": "verified-private-kp2027-v11"})

    @bp.post("/api/kp2027/sk/tahun-1/matematik/download")
    def download():
        if os.environ.get(FEATURE_FLAG) != "1":
            return denied("Penerbitan Matematik KP2027 belum diaktifkan.", 503, "KP2027_PILOT_DISABLED")
        if request.headers.get("Origin") != ORIGIN:
            return denied("Permintaan mestilah daripada Web CikguLaju.", 403, "ORIGIN_REQUIRED")
        if not request.is_json or not 0 < (request.content_length or 0) <= 1024:
            return denied("Pilihan Lesson tidak sah.", 400, "INVALID_REQUEST")
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or set(payload) != {"group", "lesson", "format"}:
            return denied("Pilihan Lesson tidak lengkap.", 400, "INVALID_SELECTION")
        try:
            group, lesson, fmt = valid_selection(payload["group"], payload["lesson"], payload["format"])
        except ValueError:
            return denied("Lesson yang dipilih belum tersedia.", 404, "LESSON_NOT_AVAILABLE")
        config, account, error = account_for_request()
        if error is not None:
            return error
        paid = has_active_paid_access(account)
        if not paid and (type(account.get("free_remaining")) is not int or not 0 <= account["free_remaining"] <= 10):
            return denied("Baki janaan percuma tidak dapat disahkan.", 503, "TRIAL_UNVERIFIED")
        if not paid and account["free_remaining"] == 0:
            return denied("10 janaan percuma telah habis. Aktifkan langganan untuk meneruskan.", 403, "FREE_TRIAL_EXHAUSTED")
        try:
            document = fetch_private_document(config, group, lesson, fmt)
        except PilotUnavailable:
            return denied("RPH ini masih dalam semakan atau tidak tersedia.", 503, "PILOT_ASSET_UNAVAILABLE")
        remaining = None
        if not paid:
            try:
                result = authorize_rendered_document(
                    account, account["telegram_user_id"], document,
                    config["supabase_url"], config["supabase_key"], debit=debit_shared_trial)
            except Exception:
                return denied("Semakan kuota tidak dapat dipastikan. Semak baki akaun sebelum cuba semula.", 503, "TRIAL_CHARGE_UNCONFIRMED")
            if not result["allowed"]:
                return denied("Baki janaan RPH percuma telah habis.", 403, "FREE_TRIAL_EXHAUSTED")
            remaining = result["remaining"]
        ext, mime = FORMATS[fmt]
        response = send_file(BytesIO(document), mimetype=mime, as_attachment=True,
                             download_name=f"CIKGULAJU_KP2027_MATH_T1_{group}_LESSON{lesson:03d}.{ext}",
                             conditional=False)
        if remaining is not None:
            response.headers["X-RPH-Trial-Remaining"] = str(remaining)
        return response

    return bp
