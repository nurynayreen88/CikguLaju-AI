"""One-time, fail-closed PI premium v2 archive migration on Web startup.

The source URL is a short-lived private download reference held ONLY in Render
environment variables. No source URL or Supabase secret is embedded in Git.
The production UI remains on verified v1 until v2 is enabled separately.
"""
from __future__ import annotations

import hashlib
import os
import threading
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SIZE = 49_779_272
DIGEST = "f68807065178f15e2acb4dd25caa7f179cad33a02d186327ec89515c9ae10569"
BUCKET = "cikgulaju-materials"
OBJECT = "rph-premium/pi-2027/v2/696-word-pdf-bundle.zip"
FLAG = "CIKGULAJU_PI_IMPORT_ONCE"
SOURCE = "CIKGULAJU_PI_IMPORT_URL"


def _source():
    value = os.environ.get(SOURCE, "").strip()
    parts = urlsplit(value)
    if (parts.scheme != "https"
            or parts.hostname != "sdmntprindiasocentral.oaiusercontent.com"
            or not parts.path.endswith("/raw")
            or parts.username or parts.password or not parts.query):
        raise RuntimeError("PI migration private source unavailable")
    return value


def _destination():
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    parts = urlsplit(base)
    if (parts.scheme != "https"
            or parts.hostname != "soxakntcanbycjoygrcx.supabase.co"
            or parts.path not in ("", "/") or parts.query or parts.fragment
            or not isinstance(key, str) or len(key) < 30):
        raise RuntimeError("PI migration server storage configuration unavailable")
    headers = {"apikey": key, "Content-Type": "application/zip",
               "Cache-Control": "no-store", "x-upsert": "false"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    return base + "/storage/v1/object/" + BUCKET + "/" + OBJECT, headers


def _import():
    try:
        url, headers = _destination()
        # Do not replace v1, and do not upsert over a prior v2 upload.
        lookup = url.replace("/object/", "/object/authenticated/", 1)
        try:
            with urlopen(Request(lookup, headers=headers, method="HEAD"), timeout=12) as check:
                if check.status == 200:
                    print("CIKGULAJU_PI_V2_IMPORT_ALREADY_EXISTS", flush=True)
                    return
        except HTTPError as exc:
            if exc.code != 404:
                raise
        with urlopen(Request(_source(), headers={"Accept": "application/zip"}), timeout=100) as response:
            blob = response.read(SIZE + 1)
        if len(blob) != SIZE or hashlib.sha256(blob).hexdigest() != DIGEST:
            raise RuntimeError("PI source archive size or SHA-256 mismatch")
        import zipfile
        from io import BytesIO
        with zipfile.ZipFile(BytesIO(blob)) as archive:
            if len(archive.namelist()) != 1392 or archive.testzip() is not None:
                raise RuntimeError("PI source archive manifest or CRC mismatch")
        request = Request(url, data=blob, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=160) as uploaded:
                if uploaded.status not in (200, 201):
                    raise RuntimeError("PI Storage did not confirm upload")
        except HTTPError as exc:
            if exc.code == 409:
                print("CIKGULAJU_PI_V2_IMPORT_ALREADY_EXISTS", flush=True)
                return
            print("CIKGULAJU_PI_V2_IMPORT_HTTP_ERROR", exc.code, flush=True)
            return
        print("CIKGULAJU_PI_V2_IMPORT_SUCCESS bytes=49779272", flush=True)
    except Exception as exc:
        # Never log the bearer source URL or any credentials.
        print("CIKGULAJU_PI_V2_IMPORT_FAILED", type(exc).__name__, flush=True)


def start_when_enabled():
    if os.environ.get(FLAG) != "1":
        return False
    threading.Thread(target=_import, name="cikgulaju-pi-v2-once", daemon=True).start()
    return True
