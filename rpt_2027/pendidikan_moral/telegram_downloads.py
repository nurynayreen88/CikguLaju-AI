"""Paid Telegram delivery: provisional 2027 Pendidikan Moral year 2-6 RPT.

Build compact landscape PDFs from the versioned CSV at request time.
Never touches user/master DB, payment entitlements or another subject's PDF.
Not an approved official KPM calendar.
"""
from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
PREFIX = "rpt2027_pm_pdf_"


def source_rows(year):
    if type(year) is not int or year not in YEARS:
        return []
    path = ROOT / ("year%d_sequence_DRAF.csv" % year)
    try:
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != 42:
            return []
        if [str(x["Lesson"]) for x in rows] != ["%03d" % x for x in range(1, 43)]:
            return []
        if any(row["Status"] != "DRAF_SEMAK" or not row.get("SP") for row in rows):
            return []
        return rows
    except (OSError, KeyError, ValueError, csv.Error):
        return []


def pdf_ready(year, ns=None):
    """The source exists and can be rendered; exact 2027 dates remain teacher-adjustable."""
    try:
        from reportlab.pdfgen import canvas  # noqa: F401
    except ImportError:
        return False
    return bool(source_rows(year))


def _ascii(text):
    """PDF builtin Helvetica supports Latin-1; strip characters it cannot render."""
    return (str(text or "").replace("\u2014", "-").replace("\u2013", "-")
            .replace("\u2019", "'").replace("\u2018", "'")
            .replace("\u2022", "-").replace("\u00a0", " "))


def _wrap(text, width, font_name="Helvetica", font_size=8, max_lines=2):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = _ascii(text).split()
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if current and stringWidth(trial, font_name, font_size) > width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines[:max_lines]


def build_pdf(year, destination):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen.canvas import Canvas

    rows = source_rows(year)
    if not rows:
        raise ValueError("No valid Moral RPT 2027 source CSV for year")
    destination = Path(destination)
    page_w, page_h = landscape(A4)
    c = Canvas(str(destination), pagesize=(page_w, page_h))
    c.setTitle("RPT Pendidikan Moral Tahun %d - Cadangan 2027" % year)
    c.setAuthor("CikguLaju AI")
    left, right = 32, page_w - 32
    row_h, rows_per_page = 55, 7
    page_total = (len(rows) + rows_per_page - 1) // rows_per_page
    for page in range(page_total):
        c.setFillColor(colors.HexColor("#183047"))
        c.rect(0, page_h - 99, page_w, 99, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 17)
        c.drawString(left, page_h - 35, "RPT PENDIDIKAN MORAL TAHUN %d - 2027" % year)
        c.setFont("Helvetica", 9)
        c.drawString(left, page_h - 55,
                     "CADANGAN GURU | 42 PdP teras dipetakan DSKP | BUKAN RPT rasmi/akhir")
        c.drawString(left, page_h - 71,
                     "Kumpulan A/B: selaraskan tarikh, cuti negeri dan jadual PdP sekolah")
        c.drawString(left, page_h - 85,
                     "Liputan tambahan/PBD tahunan belum diperincikan dalam dokumen ini")
        c.setFillColor(colors.HexColor("#E8EEF1"))
        c.rect(left, page_h - 133, right - left, 25, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#183047"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(left + 5, page_h - 125, "PdP")
        c.drawString(left + 44, page_h - 125, "UNIT / TAJUK")
        c.drawString(left + 225, page_h - 125, "SK / SP")
        c.drawString(left + 322, page_h - 125, "AKTIVITI / EVIDENS PBD")
        for idx, row in enumerate(rows[page * rows_per_page:(page + 1) * rows_per_page]):
            top = page_h - 138 - idx * row_h
            c.setFillColor(colors.white if idx % 2 else colors.HexColor("#F6F9FA"))
            c.rect(left, top - row_h + 1, right - left, row_h, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#182C3E"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(left + 5, top - 17, _ascii(row["Lesson"]))
            c.setFont("Helvetica", 8)
            unit = "%s. %s" % (row["Unit"], row["Tajuk Unit"])
            for li, line in enumerate(_wrap(unit, 171, font_size=8, max_lines=2)):
                c.drawString(left + 44, top - 16 - li * 11, line)
            c.drawString(left + 225, top - 16, "SK " + _ascii(row["SK"]))
            for li, line in enumerate(_wrap("SP " + row["SP"], 90, font_size=8)):
                c.drawString(left + 225, top - 28 - li * 11, line)
            for li, line in enumerate(_wrap(row["Aktiviti"], 430, font_size=8, max_lines=2)):
                c.drawString(left + 322, top - 15 - li * 11, line)
            for li, line in enumerate(_wrap("PBD: " + row["Evidens PBD"], 430, font_size=7, max_lines=1)):
                c.setFont("Helvetica", 7)
                c.drawString(left + 322, top - 41 - li * 11, line)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#526472"))
        c.drawString(left, 19, "Sumber: DSKP SK / RPH CikguLaju. Rujukan halaman buku: permulaan unit sahaja.")
        c.drawRightString(right, 19, "%d / %d" % (page + 1, page_total))
        c.showPage()
    c.save()
    if destination.stat().st_size < 2500:
        raise ValueError("Generated Moral RPT PDF is unexpectedly small")
    return destination


def install(ns):
    if ns.get("CIKGULAJU_RPT_MORAL_2027_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(k)) for k in required):
        return False
    previous = ns["callback"]
    send = ns["send"]

    def callback(cid, data):
        d = str(data or "")
        if not d.startswith(PREFIX):
            return previous(cid, data)
        try:
            allowed = bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
            allowed = False
        if not allowed:
            return send(cid, "RPT 2027 hanya untuk Rakan Pembangun dan pelanggan aktif.",
                        [[{"text": "Jadi Rakan Pembangun", "callback_data": "pioneer_join"}],
                         [{"text": "Menu Utama", "callback_data": "home"}]])
        raw = d[len(PREFIX):]
        if raw not in ("2", "3", "4", "5", "6") or not pdf_ready(int(raw)):
            return send(cid, "RPT Pendidikan Moral untuk pilihan ini belum tersedia.")
        year = int(raw)
        try:
            with TemporaryDirectory(prefix="cikgulaju_pm_rpt_") as temp:
                path = build_pdf(
                    year, Path(temp) / ("RPT_Pendidikan_Moral_Tahun_%d_2027_CADANGAN.pdf" % year))
                result = ns["send_document"](
                    cid, str(path), "RPT Pendidikan Moral Tahun %d - 2027 (CADANGAN, semak tarikh)" % year)
                verify = ns.get("_telegram_delivery_ok_v25279")
                if callable(verify):
                    ok = bool(verify(result))
                else:
                    ok = bool(getattr(result, "ok", False) and result.json().get("ok") is True)
                if not ok:
                    return send(cid, "Telegram belum mengesahkan penghantaran RPT Moral. Cuba lagi.")
                return result
        except Exception as exc:
            print("Moral 2027 RPT delivery:", repr(exc), flush=True)
            return send(cid, "Gagal menyediakan PDF RPT Pendidikan Moral. Tiada dokumen lain digunakan.")

    ns["callback"] = callback
    ns["CIKGULAJU_RPT_MORAL_2027_INSTALLED"] = True
    return True
