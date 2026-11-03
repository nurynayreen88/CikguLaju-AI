"""Paid-only Telegram PDF delivery for temporary Matematik 2027 RPT v28.

No external PDF links are sent. Assets must be mounted privately on the bot
server and are never committed to the public source repository by this module.
Fail closed if assets, entitlements or Telegram confirmation are unavailable.
"""
import os
import tempfile
from pathlib import Path
from rpt_2027.matematik.supabase_assets import ready as sb_ready, content as sb_content
from rpt_2027.matematik.private_bundle import private_pdf_root

YEARS = frozenset(range(2, 7))
FILE_TEMPLATE = "RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf"


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported RPT Matematik year")
    folder = os.environ.get("CIKGULAJU_RPT_MATH_PDF_DIR")
    if folder:
        return Path(folder) / (FILE_TEMPLATE % year)
    private_root = private_pdf_root()
    root = private_root if private_root is not None else Path(__file__).resolve().parent
    return root / (FILE_TEMPLATE % year)


def pdf_ready(year, ns=None):
    """Show a button only when a verified private asset source is ready."""
    try:
        path = pdf_path(year)
        if path.is_file() and path.stat().st_size >= 100000:
            with path.open("rb") as f:
                if f.read(5) == b"%PDF-":
                    return True
    except (OSError, ValueError):
        pass
    return bool(isinstance(ns, dict) and sb_ready(ns, year))


def install(ns):
    """Wrap only Mathematics download callbacks, preserving every other route."""
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

        # Never trust a saved, forwarded or forged button to bypass the menu.
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
        if not pdf_ready(year, ns=ns):
            return send(
                cid,
                "⚠️ PDF RPT Matematik Tahun %d v28 belum tersedia pada pelayan. "
                "Tiada pautan terbuka atau fail tahun lain dihantar sebagai pengganti." % year,
            )
        try:
            caption = "RPT Matematik Tahun %d — 2027 v28 (DRAF/SEMENTARA)" % year
            if pdf_ready(year):  # Existing private local file, if configured.
                result = send_document(cid, str(pdf_path(year)), caption)
            else:
                # Stored in a separate private Supabase asset table, not
                # the curriculum or users table. Entitlement checked above.
                pdf = sb_content(ns, year)
                if pdf is None:
                    return send(cid, "⚠️ PDF Matematik gagal disahkan. Sila cuba lagi.")
                with tempfile.TemporaryDirectory(prefix="cikgulaju-math-v28-") as folder:
                    safe_path = Path(folder) / (FILE_TEMPLATE % year)
                    safe_path.write_bytes(pdf)
                    result = send_document(cid, str(safe_path), caption)

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
