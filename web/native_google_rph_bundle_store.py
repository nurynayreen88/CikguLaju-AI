"""Private native Word/PDF bundle store for Google-only UUID CikguLaju Web.

Uses the SAME production Supabase project as the legacy Telegram accounts.
Only callable after a signed Google UUID session and exact source validation.
Storage is always private; database finalization makes quota debit atomic.
No fake Telegram IDs, no staging credits, no cross-Render paid bridge.
"""
from hashlib import sha256
from io import BytesIO
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from web.native_google_principal_store import (
    PROD_SUPABASE, _headers, _uuid, CanonicalAccountUnavailable)
from web.google_rph_bundle_quota import rendered_bundle_sha256

BUCKET = "cikgulaju-native-web-rph"
MIMES = {
    "word": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    "pdf": ("application/pdf", ".pdf"),
}
MAX_BYTES = 15 * 1024 * 1024


class NativeBundleUnavailable(RuntimeError):
    pass


def _job(value):
    try:
        canonical = str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Invalid native job UUID") from None
    if canonical != value:
        raise ValueError("Noncanonical native job UUID")
    return canonical


def _rpc(cfg, name, payload):
    if name not in ("prepare_native_google_web_rph", "complete_native_google_web_rph"):
        raise ValueError("RPC not approved for native RPH")
    headers = _headers(cfg)
    req = Request(PROD_SUPABASE + "/rest/v1/rpc/" + name,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        method="POST", headers={**headers,"Content-Type":"application/json"})
    try:
        with urlopen(req, timeout=15) as res:
            data = res.read(4097)
            if res.status != 200 or len(data) > 4096:
                raise NativeBundleUnavailable("Native RPH job response invalid")
        out = json.loads(data)
        if not isinstance(out, dict):
            raise NativeBundleUnavailable("Native RPH RPC reply invalid")
        return out
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, TypeError):
        raise NativeBundleUnavailable("Native RPH outcome uncertain; inspect existing job") from None


def prepare(cfg, principal_id, job_id, selection_sha256):
    principal_id = _uuid(principal_id)
    job_id = _job(job_id)
    if (not isinstance(selection_sha256, str) or len(selection_sha256)!=64
            or any(c not in "0123456789abcdef" for c in selection_sha256)):
        raise ValueError("Invalid source selection hash")
    result = _rpc(cfg,"prepare_native_google_web_rph",{
        "p_principal_id":principal_id,"p_job_id":job_id,
        "p_selection_sha256":selection_sha256})
    if result.get("job_id")!=job_id or result.get("status") not in ("prepared","ready"):
        raise NativeBundleUnavailable("Job identity not confirmed")
    return result


def _private_object(cfg, principal_id, job_id, fmt):
    mime, ext = MIMES[fmt]
    name = principal_id + "/" + job_id + ext
    # Storage authenticated route, not a public URL or reusable signed URL.
    endpoint = (PROD_SUPABASE+"/storage/v1/object/authenticated/"+
                BUCKET+"/"+quote(name, safe="/"))
    try:
        with urlopen(Request(endpoint, headers=_headers(cfg),method="GET"),timeout=30) as res:
            raw = res.read(MAX_BYTES+1)
            if res.status!=200 or len(raw)>MAX_BYTES:
                raise NativeBundleUnavailable("Protected RPH file unavailable")
        return raw,mime
    except (HTTPError,URLError,OSError,TimeoutError):
        raise NativeBundleUnavailable("Private Word/PDF unavailable") from None


def _upload_once(cfg, principal_id, job_id, fmt, raw):
    mime, ext = MIMES[fmt]
    if not isinstance(raw, bytes) or not 100 <= len(raw) <= MAX_BYTES:
        raise NativeBundleUnavailable("Invalid RPH file bytes")
    name = principal_id+"/"+job_id+ext
    endpoint = PROD_SUPABASE+"/storage/v1/object/"+BUCKET+"/"+quote(name,safe="/")
    req = Request(endpoint,data=raw,method="POST",
                  headers={**_headers(cfg),"Content-Type":mime,"x-upsert":"false"})
    try:
        with urlopen(req,timeout=40) as res:
            if res.status not in (200,201) or len(res.read(4097))>4096:
                raise NativeBundleUnavailable("Private RPH upload uncertain")
    except HTTPError as exc:
        if exc.code!=409:
            raise NativeBundleUnavailable("Private RPH upload uncertain") from None
        # A previously uploaded file is reusable only if the bytes match.
        original,_ = _private_object(cfg,principal_id,job_id,fmt)
        if sha256(original).digest()!=sha256(raw).digest():
            raise NativeBundleUnavailable("Existing private RPH file collision")
    except (URLError,OSError,TimeoutError):
        raise NativeBundleUnavailable("Private RPH upload uncertain") from None


def publish(cfg, principal_id, job_id, selection_sha256, word, pdf):
    principal_id = _uuid(principal_id)
    job_id = _job(job_id)
    doc_hash = rendered_bundle_sha256(word,pdf)
    initial = prepare(cfg,principal_id,job_id,selection_sha256)
    if initial["status"]=="ready":
        return {"status":"ready","job_id":job_id,"already_ready":True}
    _upload_once(cfg,principal_id,job_id,"word",word)
    _upload_once(cfg,principal_id,job_id,"pdf",pdf)
    result = _rpc(cfg,"complete_native_google_web_rph",{
        "p_principal_id":principal_id,"p_job_id":job_id,
        "p_manifest_sha256":doc_hash})
    if (result.get("job_id")!=job_id
            or result.get("status") not in ("ready","prepared")
            or type(result.get("allowed")) is not bool
            or type(result.get("remaining")) is not int
            or not 0 <= result["remaining"] <= 10
            or (result["allowed"] and result["status"]!="ready")
            or (not result["allowed"] and result["status"]!="prepared")):
        raise NativeBundleUnavailable("Native RPH completion unconfirmed")
    return result


def owned_job(cfg, principal_id, job_id):
    principal_id = _uuid(principal_id)
    job_id = _job(job_id)
    url = PROD_SUPABASE+"/rest/v1/cikgulaju_web_rph_jobs?"+urlencode({
        "select":"id,principal_id,status,selection_sha256,remaining_after",
        "id":"eq."+job_id, "principal_id":"eq."+principal_id, "limit":"2"})
    try:
        with urlopen(Request(url,headers=_headers(cfg),method="GET"),timeout=10) as res:
            raw=res.read(4097)
            if res.status!=200 or len(raw)>4096:
                raise NativeBundleUnavailable("Native job lookup invalid")
        rows=json.loads(raw)
    except (HTTPError,URLError,OSError,TimeoutError,ValueError,TypeError):
        raise NativeBundleUnavailable("Native job lookup unavailable") from None
    if not isinstance(rows,list) or len(rows)>1:
        raise NativeBundleUnavailable("Ambiguous native job")
    if not rows:
        return None
    row=rows[0]
    if (not isinstance(row,dict) or row.get("id")!=job_id
            or row.get("principal_id")!=principal_id
            or row.get("status") not in ("ready","prepared")):
        raise NativeBundleUnavailable("Inconsistent private RPH owner")
    return row


def ready_download(cfg, principal_id, job_id, fmt):
    if fmt not in MIMES:
        raise ValueError("Unknown private file type")
    row=owned_job(cfg,principal_id,job_id)
    if row is None or row["status"]!="ready":
        return None
    return _private_object(cfg,principal_id,job_id,fmt)
