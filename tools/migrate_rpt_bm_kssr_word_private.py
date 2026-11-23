"""One-time, idempotent migration of five checksum-pinned BM KSSR Word files.

Run from a trusted server with SUPABASE_URL and SUPABASE_SECRET_KEY already in
its environment. No credentials or Word bytes go into GitHub Actions artifacts.
Local check is default; --upload requires an explicit private approval flag.

After all five objects are present and verified, the separate Web read flag
CIKGULAJU_KSSR_BM_WORD_PRIVATE=1 can be enabled by operations.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from web.rpt_2027_kssr_bm_word import YEARS, word_document
from web.rpt_kssr_bm_private_storage import (
    BUCKET, HOST, MIMETYPE, PREFIX, NoRedirects, PrivateWordUnavailable,
    _server_settings, fetch_document,
)

def _request(url, key, *, data=None, method="GET"):
    headers = {"apikey": key, "Accept": "application/json", "Cache-Control": "no-store"}
    if not key.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + key
    if data is not None:
        headers.update({"Content-Type": MIMETYPE, "x-upsert": "false"})
    return Request(url, headers=headers, data=data, method=method)

def _config():
    return {
        "account_backend": "supabase",
        "supabase_url": os.environ.get("SUPABASE_URL", ""),
        "supabase_key": os.environ.get("SUPABASE_SECRET_KEY", ""),
    }

def private_bucket_ready(url, key, opener):
    request = _request(f"{url}/storage/v1/bucket/{BUCKET}", key)
    with opener(request, timeout=12) as response:
        if response.status != 200:
            raise PrivateWordUnavailable("Private bucket metadata unavailable")
        blob = response.read(8001)
    if len(blob) > 8000:
        raise PrivateWordUnavailable("Bucket metadata too large")
    meta = json.loads(blob)
    if not isinstance(meta, dict) or meta.get("id") != BUCKET or meta.get("public") is not False:
        raise PrivateWordUnavailable("Bucket must remain PRIVATE")

def migrate(*, upload=False, opener=None):
    """Returns verified years. Never overwrite an existing object."""
    sources = {}
    for year in YEARS:
        source = word_document(year)
        if source is None:
            raise PrivateWordUnavailable("Source Word missing or checksum invalid")
        path, digest = source
        sources[year] = (path.read_bytes(), digest)
    if not upload:
        return list(sources)
    if os.environ.get("CIKGULAJU_PRIVATE_WORD_MIGRATION_OK") != "YES":
        raise PrivateWordUnavailable("Explicit one-time migration flag required")
    config = _config()
    url, key = _server_settings(config)
    do_open = opener or build_opener(NoRedirects()).open
    private_bucket_ready(url, key, do_open)
    verified = []
    for year, (source, expected_sha) in sources.items():
        # If the object already exists and matches, do not overwrite.
        existing = None
        try:
            existing = fetch_document(year, config, opener=do_open)
        except PrivateWordUnavailable:
            pass
        if existing is None:
            target = f"{url}/storage/v1/object/{BUCKET}/{PREFIX}/tahun_{year}.docx"
            try:
                with do_open(_request(target, key, data=source, method="POST"), timeout=20) as resp:
                    if resp.status not in (200, 201):
                        raise PrivateWordUnavailable("Upload response invalid")
            except HTTPError as exc:
                # A conflict is not success; only allow an identical verified object.
                if exc.code not in (400, 409):
                    raise PrivateWordUnavailable("Private upload unavailable") from exc
            except (URLError, OSError) as exc:
                raise PrivateWordUnavailable("Private upload unavailable") from exc
        # A 400/409 is not success. Verify exact bytes regardless of upload response.
        actual, digest = fetch_document(year, config, opener=do_open)
        if digest != expected_sha or actual != source:
            raise PrivateWordUnavailable("Private upload verification failed")
        verified.append(year)
    return verified

def main():
    parser = argparse.ArgumentParser(description="Stage/verify private KSSR BM Word migration")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to existing PRIVATE bucket, never overwrite")
    args = parser.parse_args()
    try:
        years = migrate(upload=args.upload)
    except (PrivateWordUnavailable, HTTPError, URLError, OSError, ValueError, TypeError) as exc:
        # Do not print server credentials, HTTP request objects or object URLs.
        print(f"PRIVATE WORD MIGRATION FAILED: {type(exc).__name__}", file=sys.stderr)
        return 1
    stage = "PRIVATE VERIFIED" if args.upload else "LOCAL CHECK ONLY"
    print(f"{stage}: years={','.join(str(y) for y in years)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
