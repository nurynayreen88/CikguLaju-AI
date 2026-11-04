"""Private Supabase-backed Pendidikan Islam RPT 2027 PDF Telegram delivery.

Read-only: no RPH credits, curriculum, profiles or payment state is changed.
"""
import base64
import hashlib
import os
from pathlib import Path
import tempfile

PDF_ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
TABLE = "cikgulaju_rpt_pi_pdf_assets"
FILE_TEMPLATE = "RPT_Pendidikan_Islam_Tahun_%d_2027_CikguLaju.pdf"


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported RPT Pendidikan Islam year")
    return PDF_ROOT / (FILE_TEMPLATE % year)


def _get_asset(year, ns, include_pdf=False):
    if type(year) is not int or year not in YEARS or not ns:
        return None
    columns = "year,filename,size_bytes,sha256"
    if include_pdf:
        columns += ",pdf_base64"
    try:
        rows = ns["_sb_request"](
            "GET", TABLE + "?year=eq.%d&release_enabled=is.true&select=" % year + columns
        ) or []
        if isinstance(rows, list) and len(rows) == 1:
            return rows[0]
    except Exception as exc:
        print("PI RPT 2027 asset lookup failed:", repr(exc), flush=True)
    return None


def pdf_ready(year, ns=None):
    """Only advertise this year if its matching private PDF asset is enabled."""
    return bool(_get_asset(year, ns))


def install(ns):
    if ns.get("CIKGULAJU_RPT_PI_2027_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info",
                "_is_admin", "_sb_request")
    if any(not callable(ns.get(name)) for name in required):
        return False
    previous = ns["callback"]
    send = ns["send"]

    def callback(cid, d):
        prefix = "rpt2027_pi_pdf_"
        data = str(d or "")
        if not data.startswith(prefix):
            return previous(cid, d)
        # The callback itself MUST recheck entitlement, even with an old button.
        try:
            allowed = bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception as exc:
            print("PI RPT entitlement check failed:", repr(exc), flush=True)
            allowed = False
        if not allowed:
            return send(
                cid, "🔒 <b>RPT 2027 — Akses Terhad</b>\n\n"
                "RPT hanya untuk pembangun, Rakan Pembangun yang disahkan "
                "dan pelanggan dengan langganan aktif.",
                [[{"text": "🏆 Jadi Rakan Pembangun", "callback_data": "pioneer_join"}],
                 [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        suffix = data[len(prefix):]
        if suffix not in ("2", "3", "4", "5", "6"):
            return send(cid, "Pilihan tahun RPT Pendidikan Islam tidak sah.")
        year = int(suffix)
        record = _get_asset(year, ns, include_pdf=True)
        if not record:
            return send(cid, "⚠️ PDF RPT Pendidikan Islam Tahun %d belum tersedia." % year)
        try:
            decoded = base64.b64decode(record.get("pdf_base64", ""), validate=True)
            if (not decoded.startswith(b"%PDF-")
                    or len(decoded) != int(record["size_bytes"])
                    or hashlib.sha256(decoded).hexdigest() != record["sha256"]):
                raise ValueError("RPT asset integrity mismatch")
            with tempfile.TemporaryDirectory(prefix="cikgulaju_pi_rpt_") as folder:
                filename = FILE_TEMPLATE % year
                target = os.path.join(folder, filename)
                with open(target, "wb") as handle:
                    handle.write(decoded)
                result = ns["send_document"](
                    cid, target,
                    "RPT Pendidikan Islam Tahun %d — 2027 (Cadangan untuk semakan guru)" % year)
            verify = ns.get("_telegram_delivery_ok_v25279")
            if callable(verify):
                confirmed = bool(verify(result))
            else:
                confirmed = (bool(getattr(result, "ok", False))
                             and result.json().get("ok") is True)
            if not confirmed:
                raise RuntimeError("Telegram did not confirm sendDocument")
            return result
        except Exception as exc:
            print("PI RPT 2027 delivery failed:", repr(exc), flush=True)
            return send(cid, "⚠️ Muat turun PDF belum berjaya. Sila cuba lagi.")

    ns["callback"] = callback
    ns["CIKGULAJU_RPT_PI_2027_INSTALLED"] = True
    return True
