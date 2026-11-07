"""Private Supabase staging receipt storage and UUID-bound payment queue.

All calls use the dedicated staging project and server-only service key.
No access to legacy Telegram payment rows; no direct browser Supabase secrets.
"""
import hashlib
from datetime import datetime, timezone
import json
import re
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from web.provider_neutral_payment import validate_payment_plan

BUCKET = "web-receipts-staging"
MAX_RECEIPT = 4 * 1024 * 1024
MIMES = {"application/pdf": ".pdf", "image/jpeg": ".jpg",
         "image/png": ".png", "image/webp": ".webp"}


class PaymentUnavailable(RuntimeError):
    pass


class PaymentConflict(PaymentUnavailable):
    pass


def validate_receipt(data, mime):
    if not isinstance(data, bytes) or not 700 <= len(data) <= MAX_RECEIPT:
        raise ValueError("Resit tidak sah atau melebihi 4 MB")
    if mime not in MIMES:
        raise ValueError("Jenis resit tidak disokong")
    ok = ((mime == "application/pdf" and data.startswith(b"%PDF-"))
          or (mime == "image/jpeg" and data.startswith(b"\xff\xd8\xff"))
          or (mime == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n"))
          or (mime == "image/webp" and data.startswith(b"RIFF")
              and data[8:12] == b"WEBP"))
    if not ok:
        raise ValueError("Kandungan resit tidak sepadan")
    return MIMES[mime], hashlib.sha256(data).hexdigest()


def _request(config, path, *, method="GET", data=None, content_type="application/json",
             limit=32768, prefer=None):
    key = config.get("staging_service_key", "")
    base = config.get("supabase_url", "")
    if not isinstance(key, str) or len(key) < 24 or not base.startswith("https://"):
        raise PaymentUnavailable("Sambungan pembayaran staging tidak tersedia")
    headers = {"apikey": key, "Authorization": "Bearer " + key,
               "Accept": "application/json", "Content-Type": content_type}
    if prefer:
        headers["Prefer"] = prefer
    req = Request(base.rstrip("/") + path, data=data,
                  headers=headers, method=method)
    try:
        with urlopen(req, timeout=14) as resp:
            blob = resp.read(limit + 1)
            if len(blob) > limit or resp.status not in (200, 201):
                raise PaymentUnavailable("Respons pembayaran tidak sah")
            return json.loads(blob) if blob else None
    except HTTPError as exc:
        if exc.code in (409, 412):
            raise PaymentConflict("Permohonan atau resit telah digunakan") from None
        raise PaymentUnavailable("Simpanan bayaran tidak tersedia") from None
    except (URLError, OSError, ValueError, TypeError):
        raise PaymentUnavailable("Sambungan bayaran belum tersedia") from None


def _rpc(config, name, payload):
    if name not in ("submit_web_payment_request", "review_web_payment_request"):
        raise ValueError("RPC not allowlisted")
    return _request(config, "/rest/v1/rpc/" + name, method="POST",
                    data=json.dumps(payload, separators=(",", ":")).encode())


def _uuid(value):
    try:
        canonical = str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Invalid account ID") from None
    if canonical != value:
        raise ValueError("Invalid account ID")
    return canonical


def _rows(config, table, parameters):
    if table not in ("web_payment_requests", "web_entitlements"):
        raise ValueError("Invalid table")
    reply = _request(config, "/rest/v1/" + table + "?" + urlencode(parameters))
    if not isinstance(reply, list):
        raise PaymentUnavailable("Rekod pembayaran tidak sah")
    return reply


def my_payments(config, account_id):
    account_id = _uuid(account_id)
    rows = _rows(config, "web_payment_requests", {
        "select": "id,plan_code,quoted_amount_sen,status,submitted_at,reviewed_at,review_note",
        "account_id": "eq." + account_id, "order": "submitted_at.desc", "limit": "30"})
    return rows


def web_payment_access(config, account_id):
    """Read approved staging entitlements, never claim RPH generator access."""
    account_id = _uuid(account_id)
    rows = _rows(config, "web_entitlements", {
        "select": "plan_code,valid_from,valid_until",
        "account_id": "eq." + account_id, "order": "valid_from.desc", "limit": "100"})
    now = datetime.now(timezone.utc)
    active = []
    for entry in rows:
        if not isinstance(entry, dict):
            raise PaymentUnavailable("Invalid entitlement record")
        expiry = entry.get("valid_until")
        if expiry is None:
            if entry.get("plan_code") == "rakan_pembangun":
                active.append({"plan_code": "rakan_pembangun", "valid_until": None})
            continue
        try:
            expires_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
        except (TypeError, ValueError, AttributeError):
            raise PaymentUnavailable("Invalid entitlement expiry") from None
        if expires_at.tzinfo is None:
            raise PaymentUnavailable("Untrusted entitlement timezone")
        if expires_at > now:
            active.append({"plan_code": entry.get("plan_code"), "valid_until": expiry})
    return {"payment_access_active": bool(active), "active_plans": active,
            "rph_google_integration_ready": False}


def eligible_plans(config, catalog):
    # Must always be supplied by an explicitly approved server configuration.
    if not isinstance(catalog, dict):
        raise PaymentUnavailable("Katalog bayaran belum disahkan")
    return [{"code": code, "amount_sen": validate_payment_plan(code, catalog)[1]}
            for code in ("rakan_pembangun", "monthly", "annual")
            if isinstance(catalog.get(code), dict) and catalog[code].get("enabled") is True]


def submit_receipt(config, account_id, plan_code, approved_catalog, raw, mime):
    account_id = _uuid(account_id)
    plan, amount = validate_payment_plan(plan_code, approved_catalog)
    ext, sha = validate_receipt(raw, mime)
    # Reject duplicate pending payment before transferring the receipt. Race
    # conditions are still guarded by DB unique constraints.
    pending = _rows(config, "web_payment_requests", {
        "select": "id", "account_id": "eq." + account_id,
        "status": "eq.pending", "limit": "1"})
    if pending:
        raise PaymentConflict("Bayaran sebelumnya masih menunggu pengesahan")

    filename = str(uuid.uuid4()) + ext
    receipt_path = account_id + "/" + filename
    _request(config, "/storage/v1/object/" + BUCKET + "/" + receipt_path,
             method="POST", data=raw, content_type=mime)
    # IMPORTANT: Storage upload may succeed while RPC fails (or times out).
    # Never claim failure means receipt or payment was rolled back.
    try:
        result = _rpc(config, "submit_web_payment_request", {
            "p_account_id": account_id, "p_plan_code": plan,
            "p_amount_sen": amount, "p_receipt_path": receipt_path,
            "p_receipt_sha256": sha})
        return _uuid(result)
    except PaymentUnavailable:
        raise PaymentUnavailable(
            "Pengesahan rekod belum pasti. Semak status sebelum muat naik lagi.") from None


def account_display_name(config, account_id):
    account_id = _uuid(account_id)
    reply = _request(config, "/rest/v1/web_accounts?" + urlencode({
        "select": "display_name", "id": "eq." + account_id, "limit": "1"}))
    if not isinstance(reply, list) or len(reply) != 1:
        raise PaymentUnavailable("Akaun guru tidak tersedia")
    value = reply[0].get("display_name")
    return " ".join(value.split())[:120] if isinstance(value, str) else ""


def admin_pending(config):
    rows = _rows(config, "web_payment_requests", {
        "select": "id,account_id,plan_code,quoted_amount_sen,status,submitted_at,web_accounts(display_name)",
        "status": "eq.pending", "order": "submitted_at.asc", "limit": "100"})
    return rows


def admin_payment(config, request_id):
    request_id = _uuid(request_id)
    rows = _rows(config, "web_payment_requests", {
        "select": "id,account_id,plan_code,quoted_amount_sen,status,submitted_at,reviewed_at,reviewed_by,review_note,receipt_storage_path,web_accounts(display_name)",
        "id": "eq." + request_id, "limit": "2"})
    if len(rows) != 1 or rows[0].get("id") != request_id:
        return None
    return rows[0]


def private_receipt(config, request_id):
    row = admin_payment(config, request_id)
    if row is None:
        return None
    path = row.get("receipt_storage_path")
    account = row.get("account_id")
    if (not isinstance(path, str) or not isinstance(account, str)
            or not path.startswith(account + "/")
            or not re.fullmatch(r"[a-f0-9-]{36}/[a-f0-9-]{36}\.(?:pdf|png|jpg|webp)", path)):
        raise PaymentUnavailable("Rujukan resit tidak sah")
    # No signed/public URL. Proxy only to an authorized administrator.
    endpoint = "/storage/v1/object/authenticated/" + BUCKET + "/" + quote(path, safe="/")
    key = config["staging_service_key"]
    req = Request(config["supabase_url"].rstrip("/") + endpoint, headers={
        "apikey": key, "Authorization": "Bearer " + key}, method="GET")
    try:
        with urlopen(req, timeout=14) as res:
            mime = res.headers.get("Content-Type", "").split(";")[0]
            raw = res.read(MAX_RECEIPT + 1)
            if (res.status != 200 or len(raw) > MAX_RECEIPT
                    or mime not in MIMES):
                raise PaymentUnavailable("Resit tidak dapat disahkan")
            validate_receipt(raw, mime)
            return raw, mime
    except (HTTPError, URLError, OSError, ValueError, TypeError):
        raise PaymentUnavailable("Resit belum dapat dipaparkan") from None


def review_payment(config, request_id, action, admin_id, note=""):
    request_id = _uuid(request_id)
    if action not in ("approve", "reject"):
        raise ValueError("Invalid review action")
    if type(admin_id) is not int or admin_id <= 0:
        raise PermissionError("Verified admin required")
    if not isinstance(note, str) or len(note) > 500:
        raise ValueError("Nota terlalu panjang")
    result = _rpc(config, "review_web_payment_request", {
        "p_request_id": request_id, "p_action": action,
        "p_admin_actor": "telegram:" + str(admin_id), "p_note": note})
    if (not isinstance(result, dict) or result.get("id") != request_id
            or result.get("status") not in ("approved", "rejected")
            or type(result.get("already_reviewed")) is not bool):
        raise PaymentUnavailable("Pengesahan bayaran tidak dapat dipastikan")
    return result
