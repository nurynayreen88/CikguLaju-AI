"""Read-only, paid-gated Moral 2027 RPT 96-session and supplemental RPH downloads.

Preserves the existing 42-core Moral RPH route, master DB, payments and
all other subject callbacks. Class dates remain dependent on teacher timetable.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from tempfile import TemporaryDirectory

BASE = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parent
YEARS = frozenset(range(2, 7))
RPT_PREFIX = "rpt2027_pm_96_"
RPH_PDF_PREFIX = "rpt2027_pm_rph54_pdf_"
RPH_DOCX_PREFIX = "rpt2027_pm_rph54_docx_"
PHASE_NAMES = ("Set induksi", "Aktiviti 1", "Aktiviti 2",
               "Pengukuhan/Pentaksiran PBD", "Penutup")


def _accepted_year(year):
    return type(year) is int and year in YEARS


def source_rows(year, group):
    """Validate all 96 rows and their associated source-file paths."""
    if not _accepted_year(year) or group not in ("A", "B"):
        return []
    path = ROOT / ("year%d_sequence_96_2027_group%s_STAGING.csv" % (year, group))
    try:
        with path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        if len(rows) != 96 or [r["Sesi"] for r in rows] != [
                "%03d" % i for i in range(1, 97)]:
            return []
        if [r["Modul"] for r in rows].count("TERAS") != 42:
            return []
        if [r["Modul"] for r in rows].count("PENGUKUHAN") != 54:
            return []
        for r in rows:
            candidate = Path(r["Rujukan_RPH"])
            resolved = (BASE / candidate).resolve()
            if not resolved.is_relative_to(BASE.resolve()) or not resolved.is_file():
                return []
            if r["Kumpulan"] != group or r["Tahun"] != str(year):
                return []
            if not (r["Minggu_RPT"].startswith("M")
                    and 1 <= int(r["Minggu_RPT"][1:]) <= 44):
                return []
        return rows
    except (OSError, ValueError, KeyError, csv.Error):
        return []


def pdf_ready(year, group):
    try:
        from reportlab.pdfgen import canvas  # noqa
    except ImportError:
        return False
    return bool(source_rows(year, group))


def rph_ready(year):
    """Ready for rendering source, not a claim of full textbook visual QA."""
    return bool(source_rows(year, "A"))


def _latin(s):
    """Safely map unsupported punctuation for reportlab's built-in Latin fonts."""
    return (str(s or "").replace("—", "-").replace("–", "-")
            .replace("’", "'").replace("“", '"').replace("”", '"')
            .replace("•", "-").encode("latin-1", errors="replace")
            .decode("latin-1"))


def _lines(value, width, font="Helvetica", size=8.0, max_lines=4):
    from reportlab.pdfbase.pdfmetrics import stringWidth
    words = _latin(value).replace("\n", " ").split()
    out, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if current and stringWidth(candidate, font, size) > width:
            out.append(current)
            current = word
        else:
            current = candidate
    if current:
        out.append(current)
    if len(out) > max_lines:
        out = out[:max_lines]
        last = out[-1]
        while last and stringWidth(last + "...", font, size) > width:
            last = last[:-1]
        out[-1] = last.rstrip() + "..."
    return out


def _draw_lines(c, text, x, top, width, size=8, max_lines=4, line_height=10):
    lines = _lines(text, width, size=size, max_lines=max_lines)
    c.setFont("Helvetica", size)
    for n, line in enumerate(lines):
        c.drawString(x, top - n * line_height, line)
    return top - len(lines) * line_height


def build_rpt_pdf(year, group, destination):
    """RPT: each session receives its own row, grouped by source M01-M44."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen.canvas import Canvas

    rows = source_rows(year, group)
    if not rows:
        raise ValueError("Unavailable/incomplete Moral 96-session source")
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    w, h = landscape(A4)
    c = Canvas(str(dest), pagesize=(w, h))
    c.setTitle("RPT Pendidikan Moral Tahun %d 2027 Kumpulan %s" % (year, group))
    c.setAuthor("CikguLaju AI")
    left, right = 30, w - 30
    per_page, row_h = 7, 54
    total = (len(rows) + per_page - 1) // per_page
    for page in range(total):
        c.setFillColor(colors.HexColor("#183047"))
        c.rect(0, h - 90, w, 90, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(left, h - 32,
                     "RPT PENDIDIKAN MORAL TAHUN %d - 2027" % year)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left, h - 51, "KUMPULAN %s | 96 SESI | 44 MINGGU RPT" % group)
        c.setFont("Helvetica", 8.2)
        c.drawString(left, h - 67,
                     "42 PdP teras + 54 pengukuhan | 60 minit/sesi (agihan cadangan)")
        c.drawString(left, h - 81,
                     "Tarikh di bawah ialah julat minggu; tarikh kelas sebenar ikut jadual guru dan cuti negeri.")
        c.setFillColor(colors.HexColor("#E8EDF1"))
        c.rect(left, h - 127, right - left, 24, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#183047"))
        c.setFont("Helvetica-Bold", 8)
        for x, title in [(left + 5, "SESI"), (left + 49, "MINGGU / TARIKH"),
                         (left + 201, "UNIT / TAJUK"),
                         (left + 379, "SK / SP"), (left + 488, "FOKUS / PBD")]:
            c.drawString(x, h - 119, title)
        for i, r in enumerate(rows[page*per_page:(page+1)*per_page]):
            top = h - 132 - i*row_h
            c.setFillColor(colors.HexColor("#F4F7F9") if i % 2 == 0 else colors.white)
            c.rect(left, top-row_h+1, right-left, row_h, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#182C3E"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(left+5, top-16, _latin(r["Sesi"]))
            c.setFont("Helvetica", 7.2)
            c.drawString(left+5, top-31, "Teras" if r["Modul"] == "TERAS" else "Kukuh")
            c.setFont("Helvetica-Bold", 7.7)
            c.drawString(left+49, top-15, _latin(r["Minggu_RPT"]))
            _draw_lines(c, r["Tarikh_Minggu_Mula"] + " - " + r["Tarikh_Minggu_Tamat"],
                        left+49, top-28, 146, size=7.0, max_lines=2, line_height=9)
            _draw_lines(c, r["Unit"] + ". " + r["Tajuk_Unit"],
                        left+201, top-15, 168, size=7.4, max_lines=3, line_height=10)
            c.setFont("Helvetica-Bold", 7.6)
            c.drawString(left+379, top-15, _latin("SK " + r["SK"]))
            _draw_lines(c, "SP " + r["SP"], left+379, top-27, 102,
                        size=7.0, max_lines=2, line_height=10)
            _draw_lines(c, r["Fokus"], left+488, top-15, 285,
                        size=7.5, max_lines=2, line_height=10)
            _draw_lines(c, "PBD: " + r["Evidens_PBD"], left+488, top-38,
                        285, size=6.9, max_lines=2, line_height=9)
        c.setFillColor(colors.HexColor("#526472"))
        c.setFont("Helvetica", 7.6)
        c.drawString(left, 24, "Sumber: DSKP SK, RPH CikguLaju, induk minggu 2027 A/B.")
        c.drawRightString(right, 24, "%d / %d" % (page+1, total))
        c.showPage()
    c.save()
    if dest.stat().st_size < 4000:
        raise ValueError("RPT PDF too small")
    return dest


def _field(raw, key):
    match = re.search(r"^\*\*" + re.escape(key) + r":\*\*\s*(.*)$", raw, re.M)
    return match.group(1).strip() if match else ""


def _source_components(raw):
    components = {}
    for key in PHASE_NAMES:
        pattern = r"^\*\*" + re.escape(key) + r"[^\n]*?\*\*\s*(.+)$"
        m = re.search(pattern, raw, re.M | re.I)
        components[key] = m.group(1).strip() if m else ""
    m = re.search(r"(?s)^## Objektif dan kriteria kejayaan\s*\n(.+?)\n\*\*Kriteria kejayaan:", raw, re.M)
    components["Objektif"] = m.group(1).strip() if m else ""
    return components


def _supplement(year):
    rows = source_rows(year, "A")
    if not rows:
        raise ValueError("Unverified/incomplete supplementary lesson set")
    for r in rows:
        if r["Modul"] != "PENGUKUHAN":
            continue
        path = BASE / r["Rujukan_RPH"]
        raw = path.read_text(encoding="utf-8")
        sections = _source_components(raw)
        if any(not sections.get(k) for k in (*PHASE_NAMES, "Objektif")):
            raise ValueError("Missing RPH phase in " + str(path))
        if any(not _field(raw, k) for k in ("Unit", "Nilai", "SK", "SP")) or not (_field(raw, "BBM") or _field(raw, "Bahan")):
            raise ValueError("Missing RPH metadata in " + str(path))
        yield r, raw, sections


def build_rph_pdf(year, destination):
    """Generate 54 independent teacher-view RPH pages, no internal QA labels."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas

    if not _accepted_year(year):
        raise ValueError("Unsupported Moral year")
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    w, h = A4
    c = Canvas(str(dest), pagesize=(w, h))
    c.setTitle("RPH Pengukuhan Pendidikan Moral Tahun %d 2027" % year)
    count = 0
    for row, raw, sec in _supplement(year):
        count += 1
        c.setFillColor(colors.HexColor("#183047"))
        c.rect(0, h-70, w, 70, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(34, h-28, "RPH PENDIDIKAN MORAL TAHUN %d" % year)
        c.setFont("Helvetica", 9)
        c.drawString(34, h-48,
                     "Sesi %s / 096 | Pengukuhan | 60 minit" % row["Sesi"])
        c.setFillColor(colors.HexColor("#203448"))
        y = h - 91
        def item(title, value, line_max=4, size=8.5):
            nonlocal y
            c.setFont("Helvetica-Bold", 8.8)
            c.drawString(35, y, _latin(title))
            y -= 13
            y = _draw_lines(c, value, 35, y, w-70, size=size,
                            max_lines=line_max, line_height=10.5)
            y -= 8
        item("Unit / nilai", _field(raw, "Unit") + " | " + _field(raw, "Nilai"), 3)
        item("Standard kandungan / pembelajaran",
             "SK " + _field(raw, "SK") + "; SP " + _field(raw, "SP"), 4, 7.9)
        item("Objektif pembelajaran", sec["Objektif"], 4, 8.3)
        item("Bahan bantu mengajar", _field(raw, "BBM") or _field(raw, "Bahan"), 3, 7.7)
        for label, mins in zip(PHASE_NAMES, (5,20,20,10,5)):
            item(label + " (%d min)" % mins, sec[label], 6, 8.0)
        if y < 31:
            raise ValueError("RPH A4 overflow for year %s session %s (y=%s)" %
                             (year, row["Sesi"], y))
        c.setStrokeColor(colors.HexColor("#CED9DF"))
        c.line(35, 31, w-35, 31)
        c.setFont("Helvetica", 7.1)
        c.setFillColor(colors.HexColor("#526472"))
        c.drawString(35, 20, "RPH CikguLaju | PdP: guru boleh menyesuaikan langkah mengikut kelas")
        c.drawRightString(w-35, 20, "%s / 54" % count)
        c.showPage()
    c.save()
    if count != 54 or dest.stat().st_size < 4000:
        raise ValueError("Incomplete supplementary RPH PDF")
    return dest


def build_rph_docx(year, destination):
    """Editable multi-page Word pack, one carefully compact session per section."""
    from docx import Document
    from docx.shared import Cm, Pt
    from docx.enum.text import WD_BREAK

    if not _accepted_year(year):
        raise ValueError("Unsupported Moral year")
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.page_height, section.page_width = Cm(29.7), Cm(21)
    section.top_margin, section.bottom_margin = Cm(1.3), Cm(1.3)
    section.left_margin, section.right_margin = Cm(1.5), Cm(1.5)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(8.5)
    normal.paragraph_format.space_after = Pt(2)
    count = 0
    def line(label, value, bold=True):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        if bold:
            p.add_run(label + ": ").bold = True
        else:
            p.add_run(label)
        p.add_run(value)
    for row, raw, sec in _supplement(year):
        if count:
            doc.add_page_break()
        count += 1
        h = doc.add_paragraph()
        h.style = "Heading 1"
        h.paragraph_format.space_after = Pt(4)
        h.add_run("RPH PENDIDIKAN MORAL TAHUN %d — SESI %s" % (year, row["Sesi"]))
        line("Tempoh", "60 minit • Pengukuhan")
        line("Unit/Nilai", _field(raw, "Unit") + " | " + _field(raw, "Nilai"))
        line("SK/SP", _field(raw, "SK") + " | " + _field(raw, "SP"))
        line("Objektif", sec["Objektif"])
        line("BBM", _field(raw, "BBM") or _field(raw, "Bahan"))
        for name, mins in zip(PHASE_NAMES, (5,20,20,10,5)):
            line("%s (%d minit)" % (name, mins), sec[name])
        line("Refleksi guru", "Bilangan mencapai objektif: ____ / ____; tindakan susulan: __________")
    if count != 54:
        raise ValueError("Incomplete supplementary Word pack")
    doc.save(str(dest))
    if dest.stat().st_size < 10000:
        raise ValueError("Word pack too small")
    return dest


def install(ns):
    """Wrap only new Moral actions and retain old callbacks and entitlements."""
    if ns.get("CIKGULAJU_MORAL_96_DOWNLOADS_INSTALLED"):
        return True
    required = ("callback", "send", "send_document", "_access_info", "_is_admin")
    if any(not callable(ns.get(name)) for name in required):
        return False
    previous = ns["callback"]
    send = ns["send"]
    def callback(cid, data):
        action = str(data or "")
        kind, group, raw_year = None, None, None
        if action.startswith(RPT_PREFIX):
            suffix = action[len(RPT_PREFIX):].split("_")
            if len(suffix) != 2:
                return send(cid, "Pilihan RPT Pendidikan Moral tidak sah.")
            group, raw_year = suffix[0].upper(), suffix[1]
            kind = "rpt"
        elif action.startswith(RPH_PDF_PREFIX):
            raw_year = action[len(RPH_PDF_PREFIX):]
            kind = "rph_pdf"
        elif action.startswith(RPH_DOCX_PREFIX):
            raw_year = action[len(RPH_DOCX_PREFIX):]
            kind = "rph_docx"
        else:
            return previous(cid, data)
        if raw_year not in ("2","3","4","5","6") or (
                kind == "rpt" and group not in ("A","B")):
            return send(cid, "Pilihan tahun atau kumpulan tidak sah.")
        try:
            allowed = bool(ns["_is_admin"](cid) or ns["_access_info"](cid).get("active"))
        except Exception:
            allowed = False
        if not allowed:
            return send(cid, "RPT dan pakej RPH pengukuhan hanya untuk Rakan Pembangun dan pelanggan aktif.",
                        [[{"text":"Jadi Rakan Pembangun","callback_data":"pioneer_join"}],
                         [{"text":"Menu Utama","callback_data":"home"}]])
        year = int(raw_year)
        if (kind == "rpt" and not pdf_ready(year, group)) or (
                kind != "rpt" and not rph_ready(year)):
            return send(cid, "Sumber Pendidikan Moral bagi pilihan ini belum lengkap.")
        try:
            with TemporaryDirectory(prefix="cikgulaju_moral96_") as tmp:
                folder = Path(tmp)
                if kind == "rpt":
                    fname = "RPT_Pendidikan_Moral_Tahun_%d_2027_Kumpulan_%s.pdf" % (year,group)
                    path = build_rpt_pdf(year, group, folder/fname)
                    caption = "RPT Pendidikan Moral Tahun %d - 2027 Kumpulan %s (96 Sesi)" % (year,group)
                elif kind == "rph_pdf":
                    path = build_rph_pdf(year, folder/("RPH_Pengukuhan_Moral_Tahun_%d.pdf" % year))
                    caption = "RPH Pengukuhan Pendidikan Moral Tahun %d - 54 Sesi (PDF)" % year
                else:
                    path = build_rph_docx(year, folder/("RPH_Pengukuhan_Moral_Tahun_%d.docx" % year))
                    caption = "RPH Pengukuhan Pendidikan Moral Tahun %d - 54 Sesi (Word)" % year
                result = ns["send_document"](cid, str(path), caption)
                verify = ns.get("_telegram_delivery_ok_v25279")
                if callable(verify):
                    ok = bool(verify(result))
                else:
                    ok = bool(getattr(result, "ok", False) and result.json().get("ok") is True)
                if not ok:
                    return send(cid, "Telegram belum mengesahkan penghantaran bahan. Cuba lagi.")
                return result
        except Exception as exc:
            print("Moral 96 download failed:", repr(exc), flush=True)
            return send(cid, "Bahan Pendidikan Moral belum berjaya dijana. Tiada fail lain digunakan.")
    ns["callback"] = callback
    ns["CIKGULAJU_MORAL_96_DOWNLOADS_INSTALLED"] = True
    return True
