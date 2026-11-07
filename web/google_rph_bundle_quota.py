"""Staging-only *internal* post-render Google RPH credit authorization.

This module is NOT an HTTP route and is not wired to the live RPH generator.
The caller must first generate both Word + PDF from the verified Telegram
source. A failure to produce either file cannot spend one of the 10 credits.

A server-generated UUID is reused for a single complete bundle; if the RPC
times out after commit, do not assume no charge or regenerate a new reference.
"""
from hashlib import sha256
from io import BytesIO
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

from web.provider_neutral_web_identity import VerifiedWebIdentity
from web.google_staging_service_auth import staging_service_headers

MAX_DOCUMENT_BYTES = 12 * 1024 * 1024
MAX_WORD_XML_BYTES = 4 * 1024 * 1024


class BundleNotRendered(ValueError):
    """Invalid/incomplete documents: never charge."""


class BundleChargeUnconfirmed(RuntimeError):
    """Unknown backend commit outcome; reconcile the same reference."""


def server_generation_reference():
    return str(uuid.uuid4())


def _validated_bytes(document, kind):
    if not isinstance(document, bytes) or not 500 <= len(document) <= MAX_DOCUMENT_BYTES:
        raise BundleNotRendered("Missing, invalid or oversized " + kind)
    if kind == "pdf":
        if not document.startswith(b"%PDF-") or b"%%EOF" not in document[-2048:]:
            raise BundleNotRendered("Incomplete generated PDF")
    else:
        try:
            with ZipFile(BytesIO(document)) as archive:
                for name in ("[Content_Types].xml", "word/document.xml"):
                    info = archive.getinfo(name)
                    if info.file_size < 1 or info.file_size > MAX_WORD_XML_BYTES:
                        raise BundleNotRendered("Incomplete or oversized DOCX content")
        except (BadZipFile, KeyError, OSError):
            raise BundleNotRendered("Invalid Word document") from None
    return document


def rendered_bundle_sha256(word_bytes, pdf_bytes):
    """A deterministic digest for the SAME successful Word+PDF bundle.

    Hashes PDF and Word bytes without storing any teacher names, school
    identities, private files or raw document content in the database ledger.
    """
    word = _validated_bytes(word_bytes, "word")
    pdf = _validated_bytes(pdf_bytes, "pdf")
    return sha256(b"cikgulaju-google-rph-bundle-v1\\0" +
                  sha256(word).digest() + sha256(pdf).digest()).hexdigest()


def charge_successful_google_bundle(config, actor, generation_ref, word_bytes,
                                    pdf_bytes, *, transport=None):
    """Call only from trusted server code with a verified Google UUID actor.

    Never accept actor, reference, or digest directly from browser input.
    There is intentionally no public endpoint calling this function.
    """
    if not isinstance(actor, VerifiedWebIdentity) or actor.provider != "google":
        raise ValueError("Verified Google Web identity required")
    if actor.account_id is None or actor.account_id != actor.subject:
        raise ValueError("Google account identity mismatch")
    try:
        account_id = str(uuid.UUID(actor.account_id))
        canonical_ref = str(uuid.UUID(generation_ref))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Canonical server reference required") from None
    if account_id != actor.account_id or canonical_ref != generation_ref:
        raise ValueError("Noncanonical identity or server reference")

    # Do not call the database at all unless both native files are complete.
    manifest = rendered_bundle_sha256(word_bytes, pdf_bytes)

    base = config.get("supabase_url", "").rstrip("/")
    key = config.get("staging_service_key", "")
    if (not base.startswith("https://")
            or ".supabase.co" not in base
            or not isinstance(key, str) or len(key) < 24):
        raise ValueError("Staging backend must be explicitly configured")
    headers = {**staging_service_headers(key), "Content-Type": "application/json"}
    payload = json.dumps({"p_account_id": account_id,
                          "p_generation_ref": canonical_ref,
                          "p_manifest_sha256": manifest}).encode()
    req = Request(base + "/rest/v1/rpc/consume_web_rph_bundle_staging",
                  data=payload, method="POST", headers=headers)
    try:
        opener = transport or urlopen
        with opener(req, timeout=8) as result:
            raw = result.read(4097)
            if result.status != 200 or len(raw) > 4096:
                raise BundleChargeUnconfirmed("Unexpected quota RPC response")
        reply = json.loads(raw)
        if (not isinstance(reply, dict)
                or type(reply.get("allowed")) is not bool
                or type(reply.get("replayed")) is not bool
                or type(reply.get("remaining")) is not int
                or not 0 <= reply["remaining"] <= 10
                or reply.get("access_mode") not in ("trial","paid","exhausted")
                or (not reply["allowed"]) != (reply["access_mode"] == "exhausted")):
            raise BundleChargeUnconfirmed("Quota status invalid; verify ledger")
        return reply
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, TypeError, KeyError):
        raise BundleChargeUnconfirmed(
            "RPH credit outcome uncertain; check same reference before any retry") from None
