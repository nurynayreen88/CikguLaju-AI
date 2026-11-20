"""Read-only Telegram delivery of English 2027 RPT PDFs.

This is installed after app.py's existing callback wrappers by the active WSGI
entrypoint. It never alters RPH credit accounting, subscriptions or the DB.
"""
from pathlib import Path
from primary_language_subjects import PRIMARY_LANGUAGE_SUBJECTS
from tempfile import TemporaryDirectory
import os
from rpt_2027.dlp.documents import PUBLISHED_YEARS, SUBJECTS as DLP_SUBJECTS, document_path
from rpt_2027.sains import tahun5_documents as sains_sk_tahun5, tahun6_documents as sains_sk_tahun6
from rpt_2027.bahasa_arab import documents as bahasa_arab
from rpt_2027.sjkc.bahasa_cina import documents as bahasa_cina_sjkc
from rpt_2027.sjkc.bahasa_melayu import documents as bahasa_melayu_sjk
from rpt_2027.sjkc.sains import documents as sains_sjkc
from rpt_2027.sjkc.matematik import documents as matematik_sjkc
from rpt_2027.sjkt.matematik import documents as matematik_sjkt
from rpt_2027.psv.telegram_downloads import pdf_ready as psv_pdf_ready, build_pdf as build_psv_pdf
from rpt_2027.matematik.telegram_downloads import pdf_ready as math_pdf_ready
from rpt_2027.matematik.sk_documents import DIGESTS as math_sk_editions, DPK_DIGESTS as math_dpk_editions
from rpt_2027.bahasa_melayu.telegram_downloads import pdf_ready as bm_pdf_ready
from rpt_2027.pendidikan_islam.telegram_downloads import pdf_ready as pi_pdf_ready
from rpt_2027.pjpk.telegram_downloads import pdf_ready as pjpk_pdf_ready
from rpt_2027.pendidikan_moral.telegram_downloads import pdf_ready as moral_pdf_ready
from rpt_2027.pendidikan_moral.complete_96_downloads import combined_pdf_ready as moral_combined_pdf_ready

PDF_ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
SCHOOL_RPT_CALLBACKS = {
    "rpt2027_bahasa_arab": bahasa_arab,
    "rpt2027_sjkc": bahasa_cina_sjkc,
    "rpt2027_bm_sjk": bahasa_melayu_sjk,
    "rpt2027_sains_sjkc": sains_sjkc,
    "rpt2027_sains_sk5": sains_sk_tahun5,
    "rpt2027_sains_sk6": sains_sk_tahun6,
    "rpt2027_matematik_sjkc": matematik_sjkc,
    "rpt2027_matematik_sjkt": matematik_sjkt,
}


def pdf_path(year):
    if type(year) is not int or year not in YEARS:
        raise ValueError("Unsupported RPT English year")
    if os.environ.get("CIKGULAJU_ENGLISH_2027_INTEGRATED_RPH_ENABLED") == "1":
        return PDF_ROOT / f"RPT_English_SK_2027_Year_{year}_A_B.pdf"
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

    published_year_tokens = tuple(map(str, PUBLISHED_YEARS))

    def callback(cid, d):
        data = str(d or "")
        is_year = data.startswith("rpt2027_year_")
        is_download = data.startswith("rpt2027_en_pdf_")
        is_psv = data.startswith("rpt2027_psv_pdf_")
        is_dlp = data.startswith("rpt2027_dlp:")
        is_language = data.startswith("rpt2027_language:")
        is_ppki = data.startswith("rpt2027_ppki_")
        callback_key, separator, payload = data.partition(":")
        school_subject = SCHOOL_RPT_CALLBACKS.get(callback_key) if separator else None
        if data != "rpt2027_home" and not is_year and not is_download and not is_psv and not is_dlp and not is_language and not is_ppki and school_subject is None:
            return previous(cid, d)
        # Enforce entitlement again for stale/forged buttons and downloads.
        if not allowed(cid):
            return locked(cid)
        if is_ppki:
            from staging.ppki.catalog import RPT_COMBINED_FILENAME, UNIT_LESSONS
            from staging.ppki.rpt import render_rpt
            count = sum(len(numbers) for numbers in UNIT_LESSONS.values())
            edition = f"Unit 2–{len(UNIT_LESSONS) + 1}"

            if data == "rpt2027_ppki_home":
                return send(cid, "📅 <b>RPT 2027 · Pendidikan Khas (PPKI)</b>\n\nPilih tahun.", [
                    [{"text": "Tahun 2", "callback_data": "rpt2027_ppki_year2"}],
                    [{"text": "⬅️ Kembali", "callback_data": "rpt2027_home"}],
                ])
            if data == "rpt2027_ppki_year2":
                return send(cid, f"<b>PPKI Tahun 2</b>\n\nAgihan {count} PdP bagi {edition}.", [
                    [{"text": "Pengurusan Kehidupan (PDF)", "callback_data": "rpt2027_ppki_pdf2"}],
                    [{"text": "⬅️ Kembali", "callback_data": "rpt2027_ppki_home"}],
                ])
            if data != "rpt2027_ppki_pdf2":
                return send(cid, "Pilihan RPT PPKI tidak sah.")
            try:
                with TemporaryDirectory(prefix="cikgulaju-rpt-ppki-") as folder:
                    path = Path(folder) / RPT_COMBINED_FILENAME
                    path.write_bytes(render_rpt(combined=True))
                    result = send_document(cid, str(path), f"RPT 2027 PPKI · Pengurusan Kehidupan Tahun 2 · {edition}")
                verify = ns.get("_telegram_delivery_ok_v25279")
                if callable(verify) and not verify(result):
                    return send(cid, "Telegram belum mengesahkan penghantaran RPT PPKI.")
                return result
            except Exception as exc:
                print("PPKI RPT delivery failed:", type(exc).__name__, flush=True)
                return send(cid, "Muat turun RPT PPKI gagal. Cuba lagi.")
        if school_subject is not None:
            year, _, fmt = payload.partition(":")
            label = school_subject.LABEL
            if year not in tuple(map(str, school_subject.YEARS)) or fmt not in school_subject.FORMATS:
                return send(cid, f"Pilihan RPT {label} tidak sah.")
            path = school_subject.document_path(int(year), fmt)
            if path is None:
                return send(cid, f"Fail RPT {label} belum tersedia.")
            try:
                result = send_document(
                    cid, str(path), f"RPT 2027 · {label} · Tahun {year} · {school_subject.FORMATS[fmt]}",
                )
                verify = ns.get("_telegram_delivery_ok_v25279")
                confirmed = verify(result) if callable(verify) else (
                    getattr(result, "ok", False) and result.json().get("ok") is True
                )
                if not confirmed:
                    return send(cid, f"Telegram belum mengesahkan penghantaran RPT {label}.")
                return result
            except Exception as exc:
                print("RPT delivery failed:", label, type(exc).__name__, flush=True)
                return send(cid, f"Muat turun RPT {label} gagal. Cuba lagi.")
        if is_language:
            code, _, year = data.removeprefix("rpt2027_language:").partition(":")
            label = PRIMARY_LANGUAGE_SUBJECTS.get(code)
            if label is None or year not in ("2", "3", "4", "5", "6"):
                return send(cid, "Pilihan RPT tidak sah.")
            return send(cid, f"<b>{label} · Tahun {year}</b>\n\nRPT 2027 dalam penyediaan.",
                        [[{"text": "⬅️ Pilih Subjek", "callback_data": f"rpt2027_year_{year}"}]])
        if is_dlp:
            parts = data.split(":")
            if len(parts) == 3:
                # Year 2 buttons sent before the multi-year menu remain valid.
                _, subject, fmt = parts
                year = 2
            elif len(parts) == 4 and parts[2] in published_year_tokens:
                _, subject, year_text, fmt = parts
                year = int(year_text)
            else:
                return send(cid, "Pilihan RPT DLP tidak sah.")
            path = document_path(subject, year, fmt)
            if path is None:
                return send(cid, "Fail RPT DLP ini belum tersedia.")
            try:
                result = send_document(cid, str(path), f"RPT 2027 · {DLP_SUBJECTS[subject]} (DLP) · Year {year}")
                verify = ns.get("_telegram_delivery_ok_v25279")
                if callable(verify) and not verify(result):
                    return send(cid, "Telegram belum mengesahkan penghantaran RPT DLP. Cuba lagi.")
                return result
            except Exception as exc:
                print("DLP RPT delivery failed:", type(exc).__name__, flush=True)
                return send(cid, "Muat turun RPT DLP gagal. Cuba lagi.")
        if data == "rpt2027_home":
            kb = [[{"text": "Tahun %s" % year,
                    "callback_data": "rpt2027_year_%s" % year}]
                  for year in range(1, 7)]
            kb.append([{"text": "Pendidikan Khas (PPKI)", "callback_data": "rpt2027_ppki_home"}])
            kb.append([{"text": "🏠 Menu Utama", "callback_data": "home"}])
            return send(cid,
                "📅 <b>RPT 2027</b>\n\n"
                "English Tahun 2–6 tersedia dalam PDF (160 Lesson/tahun). Bahasa Melayu: RPT DRAF untuk semakan, jika tersedia. Pendidikan Islam: RPT cadangan, jika tersedia. "
                "Matematik SK Tahun 5–6: 117 Lesson dan 96 jam bagi setiap tahun. PJPK Tahun 2–6: RPT DRAF (jika tersedia). Pendidikan Moral: satu PDF RPT merangkumi Kumpulan A/B (96 sesi/tahun). PSV: 42 PdP cadangan bagi Tahun 2–6.",
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
            math_label = ("Matematik SK (PDF • Kumpulan A/B)" if year in math_sk_editions or year in math_dpk_editions
                          else "Matematik (PDF v28 • DRAF/SEMENTARA)")
            if math_pdf_ready(year, ns=ns):
                kb.append([{"text": f"📥 {math_label}",
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
                kb.append([{"text": "📘 Pendidikan Moral • RPH mengikut RPT",
                            "callback_data": "moral_supp_menu_%d" % year}])
            if psv_pdf_ready(year):
                kb.append([{"text": "📥 Pendidikan Seni Visual (PDF)",
                            "callback_data": "rpt2027_psv_pdf_%d" % year}])
            for code, name in DLP_SUBJECTS.items():
                buttons = [
                    {"text": f"{name} DLP ({label})", "callback_data": f"rpt2027_dlp:{code}:{year}:{fmt}"}
                    for fmt, label in (("pdf", "PDF"), ("docx", "Word"))
                    if document_path(code, year, fmt)
                ]
                if buttons:
                    kb.append(buttons)
            for key, school_subject in SCHOOL_RPT_CALLBACKS.items():
                buttons = [
                    {"text": f"{school_subject.LABEL} ({label})", "callback_data": f"{key}:{year}:{fmt}"}
                    for fmt, label in school_subject.FORMATS.items()
                    if school_subject.document_path(year, fmt)
                ]
                if buttons:
                    kb.append(buttons)
            kb.extend(
                [{"text": f"{label} — Dalam Penyediaan",
                  "callback_data": f"rpt2027_language:{code}:{year}"}]
                for code, label in PRIMARY_LANGUAGE_SUBJECTS.items()
            )
            kb.extend([
                [{"text": "⬅️ Pilih Tahun", "callback_data": "rpt2027_home"}],
                [{"text": "🏠 Menu Utama", "callback_data": "home"}],
            ])
            return send(cid,
                "📅 <b>RPT 2027 — Tahun %d</b>\n\n"
                "Pilih subjek untuk memuat turun RPT.\n"
                "English: 160 Lesson; Kumpulan A/B dalam satu PDF.\nBahasa Melayu: RPT 2027 DRAF untuk semakan guru, jika tersedia.\n"
                f"{math_label}, jika fail tersedia.\nPendidikan Islam: cadangan untuk semakan guru, jika fail tersedia.\nPJPK: RPT cadangan PdP 2027 (DRAF), jika tersedia.\nPendidikan Moral: RPT PDF Kumpulan A dan B dan RPH Word/PDF bagi setiap PdP (96 sesi).\n\n"
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
            result = send_document(cid, str(path), "RPT English Year %d — 2027 (PDF)" % year)
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
