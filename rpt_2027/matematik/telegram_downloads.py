"""Telegram delivery of Matematik 2027 RPT PDFs, mirroring English 2027.

PDFs live beside this module in the GitHub repository, just like English
RPT PDFs. This module does not query Supabase or alter subscriptions, trial
quotas, RPH, curriculum databases, or other Telegram callback routes.

Important: the GitHub repository is public, so PDF files stored there are
publicly readable even though the Telegram menu is paid-only.
"""
from pathlib import Path

PDF_ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
FILE_TEMPLATE = "RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf"


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported RPT Matematik year")
    return PDF_ROOT / (FILE_TEMPLATE % year)


def pdf_ready(year, ns=None):
    """Keep ns optional for compatibility with the English RPT menu."""
    try:
        path = pdf_path(year)
        if not path.is_file() or path.stat().st_size < 100000:
            return False
        with path.open("rb") as document:
            return document.read(5) == b"%PDF-"
    except (OSError, ValueError):
        return False


def install(ns):
    """Wrap only Matematik PDF callbacks; delegate all other routes unchanged."""
    if ns.get("CIKGULAJU_RPT_MATEMATIK_2027_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(name)) for name in required):
        return False

    previous = ns["callback"]
    send = ns["send"]
    send_document = ns["send_document"]

    def callback(cid, d):
        data = str(d or "")
        prefix = "rpt2027_math_pdf_"
        if not data.startswith(prefix):
            return previous(cid, d)

        # Recheck entitlement even when a saved or forged button is used.
        try:
            allowed = bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
            allowed = False
        if not allowed:
            return send(
                cid,
                "🔒 <b>RPT 2027 — Akses Terhad</b>\n\n"
                "RPT hanya untuk pembangun, Rakan Pembangun yang disahkan "
                "dan pelanggan dengan langganan aktif.",
                [[{"text": "🏆 Jadi Rakan Pembangun", "callback_data": "pioneer_join"}],
                 [{"text": "🏠 Menu Utama", "callback_data": "home"}]],
            )

        suffix = data[len(prefix):]
        if suffix not in ("2", "3", "4", "5", "6"):
            return send(cid, "Pilihan tahun RPT Matematik tidak sah.")
        year = int(suffix)
        if not pdf_ready(year):
            return send(
                cid,
                "⚠️ PDF RPT Matematik Tahun %d v28 belum tersedia pada pelayan. "
                "Tiada fail tahun lain dihantar sebagai pengganti." % year,
            )

        try:
            result = send_document(
                cid, str(pdf_path(year)),
                "RPT Matematik Tahun %d — 2027 v28 (DRAF/SEMENTARA)" % year,
            )
            verify = ns.get("_telegram_delivery_ok_v25279")
            if callable(verify):
                confirmed = bool(verify(result))
            else:
                confirmed = (bool(getattr(result, "ok", False))
                             and result.json().get("ok") is True)
            if not confirmed:
                return send(cid, "⚠️ Telegram belum mengesahkan penghantaran PDF RPT. Sila cuba lagi.")
            return result
        except Exception as exc:
            print("MATH RPT 2027 PDF delivery failed:", repr(exc), flush=True)
            return send(cid, "⚠️ Muat turun RPT gagal. Sila cuba lagi.")

    ns["callback"] = callback
    ns["CIKGULAJU_RPT_MATEMATIK_2027_INSTALLED"] = True
    return True
