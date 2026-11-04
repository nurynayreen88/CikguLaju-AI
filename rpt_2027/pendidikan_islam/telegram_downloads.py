"""Paid Telegram route for Pendidikan Islam RPT 2027 PDF downloads.

Additive and fail-closed; no DB, RPH, quota, subscription, or profile writes.
The supplied RPT remains a suggested/teacher-review document.
"""
from pathlib import Path

PDF_ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
FILE_TEMPLATE = "RPT_Pendidikan_Islam_Tahun_%d_2027_CikguLaju.pdf"


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported Pendidikan Islam RPT year")
    return PDF_ROOT / (FILE_TEMPLATE % year)


def pdf_ready(year, ns=None):
    """Only advertise a download if the matching local PDF is valid."""
    try:
        path = pdf_path(year)
        if not path.is_file() or path.stat().st_size < 100000:
            return False
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except (OSError, ValueError):
        return False


def install(ns):
    """Wrap only Pendidikan Islam RPT callbacks, preserving every other route."""
    if ns.get("CIKGULAJU_RPT_PI_2027_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(name)) for name in required):
        return False
    previous = ns["callback"]
    send = ns["send"]
    send_document = ns["send_document"]
    prefix = "rpt2027_pi_pdf_"

    def callback(cid, d):
        data = str(d or "")
        if not data.startswith(prefix):
            return previous(cid, d)

        # Paid-access check is repeated for stale/forged callback data.
        try:
            allowed = bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
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
        if not pdf_ready(year):
            return send(
                cid, "⚠️ PDF RPT Pendidikan Islam Tahun %d belum tersedia pada pelayan. "
                "Tiada fail lain dihantar sebagai pengganti." % year)

        try:
            result = send_document(
                cid, str(pdf_path(year)),
                "RPT Pendidikan Islam Tahun %d — 2027 (Cadangan untuk semakan guru)" % year)
            check = ns.get("_telegram_delivery_ok_v25279")
            if callable(check):
                confirmed = bool(check(result))
            else:
                confirmed = (bool(getattr(result, "ok", False))
                             and result.json().get("ok") is True)
            if not confirmed:
                return send(cid, "⚠️ Telegram belum mengesahkan penghantaran PDF RPT. Sila cuba lagi.")
            return result
        except Exception as exc:
            print("PI RPT 2027 PDF delivery failed:", repr(exc), flush=True)
            return send(cid, "⚠️ Muat turun RPT gagal. Sila cuba lagi.")

    ns["callback"] = callback
    ns["CIKGULAJU_RPT_PI_2027_INSTALLED"] = True
    return True
