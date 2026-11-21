"""Import 696 Pendidikan Islam RPH files into PRIVATE Supabase Storage.

One-off admin utility. No changes to teacher RPH content or to accounts,
login, quotas, and paid entitlements. This script does NOT publish a Web route.
Use an approved production session with server-only service-role credentials.

Inventory:
    python tools/import_pi_696_private_storage.py --archive /private/PI_696.zip
Upload:
    SUPABASE_URL=https://soxakntcanbycjoygrcx.supabase.co \
    SUPABASE_SERVICE_ROLE_KEY=... \
    python tools/import_pi_696_private_storage.py --archive /private/PI_696.zip --upload
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

BUCKET = "cikgulaju-materials"
PREFIX = "rph-premium/pi-2027/v1"
YEARS = {2: 112, 3: 147, 4: 151, 5: 143, 6: 143}
HELD_ORIGIN = [(2, 35), (6, 6), (6, 14), (6, 18), (6, 60), (6, 117)]
PATTERN = re.compile(
    r"Tahun_([2-6])/(Word|PDF)/CIKGULAJU_PI_T([2-6])_RPH_(\d{3})_AUDIT_PREMIUM\.(docx|pdf)"
)


def inventory(archive):
    """Validate the exact 696-source ZIP; avoid inventing lesson materials."""
    entries, seen = [], set()
    with ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("Invalid source archive")
        for name in z.namelist():
            m = PATTERN.fullmatch(name)
            if m is None:
                continue  # Internal QA files are never published.
            year, folder, copy_year, no, fmt = m.groups()
            year, no = int(year), int(no)
            key = (year, no, fmt)
            if year != int(copy_year) or (fmt == "docx") != (folder == "Word"):
                raise ValueError("Malformed file path: " + name)
            if key in seen:
                raise ValueError("Duplicate RPH: " + name)
            seen.add(key)
            data = z.read(name)
            if fmt == "pdf" and not data.startswith(b"%PDF-"):
                raise ValueError("Not a PDF: " + name)
            if fmt == "docx":
                try:
                    with ZipFile(io.BytesIO(data)) as doc:
                        if doc.testzip() or "word/document.xml" not in doc.namelist():
                            raise ValueError("Not an editable Word package: " + name)
                except BadZipFile as exc:
                    raise ValueError("Invalid Word package: " + name) from exc
            path = f"{PREFIX}/tahun-{year}/pdp-{no:03d}.{fmt}"
            entries.append((name, path, hashlib.sha256(data).hexdigest(), len(data)))
    required = {(year, no, fmt) for year, total in YEARS.items()
                for no in range(1, total + 1) for fmt in ("docx", "pdf")}
    if seen != required or len(entries) != 1392:
        raise ValueError("The exact 696 matched Word/PDF pairs are required")
    return sorted(entries, key=lambda x: x[1])


def storage_request(url, secret, method, data=None, mime=None):
    headers = {"apikey": secret, "Authorization": "Bearer " + secret,
               "Accept": "application/json"}
    if mime:
        headers["Content-Type"] = mime
    return urlopen(Request(url, method=method, data=data, headers=headers), timeout=60)


def upload(archive, entries, base, secret):
    parts = urlsplit(base)
    if (parts.scheme != "https" or parts.hostname != "soxakntcanbycjoygrcx.supabase.co"
            or parts.username or parts.password or parts.query or len(secret) < 30):
        raise ValueError("Production Supabase service-role configuration missing")
    with storage_request(base + "/storage/v1/bucket/" + BUCKET, secret, "GET") as r:
        bucket = json.load(r)
    if bucket.get("public") is not False:
        raise ValueError("Refuse to upload to a public bucket")
    with ZipFile(archive) as z:
        for index, (member, object_key, digest, size) in enumerate(entries, 1):
            encoded = "/".join(quote(v, safe="") for v in object_key.split("/"))
            url = f"{base}/storage/v1/object/{BUCKET}/{encoded}"
            fmt = object_key.rsplit(".", 1)[-1]
            mime = ("application/pdf" if fmt == "pdf" else
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            body = z.read(member)
            if len(body) != size or hashlib.sha256(body).hexdigest() != digest:
                raise ValueError("Source changed during import")
            for retry in range(3):
                try:
                    with storage_request(url, secret, "POST", body, mime) as r:
                        if r.status not in (200, 201):
                            raise ValueError("Unexpected upload status")
                    break
                except HTTPError as exc:
                    if exc.code in (400, 409):
                        raise RuntimeError("Existing object requires content reconciliation: " + object_key) from exc
                    if retry == 2 or exc.code < 500:
                        raise RuntimeError("Upload failed: " + object_key) from exc
                except (TimeoutError, URLError) as exc:
                    if retry == 2:
                        raise RuntimeError("Storage temporarily unreachable: " + object_key) from exc
                time.sleep(2 ** retry)
            if index % 100 == 0:
                print(json.dumps({"uploaded": index, "expected": 1392}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--upload", action="store_true", help="Perform private Storage upload")
    parser.add_argument("--analysis", type=Path, help="Internal QA file outside RPH ZIP")
    args = parser.parse_args()
    entries = inventory(args.archive)
    report = {"lesson_count": 696, "asset_count": len(entries),
              "by_year": YEARS, "source_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
              "internal_review_only": [f"T{y}-L{n:03d}" for y, n in HELD_ORIGIN],
              "notice": "Review notes must not be included in teacher-facing Word or PDF."}
    if args.analysis:
        args.analysis.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.upload:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    secret = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    upload(args.archive, entries, url, secret)
    print("696 private RPH pairs uploaded to Supabase Storage")


if __name__ == "__main__":
    main()
