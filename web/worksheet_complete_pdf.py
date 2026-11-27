"""Read-only complete worksheet packages: one verified PDF per exact SK Lesson.

No RPH generation, database mutations, direct Drive URL exposure, or quota debits.
Only byte-identical, reviewed PDFs are returned.
"""
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json
import os
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, build_opener
from web.native_telegram_rph_client import BlockRedirects

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "worksheets/catalog/english_web_batch1_20261127.json"
SOW = ROOT / "audits/english_primary_2_6_official_sow_index_20261103.json"
MAX_SIZE = 2 * 1024 * 1024

@lru_cache(maxsize=1)
def _sources():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    index = json.loads(SOW.read_text(encoding="utf-8"))
    if catalog.get("scope") != "KSSR SK" or catalog.get("delivery") != "complete-pdf":
        raise ValueError("Invalid worksheet catalog")
    return catalog["records"], index["lessons"]

def _norm(value):
    return " ".join(str(value or "").split()).casefold()

def resolve(year, lesson, unit):
    if type(year) is not int or year not in (3, 4) or type(lesson) is not int or not 1 <= lesson <= 160:
        return None
    if not isinstance(unit, str) or not unit.strip():
        return None
    records, index = _sources()
    key = f"{year}/{lesson}"
    rec, source = records.get(key), index.get(key)
    if not isinstance(rec, dict) or not isinstance(source, dict):
        return None
    if (source.get("n") != lesson or source.get("teacher_selected") is not False
            or _norm(source.get("topic")) != _norm(unit)
            or _norm(rec.get("unit")) != _norm(unit)
            or source.get("main_ls") != rec.get("main_sp")
            or source.get("complementary_ls") != rec.get("complementary_sp")):
        return None
    if (not re.fullmatch(r"[A-Za-z0-9_-]{10,100}", str(rec.get("drive_file_id", "")))
            or not re.fullmatch(r"[a-f0-9]{64}", str(rec.get("sha256", "")))
            or type(rec.get("size_bytes")) is not int
            or not 450 <= rec["size_bytes"] <= MAX_SIZE):
        return None
    return dict(rec)

@lru_cache(maxsize=16)
def _pdf(file_id, digest, size):
    # Only server-side credentials and a fixed table; the Drive ID is
    # retained as provenance, never used as a public download address.
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    secret = (os.environ.get("SUPABASE_SECRET_KEY", "") or
              os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""))
    origin = urlsplit(base)
    if (origin.scheme != "https" or not re.fullmatch(r"[a-z0-9]+\.supabase\.co", origin.netloc)
            or origin.path or origin.query or origin.fragment or not secret):
        raise ValueError("Private worksheet source unavailable")
    if not re.fullmatch(r"[a-f0-9]{64}", digest) or type(size) is not int or not 450 <= size <= MAX_SIZE:
        raise ValueError("Invalid worksheet identity")
    url = base + "/rest/v1/cikgulaju_worksheet_pdf_assets?" + urlencode({
        "asset_sha256": "eq." + digest, "select": "asset_sha256,size_bytes,pdf_bytes", "limit": 2})
    headers = {"apikey": secret, "Accept": "application/json"}
    if not secret.startswith("sb_secret_"):
        headers["Authorization"] = "Bearer " + secret
    request = Request(url, headers=headers, method="GET")
    with build_opener(BlockRedirects()).open(request, timeout=12) as response:
        if response.status != 200 or response.headers.get_content_type() != "application/json":
            raise ValueError("Worksheet PDF unavailable")
        body = response.read(size * 2 + 1024)
    rows = json.loads(body)
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("Worksheet asset missing or ambiguous")
    row = rows[0]
    if row.get("asset_sha256") != digest or row.get("size_bytes") != size:
        raise ValueError("Worksheet metadata mismatch")
    hex_bytes = row.get("pdf_bytes")
    if not isinstance(hex_bytes, str) or not hex_bytes.startswith("\\x") or len(hex_bytes) != 2 + 2 * size:
        raise ValueError("Worksheet encoding mismatch")
    raw = bytes.fromhex(hex_bytes[2:])
    if len(raw) != size or not raw.startswith(b"%PDF-") or sha256(raw).hexdigest() != digest:
        raise ValueError("Worksheet integrity mismatch")
    return raw

def complete_pdf(year, lesson, unit):
    rec = resolve(year, lesson, unit)
    if not rec:
        return None
    return _pdf(rec["drive_file_id"], rec["sha256"], rec["size_bytes"])
