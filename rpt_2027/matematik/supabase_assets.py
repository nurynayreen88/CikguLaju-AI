"""Private read-only RPT Matematik v28 asset adapter (server-side Supabase).

Caller must authenticate the Telegram account and confirm the active RPT
entitlement BEFORE using this module. Never expose the source rows, file
bytes or Supabase credentials in a Telegram/web response.
"""
import base64
import binascii
import hashlib
import re

TABLE = "cikgulaju_rpt_math_pdf_assets"
VERSION = "v28"
NAMES = {year: f"RPT_Matematik_Tahun_{year}_2027_v28_SEMENTARA.pdf"
         for year in range(2, 7)}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _row(ns, year, *, with_content):
    if type(year) is not int or year not in NAMES:
        return None
    sb = ns.get("_sb_request")
    if not callable(sb):
        return None
    columns = "year,version,filename,sha256,size_bytes"
    if with_content:
        columns += ",pdf_base64"
    url = (f"{TABLE}?year=eq.{year}&version=eq.{VERSION}"
           f"&release_enabled=eq.true&select={columns}&limit=2")
    try:
        rows = sb("GET", url)
    except Exception:
        return None
    if not isinstance(rows, list) or len(rows) != 1:
        return None
    row = rows[0]
    if not isinstance(row, dict):
        return None
    if (row.get("year") != year or row.get("version") != VERSION
            or row.get("filename") != NAMES[year]
            or not isinstance(row.get("sha256"), str)
            or not _SHA256.fullmatch(row["sha256"])
            or type(row.get("size_bytes")) is not int
            or not 100000 <= row["size_bytes"] <= 1024 * 1024):
        return None
    return row


def ready(ns, year):
    """Small metadata-only query; fails closed when DB/API is unavailable."""
    return _row(ns, year, with_content=False) is not None


def content(ns, year):
    """Return verified PDF bytes, or None; never return a public download URL."""
    row = _row(ns, year, with_content=True)
    if row is None:
        return None
    data = row.get("pdf_base64")
    if not isinstance(data, str) or len(data) > 1500000:
        return None
    try:
        pdf = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error):
        return None
    if (len(pdf) != row["size_bytes"]
            or not pdf.startswith(b"%PDF-")
            or hashlib.sha256(pdf).hexdigest() != row["sha256"]):
        return None
    return pdf
