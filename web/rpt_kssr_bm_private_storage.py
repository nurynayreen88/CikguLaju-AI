"""Read an exact, SHA-pinned KSSR BM Word object from PRIVATE Supabase Storage.

Opt-in only; call AFTER session and paid-entitlement checks. No signed/public
URLs, redirects, user-supplied object keys, credits, payment or DB writes.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zipfile import BadZipFile, ZipFile

from web import rpt_2027_kssr_bm_word as bm_word

HOST = "soxakntcanbycjoygrcx.supabase.co"
BUCKET = "cikgulaju-materials"
PREFIX = "rpt-premium/bahasa-melayu-kssr-2027"
MIMETYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class PrivateWordUnavailable(Exception):
    """Private object missing, corrupt or server credentials unavailable."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _server_settings(config):
    if not isinstance(config, dict) or config.get("account_backend") != "supabase":
        raise PrivateWordUnavailable("Private storage backend unavailable")
    url, key = config.get("supabase_url"), config.get("supabase_key")
    parts = urlsplit(url if isinstance(url, str) else "")
    if (parts.scheme != "https" or parts.hostname != HOST
            or parts.path not in ("", "/") or parts.port is not None
            or parts.username or parts.password or parts.query or parts.fragment
            or not isinstance(key, str) or len(key) < 30):
        raise PrivateWordUnavailable("Private storage configuration unavailable")
    # A publishable key can never be trusted as the server-side storage secret.
    if key.startswith("sb_publishable_"):
        raise PrivateWordUnavailable("Storage service key required")
    return url.rstrip("/"), key


def verified_manifest_entry(year, *, root=bm_word.ROOT):
    """Validate manifest and academic-source hashes without requiring local DOCX."""
    if type(year) is not int or year not in bm_word.YEARS:
        return None
    root = Path(root)
    manifest = bm_word._manifest(root / "kssr_word_premium" / "manifest.json")
    if not isinstance(manifest, dict):
        return None
    entry = manifest.get("files", {}).get(str(year))
    if not isinstance(entry, dict):
        return None
    if (entry.get("path") != f"bahasa_melayu/tahun_{year}.docx"
            or entry.get("status") != "DRAF_SEMAKAN_NOT_ACADEMIC_FINAL"
            or type(entry.get("bytes")) is not int
            or not 20000 <= entry["bytes"] <= 3_000_000
            or not isinstance(entry.get("sha256"), str)
            or len(entry["sha256"]) != 64):
        return None
    try:
        source = Path(__file__).resolve().parents[1] / entry["source_html"]
        if source.is_symlink() or not source.is_file():
            return None
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry["source_html_sha256"]:
            return None
        pdf_manifest = json.loads((root / "web_2027_pdfs" / "manifest.json").read_text("utf-8"))
        if pdf_manifest["files"][f"bahasa_melayu:{year}"]["sha256"] != entry["source_pdf_sha256"]:
            return None
    except (OSError, ValueError, TypeError, KeyError):
        return None
    return entry


def _check_docx(blob, entry):
    if (not isinstance(blob, bytes) or len(blob) != entry["bytes"]
            or not blob.startswith(bytes((80, 75, 3, 4)))
            or hashlib.sha256(blob).hexdigest() != entry["sha256"]):
        raise PrivateWordUnavailable("Private Word checksum mismatch")
    try:
        with ZipFile(BytesIO(blob)) as archive:
            if "word/document.xml" not in archive.namelist() or archive.testzip() is not None:
                raise PrivateWordUnavailable("Private Word format invalid")
    except (BadZipFile, OSError, ValueError) as exc:
        raise PrivateWordUnavailable("Private Word format unavailable") from exc
    return blob


def fetch_document(year, config, *, root=bm_word.ROOT, opener=None):
    entry = verified_manifest_entry(year, root=root)
    if entry is None:
        raise PrivateWordUnavailable("Verified Word manifest unavailable")
    base, key = _server_settings(config)
    path = f"{PREFIX}/tahun_{year}.docx"
    headers = {"apikey": key, "Accept": MIMETYPE, "Cache-Control": "no-store"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    req = Request(f"{base}/storage/v1/object/authenticated/{BUCKET}/{path}",
                  headers=headers, method="GET")
    open_request = opener or build_opener(NoRedirects()).open
    try:
        with open_request(req, timeout=12) as response:
            if getattr(response, "status", None) != 200:
                raise PrivateWordUnavailable("Private Word download unavailable")
            data = response.read(entry["bytes"] + 1)
    except (HTTPError, URLError, OSError, ValueError) as exc:
        raise PrivateWordUnavailable("Private Word storage unavailable") from exc
    return _check_docx(data, entry), entry["sha256"]
