"""Read-only, paid-gated Telegram delivery of 2027 Bahasa Melayu RPT PDFs.

All files retain DRAF status. No writes to DB, subscriptions, quotas or RPH.
Year number and exact local PDF path are checked before every delivery.
"""
from pathlib import Path

PDF_ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
FILE_TEMPLATE = "RPT_Bahasa_Melayu_Tahun_%d_2027_DRAF.pdf"
CALLBACK_PREFIX = "rpt2027_bm_pdf_"


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Tahun RPT Bahasa Melayu tidak sah")
    return PDF_ROOT / (FILE_TEMPLATE % year)


def pdf_ready(year, ns=None):
    try:
        path = pdf_path(year)
        if not path.is_file() or path.stat().st_size < 50000:
            return False
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except (OSError, ValueError):
        return False


def install(ns):
    """Add only BM PDF callback; preserve every unrelated Telegram callback."""
    if ns.get("CIKGULAJU_RPT_BM_2027_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(name)) for name in required):
        return False
    previous = ns["callback"]
    send = ns["send"]
    send_document = ns["send_document"]

    def callback(cid, d):
        data = str(d or "")
        if not data.startswith(CALLBACK_PREFIX):
            return previous(cid, d)

        try:
            allowed = bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
            allowed = False
        if not allowed:
            return send(cid,
                        "🔒 <b>RPT 2027 — Akses Terhad</b>\n\n"
                        "RPT hanya untuk pembangun, Rakan Pembangun yang disahkan "
                        "dan pelanggan dengan langganan aktif.",
                        [[{"text": "🏆 Jadi Rakan Pembangun", "callback_data": "pioneer_join"}],
                         [{"text": "🏠 Menu Utama", "callback_data": "home"}]])

        suffix = data[len(CALLBACK_PREFIX):]
        if suffix not in ("2", "3", "4", "5", "6"):
            return send(cid, "Pilihan tahun RPT Bahasa Melayu tidak sah.")
        year = int(suffix)
        if not pdf_ready(year):
            return send(cid,
                        "⚠️ PDF RPT Bahasa Melayu Tahun %d belum tersedia pada pelayan. "
                        "Tiada fail tahun lain dihantar sebagai pengganti." % year)
        try:
            result = send_document(
                cid, str(pdf_path(year)),
                "RPT Bahasa Melayu Tahun %d — 2027 (PDF • DRAF untuk semakan guru)" % year
            )
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
            print("BM RPT 2027 PDF delivery failed:", repr(exc), flush=True)
            return send(cid, "⚠️ Muat turun RPT Bahasa Melayu gagal. Sila cuba lagi.")

    ns["callback"] = callback
    ns["CIKGULAJU_RPT_BM_2027_INSTALLED"] = True
    return True
