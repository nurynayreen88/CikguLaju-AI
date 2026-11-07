"""Private Google staging RPH job orchestration; NOT an HTTP endpoint.

The parent handler must authenticate the Google UUID identity and generate a
job UUID on the SERVER. No user-provided IDs, email or Telegram ID can grant
quota. Private Word/PDF must be fully available before the *atomic* finalizer
charges exactly one credit; retry fetches identical private files.
"""
from hashlib import sha256
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from web.provider_neutral_web_identity import VerifiedWebIdentity
from web.google_staging_service_auth import staging_service_headers
from web.google_rph_bundle_quota import rendered_bundle_sha256
from web.google_rph_bundle_delivery import _private_file, BUCKET, MIMES

MAX_API_REPLY = 4096


class BundleCommitUnconfirmed(RuntimeError):
    """Read the persisted job status before returning or retrying this charge."""


def _actor_id(actor):
    if (not isinstance(actor, VerifiedWebIdentity)
            or actor.provider != "google"
            or actor.account_id is None
            or actor.subject != actor.account_id):
        raise ValueError("Verified Google account required")
    try:
        account_id = str(uuid.UUID(actor.account_id))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Verified UUID account required") from None
    if account_id != actor.account_id:
        raise ValueError("Noncanonical Google UUID")
    return account_id


def _job_id(job_id):
    if not isinstance(job_id, str):
        raise ValueError("Server-generated UUID required")
    try:
        canonical = str(uuid.UUID(job_id))
    except (ValueError, AttributeError):
        raise ValueError("Canonical server UUID required") from None
    if canonical != job_id:
        raise ValueError("Canonical server UUID required")
    return canonical


def selection_fingerprint(selection, teacher):
    """Hash the validated exact selection; don't store teacher PII in ledger."""
    if not isinstance(selection, dict) or not isinstance(teacher, dict):
        raise ValueError("Server-validated selection required")
    canonical = json.dumps(
        {"selection": selection, "teacher": teacher},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    if not 10 <= len(canonical) <= 6000:
        raise ValueError("Oversized/invalid teacher selection")
    return sha256(b"cikgulaju-rph-job-selection-v1\0" + canonical).hexdigest()


def _rpc(config, function, payload, *, transport=None):
    key = config["staging_service_key"]
    base = config["supabase_url"].rstrip("/")
    if not base.startswith("https://") or ".supabase.co" not in base:
        raise ValueError("Staging Supabase backend required")
    req = Request(base + "/rest/v1/rpc/" + function,
                  data=json.dumps(payload).encode("utf-8"), method="POST",
                  headers={**staging_service_headers(key),
                           "Content-Type": "application/json"})
    opener = transport or urlopen
    try:
        with opener(req, timeout=10) as res:
            body = res.read(MAX_API_REPLY + 1)
            if res.status != 200 or len(body) > MAX_API_REPLY:
                raise BundleCommitUnconfirmed("Staging RPC response invalid")
        result = json.loads(body)
        if not isinstance(result, dict):
            raise BundleCommitUnconfirmed("Staging RPC result invalid")
        return result
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, TypeError):
        raise BundleCommitUnconfirmed(
            "Backend outcome uncertain: reconcile original private job ID") from None


def prepare_private_bundle(config, actor, job_id, selection_hash,
                           *, transport=None):
    account_id = _actor_id(actor)
    jid = _job_id(job_id)
    if (not isinstance(selection_hash, str)
            or len(selection_hash) != 64
            or any(c not in "0123456789abcdef" for c in selection_hash)):
        raise ValueError("Canonical selection fingerprint required")
    result = _rpc(config, "prepare_web_rph_bundle_staging", {
        "p_account_id": account_id,
        "p_job_id": jid,
        "p_selection_sha256": selection_hash,
    }, transport=transport)
    if result.get("job_id") != jid or result.get("status") not in ("prepared", "ready"):
        raise BundleCommitUnconfirmed("Job identity not confirmed")
    return result


def _upload_once(config, account_id, job_id, fmt, contents, *, transport=None,
                 existing_reader=None):
    mime, ext = MIMES[fmt]
    key = config["staging_service_key"]
    name = account_id + "/" + job_id + ext
    base = config["supabase_url"].rstrip("/")
    req = Request(
        base + "/storage/v1/object/" + BUCKET + "/" + quote(name, safe="/"),
        data=contents,
        headers={**staging_service_headers(key),
                 "Content-Type": mime, "x-upsert": "false"},
        method="POST")
    opener = transport or urlopen
    try:
        with opener(req, timeout=35) as res:
            if res.status not in (200, 201):
                raise BundleCommitUnconfirmed("Private file upload not confirmed")
            if len(res.read(4097)) > 4096:
                raise BundleCommitUnconfirmed("Oversized storage response")
    except HTTPError as exc:
        if exc.code != 409:
            raise BundleCommitUnconfirmed("Private upload outcome uncertain") from None
        # Conflict means there is a previous file. It may be from an
        # interrupted identical attempt. Trust it ONLY if bytes match.
        reader = existing_reader or _private_file
        try:
            original = reader(config, account_id, job_id, fmt)
        except Exception:
            raise BundleCommitUnconfirmed("Existing file cannot be verified") from None
        if sha256(original).digest() != sha256(contents).digest():
            raise BundleCommitUnconfirmed("Private file collision with different bytes")
    except (URLError, OSError, TimeoutError):
        raise BundleCommitUnconfirmed("Private upload outcome uncertain") from None


def publish_rendered_bundle(config, actor, job_id, selection_hash,
                            word_bytes, pdf_bytes, *, rpc_transport=None,
                            upload_transport=None, existing_reader=None):
    """Internal synchronous staging orchestration. No browser download routes.

    If a crash occurs after charge, the database marks ready transactionally
    and the private files remain downloadable by the verified owner.
    """
    account_id = _actor_id(actor)
    jid = _job_id(job_id)
    manifest = rendered_bundle_sha256(word_bytes, pdf_bytes)
    job = prepare_private_bundle(config, actor, jid, selection_hash,
                                 transport=rpc_transport)
    if job["status"] == "ready":
        # Completed request should be READ from private persisted job. Do not
        # charge or overwrite. The caller may use download route instead.
        return {"job_id": jid, "status": "ready", "already_ready": True}
    _upload_once(config, account_id, jid, "word", word_bytes,
                 transport=upload_transport, existing_reader=existing_reader)
    _upload_once(config, account_id, jid, "pdf", pdf_bytes,
                 transport=upload_transport, existing_reader=existing_reader)
    result = _rpc(config, "complete_web_rph_bundle_staging", {
        "p_account_id": account_id, "p_job_id": jid,
        "p_manifest_sha256": manifest,
    }, transport=rpc_transport)
    if (result.get("job_id") != jid
            or result.get("status") not in ("prepared", "ready")
            or type(result.get("allowed")) is not bool
            or type(result.get("remaining")) is not int
            or not 0 <= result["remaining"] <= 10):
        raise BundleCommitUnconfirmed("Private bundle finalization unconfirmed")
    if result["allowed"] and result["status"] != "ready":
        raise BundleCommitUnconfirmed("Debit without durable RPH ready marker")
    if not result["allowed"] and result["status"] != "prepared":
        raise BundleCommitUnconfirmed("Exhausted job marked ready")
    return result
