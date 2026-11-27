"""Fail-closed BM worksheet selection from the signed native master identity."""
import json
from urllib.parse import urlencode
from urllib.request import Request
from web.native_telegram_bm_rph_client import _selection, _client, _backend
from web.worksheet_complete_pdf import _pdf

# Only independently audited material is eligible. The draft RPT ordinals
# for Membeli Bahan Kek and Kek Hari Lahir are not authoritative identities.
RECORDS = {
    (2, "Hidup Berjiran", "Majlis Pengikat Kemesraan"): {
        "standards": {("2.2", "2.2.1")},
        "drive_file_id": "1IQ2yLLNXRQNPkTMP2aKJNO6D25F1qqUF",
        "sha256": "4c8c2931888a038d2e6549ff415727fd2d722ad98b5069e54b310f48a5143c5d",
        "size_bytes": 85641,
        "filename": "CIKGULAJU_LATIHAN_BM_T2_MAJLIS_PENGIKAT_KEMESRAAN.pdf",
    }
}

def resolve_bm(year, unit, token, *, opener=None):
    args = _selection(year, unit, token)
    if not any(k[:2] == (year, unit) for k in RECORDS):
        return None
    base, secret = _backend()
    req = Request(base + "/internal/rph/v1/bm-sequence/worksheet-identity?" +
                  urlencode(args), method="GET", headers={
                      "Authorization": "Bearer " + secret,
                      "Accept": "application/json",
                  })
    with (opener or _client()).open(req, timeout=12) as response:
        if response.status != 200:
            return None
        data = response.read(4097)
    if len(data) > 4096:
        return None
    row = json.loads(data)
    if (not isinstance(row, dict) or row.get("available") is not True
            or row.get("year") != year or row.get("subject") != "BM"
            or row.get("unit") != unit or row.get("token") != token
            or not isinstance(row.get("topic"), str)):
        return None
    record = RECORDS.get((year, unit, row["topic"]))
    if record is None:
        return None
    standards = row.get("standards")
    if not isinstance(standards, list) or not all(
        isinstance(x, dict) and isinstance(x.get("sk"), str)
        and isinstance(x.get("sp"), str) for x in standards
    ):
        return None
    if {(x["sk"], x["sp"]) for x in standards} != record["standards"]:
        return None
    return dict(record)

def complete_bm_pdf(year, unit, token):
    record = resolve_bm(year, unit, token)
    if record is None:
        return None
    return (_pdf(record["drive_file_id"], record["sha256"],
                 record["size_bytes"]), record["filename"])
