"""Read-only Telegram delivery of English 2027 RPT PDFs.

This is installed after app.py's existing callback wrappers by the active WSGI
entrypoint. It never alters RPH credit accounting, subscriptions or the DB.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from rpt_2027.psv.telegram_downloads import pdf_ready as psv_pdf_ready, build_pdf as build_psv_pdf
from rpt_2027.matematik.telegram_downloads import pdf_ready as math_pdf_ready
from rpt_2027.bahasa_melayu.telegram_downloads import pdf_ready as bm_pdf_ready
from rpt_2027.pendidikan_islam.telegram_downloads import pdf_ready as pi_pdf_ready
from rpt_2027.pjpk.telegram_downloads import pdf_ready as pjpk_pdf_ready
from rpt_2027.pendidikan_moral.telegram_downloads import pdf_ready as moral_pdf_ready
from rpt_2027.pendidikan_moral.complete_96_downloads import combined_pdf_ready as moral_combined_pdf_ready

PDF_ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported RPT English year")
    return PDF_ROOT / ("RPT_ENGLISH_TAHUN_%d_2027_UNTUK_GURU.pdf" % year)


def install(ns):
    """Wrap only RPT callbacks, retaining the existing callback for everything else."""
    if ns.get("CIKGULAJU_RPT_ENGLISH_2027_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(name)) for name in required):
        return False
    previous = ns["callback"]
    send = ns["send"]
    send_document = ns["send_document"]

    def allowed(cid):
        # Use the same entitlement authority as the existing RPT 2027 menu.
        try:
            return bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
            return False

    def locked(cid):
        return send(cid,
            "🔒 <b>RPT 2027 — Akses Terhad</b>\n\n"
            "RPT hanya untuk pembangun, Rakan Pembangun yang disahkan "
            "dan pelanggan dengan langganan aktif.",
            [[{"text": "🏆 Jadi Rakan Pembangun", "callback_data": "pioneer_join"}],
             [{"text": "🏠 Menu Utama", "callback_data": "home"}]])

    def callback(cid, d):
        data = str(d or "")
        is_year = data.startswith("rpt2027_year_")
        is_download = data.startswith("rpt2027_en_pdf_")
        is_psv = data.startswith("rpt2027_psv_pdf_")
        if data != "rpt2027_home" and not is_year and not is_download and not is_psv:
            return previous(cid, d)
        # Enforce entitlement again for stale/forged buttons and downloads.
        if not allowed(cid):
            return locked(cid)
        if data == "rpt2027_home":
            kb = [[{"text": "Tahun %s" % year,
                    "callback_data": "rpt2027_year_%s" % year}]
                  for year in range(1, 7)]
            kb.append([{"text": "🏠 Menu Utama", "callback_data": "home"}])
            return send(cid,
                "📅 <b>RPT 2027</b>\n\n"
                "English Tahun 2–6 tersedia dalam PDF (160 Lesson/tahun). Bahasa Melayu: RPT DRAF untuk semakan, jika tersedia. Pendidikan Islam: RPT cadangan, jika tersedia. "
                "Matematik v28 dipaparkan hanya apabila PDF DRAF/SEMENTARA tersedia. PJPK Tahun 2–6: RPT DRAF (jika tersedia). Pendidikan Moral: satu PDF RPT merangkumi Kumpulan A/B (96 sesi/tahun). PSV: 42 PdP cadangan bagi Tahun 2–6.",
                kb)
        if is_year:
            suffix = data[len("rpt2027_year_"):]
            if suffix not in ("2", "3", "4", "5", "6"):
                return previous(cid, d)
            year = int(suffix)
            kb = [[{"text": "📥 English (PDF)", "callback_data": "rpt2027_en_pdf_%d" % year}]]
            if bm_pdf_ready(year):
                kb.append([{"text": "📥 Bahasa Melayu (PDF • DRAF)",
                            "callback_data": "rpt2027_bm_pdf_%d" % year}])
            # Do not advertise temporary PDFs until mounted and header-checked.
            if math_pdf_ready(year, ns=ns):
                kb.append([{"text": "📥 Matematik (PDF v28 • DRAF/SEMENTARA)",
                            "callback_data": "rpt2027_math_pdf_%d" % year}])
            if pi_pdf_ready(year):
                kb.append([{"text": "📥 Pendidikan Islam (PDF • Cadangan)",
                            "callback_data": "rpt2027_pi_pdf_%d" % year}])
            if pjpk_pdf_ready(year):
                kb.append([{"text": "📥 PJPK (PDF • DRAF 2027)",
                            "callback_data": "rpt2027_pjpk_pdf_%d" % year}])
            if moral_combined_pdf_ready(year):
                kb.append([{"text": "📥 Pendidikan Moral (PDF)",
                            "callback_data": "rpt2027_pm_ab_pdf_%d" % year}])
            if psv_pdf_ready(year):
                kb.append([{"text": "📥 Pendidikan Seni Visual (PDF)",
                            "callback_data": "rpt2027_psv_pdf_%d" % year}])
            kb.extend([
                [{"text": "⬅️ Pilih Tahun", "callback_data": "rpt2027_home"}],
                [{"text": "🏠 Menu Utama", "callback_data": "home"}],
            ])
            return send(cid,
                "📅 <b>RPT 2027 — Tahun %d</b>\n\n"
                "Pilih subjek untuk memuat turun RPT.\n"
                "English: 160 Lesson; Kumpulan A/B dalam satu PDF.\nBahasa Melayu: RPT 2027 DRAF untuk semakan guru, jika tersedia.\n"
                "Matematik v28: DRAF/SEMENTARA, jika fail tersedia.\nPendidikan Islam: cadangan untuk semakan guru, jika fail tersedia.\nPJPK: RPT cadangan PdP 2027 (DRAF), jika tersedia.\nPendidikan Moral: satu fail PDF dengan Kumpulan A dan B, merangkumi 42 PdP teras dan 54 sesi pengukuhan.\n\n"
                "PSV: 42 PdP cadangan (PDF A4 landscape).\n\nTarikh individu bergantung kepada jadual kelas serta cuti negeri." % year,
                kb)
        if is_psv:
            suffix = data[len("rpt2027_psv_pdf_"):]
            if suffix not in ("2", "3", "4", "5", "6"):
                return send(cid, "Pilihan tahun RPT PSV tidak sah.")
            year = int(suffix)
            if not psv_pdf_ready(year):
                return send(cid, "RPT PSV tahun ini belum tersedia.")
            try:
                with TemporaryDirectory(prefix="cikgulaju_rpt_psv_") as folder:
                    path = build_psv_pdf(year, Path(folder) / (
                        "RPT_Pendidikan_Seni_Visual_Tahun_%d_2027.pdf" % year))
                    result = send_document(cid, str(path),
                        "RPT Pendidikan Seni Visual Tahun %d - 2027 (42 PdP)" % year)
                    checker = ns.get("_telegram_delivery_ok_v25279")
                    if callable(checker):
                        confirmed = bool(checker(result))
                    else:
                        confirmed = bool(getattr(result, "ok", False)
                                         and result.json().get("ok") is True)
                    if not confirmed:
                        return send(cid, "Telegram belum mengesahkan penghantaran PDF PSV.")
                    return result
            except Exception as exc:
                print("RPT PSV PDF delivery failed:", repr(exc), flush=True)
                return send(cid, "RPT PSV gagal dijana. Tiada PDF tahun lain digunakan.")
        suffix = data[len("rpt2027_en_pdf_"):]
        if suffix not in ("2", "3", "4", "5", "6"):
            return send(cid, "Pilihan tahun RPT tidak sah.")
        year = int(suffix)
        path = pdf_path(year)
        if not path.is_file():
            return send(cid,
                "⚠️ PDF RPT English Tahun %d belum tersedia pada pelayan. "
                "Tiada fail lain dihantar sebagai pengganti." % year)
        try:
            result = send_document(cid, str(path), "RPT English Tahun %d — 2027 (PDF)" % year)
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
            print("ENGLISH RPT 2027 PDF delivery failed:", repr(exc), flush=True)
            return send(cid, "⚠️ Muat turun RPT gagal. Sila cuba lagi.")

    ns["callback"] = callback
    ns["CIKGULAJU_RPT_ENGLISH_2027_INSTALLED"] = True
    return True
