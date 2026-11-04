"""2027 PJPK RPT PDFs in the paid Telegram RPT 2027 menu (DRAF).

Read-only delivery. No user DB or curriculum DB writes, no RPH credit debit,
subscription updates, change of READY flags, or unapproved Year 1 assets.
"""
from pathlib import Path

PDF_ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
FILE_TEMPLATE = "RPT_PJPK_Tahun_%d_2027_DRAF.pdf"
PREFIX = "rpt2027_pjpk_pdf_"


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("RPT PJPK Tahun tidak sah")
    return PDF_ROOT / (FILE_TEMPLATE % year)


def pdf_ready(year, ns=None):
    """Only present buttons for the exact local PDF if the header and size pass."""
    try:
        path = pdf_path(year)
        if not path.is_file() or path.stat().st_size < 50000:
            return False
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except (OSError, ValueError):
        return False


def install(ns):
    """Wrap only PJPK RPT download callbacks and delegate all other routes."""
    if ns.get("CIKGULAJU_RPT_PJPK_2027_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(key)) for key in required):
        return False
    previous = ns["callback"]
    send = ns["send"]
    send_document = ns["send_document"]

    def callback(cid, data):
        value = str(data or "")
        if not value.startswith(PREFIX):
            return previous(cid, data)
        try:
            allowed = bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
            allowed = False
        if not allowed:
            return send(
                cid,
                "🔒 <b>RPT PJPK 2027 — Akses Terhad</b>\n\n"
                "Muat turun RPT tersedia kepada Rakan Pembangun yang disahkan "
                "dan pelanggan berlangganan aktif.",
                [[{"text": "🏆 Jadi Rakan Pembangun", "callback_data": "pioneer_join"}],
                 [{"text": "🏠 Menu Utama", "callback_data": "home"}]])
        suffix = value[len(PREFIX):]
        if suffix not in ("2", "3", "4", "5", "6"):
            return send(cid, "Pilihan tahun RPT PJPK tidak sah.")
        year = int(suffix)
        if not pdf_ready(year):
            return send(
                cid, "⚠️ RPT PJPK Tahun %d 2027 belum tersedia pada pelayan. "
                     "Tiada PDF lain digunakan sebagai pengganti." % year)
        try:
            result = send_document(
                cid, str(pdf_path(year)),
                "RPT PJPK Tahun %d — 2027 (DRAF untuk semakan guru)" % year)
            check = ns.get("_telegram_delivery_ok_v25279")
            if callable(check):
                confirmed = bool(check(result))
            else:
                confirmed = (bool(getattr(result, "ok", False))
                             and result.json().get("ok") is True)
            if not confirmed:
                return send(cid, "⚠️ Penghantaran PDF belum disahkan Telegram. Cuba lagi.")
            return result
        except Exception as exc:
            print("PJPK RPT 2027 PDF delivery failed:", repr(exc), flush=True)
            return send(cid, "⚠️ Penghantaran RPT PJPK gagal. Sila cuba lagi.")

    ns["callback"] = callback
    ns["CIKGULAJU_RPT_PJPK_2027_INSTALLED"] = True
    return True
