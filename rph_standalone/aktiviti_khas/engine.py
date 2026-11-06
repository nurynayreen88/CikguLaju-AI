"""CikguLaju RPH Aktiviti Khas: immutable 59-entry catalogue and shared renderer.

No runtime AI, curriculum DB access, fabricated SK/SP, quota updates or network.
The same module is called in the Telegram deployment for Web-proxied downloads.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "catalog_v1.json"
TRANSISI = "TRANSISI_TAHUN_1"
SELEPAS = "SELEPAS_TAMAT_SUKATAN"
STATUS = "DRAFT_REVIEW"
STEPS = (("Set Induksi", 5), ("Aktiviti 1", 15), ("Aktiviti 2", 15),
         ("Aktiviti 3", 15), ("Pengukuhan / Penilaian", 5), ("Penutup", 5))
MIMES = {"word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         "pdf": "application/pdf"}


class SourceUnavailable(ValueError):
    pass


def _catalog(path=CATALOG):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 1000 <= path.stat().st_size <= 250000:
        raise SourceUnavailable("Activity source missing or unsafe")
    raw = path.read_bytes()
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise SourceUnavailable("Activity source corrupt") from exc
    rows = data.get("activities")
    if (data.get("schema_version") != "1.0" or data.get("release_status") != STATUS
            or not isinstance(rows, list) or len(rows) != 59):
        raise SourceUnavailable("Incomplete or unapproved activity source")
    ids, buckets = set(), {}
    for row in rows:
        if not isinstance(row, dict):
            raise SourceUnavailable("Invalid row")
        ident, kind, years = row.get("id"), row.get("category"), row.get("years")
        if (not isinstance(ident, str)
                or not re.fullmatch(r"(?:K(?:0[1-9]|1[0-9]|20)|S(?:0[1-9]|1[0-3])[ABC])", ident)
                or ident in ids):
            raise SourceUnavailable("Duplicate/invalid ID")
        ids.add(ident)
        if kind == TRANSISI:
            if years != [1] or row.get("phase") not in ("Fasa Penyesuaian", "Fasa Kesediaan"):
                raise SourceUnavailable("Invalid transition")
        elif kind == SELEPAS:
            if years not in ([1, 2], [3, 4], [5, 6]) or row.get("phase") is not None:
                raise SourceUnavailable("Invalid tier")
            if (not isinstance(row.get("subject_options"), list)
                    or len(row["subject_options"]) != 1
                    or not isinstance(row["subject_options"][0], str)
                    or not row["subject_options"][0].strip()):
                raise SourceUnavailable("Invalid subject options")
        else:
            raise SourceUnavailable("Unknown activity category")
        buckets[(kind, tuple(years))] = buckets.get((kind, tuple(years)), 0) + 1
        for key in ("title", "learning_objective", "set_induksi",
                    "pengukuhan_penilaian", "penutup", "bbm"):
            value = row.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > 1600:
                raise SourceUnavailable("Missing RPH field")
        steps = row.get("aktiviti_utama")
        if (not isinstance(steps, list) or len(steps) != 3
                or any(not isinstance(step, str) or len(step.strip()) < 185 or len(step) > 1600
                       for step in steps) or row.get("duration_minutes") != 60):
            raise SourceUnavailable("Invalid steps or duration")
        if any(key in row for key in ("sk", "sp", "lesson_number", "textbook_page")):
            raise SourceUnavailable("No invented curriculum references permitted")
    if buckets.get((TRANSISI, (1,))) != 20 or any(
            buckets.get((SELEPAS, years)) != 13 for years in
            ((1, 2), (3, 4), (5, 6))):
        raise SourceUnavailable("Missing year-group activity variants")
    return data, hashlib.sha256(raw).hexdigest()


def list_options(kind, year, *, phase=None, subject=None, path=CATALOG):
    if kind not in (TRANSISI, SELEPAS) or type(year) is not int or year not in range(1, 7):
        raise ValueError("Invalid category/year")
    if kind == TRANSISI and (year != 1 or phase not in
                            (None, "Fasa Penyesuaian", "Fasa Kesediaan")):
        raise ValueError("Transition restricted to Year 1")
    if kind == SELEPAS and phase is not None:
        raise ValueError("No phase for post-syllabus activity")
    if kind == TRANSISI and subject is not None:
        raise ValueError("Transition is not a school subject")
    if subject is not None and (not isinstance(subject, str) or not subject.strip() or len(subject) > 100):
        raise ValueError("Invalid subject filter")
    source, digest = _catalog(path)
    rows = (r for r in source["activities"] if r["category"] == kind
            and year in r["years"] and (phase is None or r["phase"] == phase)
            and (subject is None or subject in r.get("subject_options", [])))
    return [{"id": r["id"], "label": r["title"], "phase": r["phase"]}
            for r in rows], digest


def select(kind, year, activity_id, digest, *, path=CATALOG):
    if not isinstance(activity_id, str) or not isinstance(digest, str):
        raise ValueError("Missing activity identity")
    choices, authoritative_digest = list_options(kind, year, path=path)
    if not re.fullmatch(r"[a-f0-9]{64}", digest) or digest != authoritative_digest:
        raise SourceUnavailable("Web/Telegram activity source mismatch")
    if not any(choice["id"] == activity_id for choice in choices):
        raise SourceUnavailable("Activity/year not in source")
    source, _ = _catalog(path)
    return next(row for row in source["activities"] if row["id"] == activity_id)


def _teacher(fields):
    if not isinstance(fields, dict) or set(fields) != {"class", "date", "time", "students"}:
        raise ValueError("Invalid teacher metadata")
    cls, dt, tm, students = (fields[k] for k in ("class", "date", "time", "students"))
    if any(not isinstance(x, str) for x in (cls, dt, tm, students)):
        raise ValueError("Invalid metadata field type")
    if len(cls) > 40 or (cls and not re.fullmatch(r"[\w .\-/()]+", cls)):
        raise ValueError("Invalid class")
    if dt:
        if not re.fullmatch(r"20\d\d-\d\d-\d\d", dt):
            raise ValueError("Invalid date")
        actual = date.fromisoformat(dt)
        if actual.year not in range(2025, 2032):
            raise ValueError("Invalid date range")
        day = ("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad")[actual.weekday()]
        dt = actual.strftime("%d/%m/%Y")
    else:
        dt, day = "__________", "__________"
    if tm and (len(tm) > 12 or not re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d\s*-\s*(?:[01]\d|2[0-3]):[0-5]\d", tm)):
        raise ValueError("Invalid time range")
    if students and (not re.fullmatch(r"[1-9]\d{0,2}", students) or int(students) > 200):
        raise ValueError("Invalid pupil number")
    return {"class": cls or "________", "date": dt, "day": day,
            "time": tm or "________", "students": students or "_____"}


def fields_for(row, year, teacher, subject=None):
    if type(year) is not int or year not in row["years"]:
        raise ValueError("Wrong year for activity")
    if row["category"] == TRANSISI:
        if subject is not None:
            raise ValueError("No subject required for Transition")
        subject = "Program Transisi Tahun Satu"
    elif subject is None or subject not in row["subject_options"]:
        raise ValueError("Explicit matching subject is required for this activity")
    parts = [row["set_induksi"], *row["aktiviti_utama"],
             row["pengukuhan_penilaian"], row["penutup"]]
    return {
        "id": row["id"], "year": year, "title": row["title"], "subject": subject,
        "objective": row["learning_objective"], "bbm": row["bbm"],
        "assessment": row["pengukuhan_penilaian"], "meta": _teacher(teacher),
        "phases": [(label, minute, part) for (label, minute), part
                   in zip(STEPS, parts)]
    }


def render_word(fields):
    """Editable original CikguLaju RPH table; each numbered activity is its own row."""
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Mm(297), Mm(210)
    sec.top_margin = sec.bottom_margin = Mm(11)
    sec.left_margin = sec.right_margin = Mm(12)
    sec.footer_distance = Mm(5)
    style = doc.styles["Normal"]
    style.font.name, style.font.size = "Arial", Pt(8.1)
    style.paragraph_format.space_before = style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.line_spacing = 1

    def write(c, val, bold=False):
        c.text = ""
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1
        run = p.add_run(str(val))
        run.bold, run.font.size = bold, Pt(8.1)
        if bold:
            shd = OxmlElement("w:shd")
            shd.set(qn("w:fill"), "E8EBEF")
            c._tc.get_or_add_tcPr().append(shd)

    def table(rows, widths):
        t = doc.add_table(rows=0, cols=len(widths), style="Table Grid")
        t.alignment, t.autofit = WD_TABLE_ALIGNMENT.CENTER, False
        for row in rows:
            cells = t.add_row().cells
            for i, (val, bold) in enumerate(row):
                write(cells[i], val, bold)
        for row in t.rows:
            for c, w in zip(row.cells, widths):
                c.width = Mm(w)
                tc = c._tc.get_or_add_tcPr()
                mar = OxmlElement("w:tcMar")
                for side in ("top", "bottom", "left", "right"):
                    el = OxmlElement("w:" + side)
                    el.set(qn("w:w"), "30" if side in ("top", "bottom") else "55")
                    el.set(qn("w:type"), "dxa")
                    mar.append(el)
                tc.append(mar)
        return t

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("RANCANGAN PENGAJARAN HARIAN")
    r.bold, r.font.size = True, Pt(12.5)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("AKTIVITI KHAS - DRAF UNTUK SEMAKAN GURU")
    r.bold, r.font.size = True, Pt(8.5)

    m = fields["meta"]
    table([
        [("Tahun", True), ("Tahun " + str(fields["year"]), False),
         ("Kelas", True), (m["class"], False)],
        [("Tarikh", True), (m["date"], False), ("Hari", True), (m["day"], False)],
        [("Masa", True), (m["time"], False), ("Bil. Murid", True), (m["students"], False)],
        [("Bidang", True), (fields["subject"], False), ("Kod", True), (fields["id"], False)]
    ], (26, 65, 30, 65))
    table([[(k, True), (v, False)] for k, v in (
        ("Tajuk", fields["title"]), ("Objektif", fields["objective"]),
        ("BBM", fields["bbm"]), ("Pentaksiran", fields["assessment"]))], (43, 143))
    table([
        [("Fasa / Masa", True), ("Aktiviti Pengajaran dan Pembelajaran", True)],
        *[[(f"{title} ({minutes} minit)", True), (body, False)]
          for title, minutes, body in fields["phases"]]
    ], (43, 143))
    table([[("Refleksi", True),
            ("____ / ____ murid mencapai objektif. Tindakan susulan: ______________", False)]],
          (43, 143))
    foot = sec.footer.paragraphs[0]
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    foot.add_run("CikguLaju | DRAF - Aktiviti khas tanpa SK/SP rasmi").font.size = Pt(7)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def render_pdf(fields):
    """Fit exactly one A4 page or fail closed; never silently return two pages."""
    def safe(value):
        value = str(value).replace("—", "-").replace("–", "-").replace("’", "'")
        return escape(value)

    for font_size in (8.2, 7.8, 7.4, 7.0):
        buf = io.BytesIO()
        pdf = SimpleDocTemplate(buf, pagesize=A4, topMargin=10 * mm,
                                bottomMargin=10 * mm, leftMargin=12 * mm,
                                rightMargin=12 * mm,
                                title="CikguLaju RPH Aktiviti Khas - DRAF")
        body = ParagraphStyle("body", fontName="Helvetica", fontSize=font_size,
                              leading=font_size + 1.6)
        bold = ParagraphStyle("bold", parent=body, fontName="Helvetica-Bold")
        heading = ParagraphStyle("heading", parent=bold, fontSize=12.5, leading=15,
                                 alignment=1, spaceAfter=3)
        sub = ParagraphStyle("sub", parent=bold, fontSize=8.4, leading=10,
                             alignment=1, spaceAfter=5)
        plain = lambda v: Paragraph(safe(v), body)
        strong = lambda v: Paragraph(safe(v), bold)

        def grid(rows, widths):
            t = Table(rows, colWidths=[w * mm for w in widths], hAlign="LEFT")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), .5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            return t

        m = fields["meta"]
        meta = [
            [strong("Tahun"), plain("Tahun " + str(fields["year"])),
             strong("Kelas"), plain(m["class"])],
            [strong("Tarikh"), plain(m["date"]), strong("Hari"), plain(m["day"])],
            [strong("Masa"), plain(m["time"]), strong("Bil. Murid"), plain(m["students"])],
            [strong("Bidang"), plain(fields["subject"]), strong("Kod"), plain(fields["id"])]
        ]
        info = [[strong(k), plain(v)] for k, v in (
            ("Tajuk", fields["title"]), ("Objektif", fields["objective"]),
            ("BBM", fields["bbm"]), ("Pentaksiran", fields["assessment"]))]
        steps = [[strong("Fasa / Masa"), strong("Aktiviti Pengajaran dan Pembelajaran")]]
        steps += [[strong(f"{name} ({minutes} minit)"), plain(text)]
                  for name, minutes, text in fields["phases"]]
        story = [Paragraph("RANCANGAN PENGAJARAN HARIAN", heading),
                 Paragraph("AKTIVITI KHAS - DRAF UNTUK SEMAKAN GURU", sub),
                 grid(meta, (26, 65, 30, 65)), Spacer(1, 2 * mm),
                 grid(info, (43, 143)), Spacer(1, 2 * mm),
                 grid(steps, (43, 143)), Spacer(1, 2 * mm),
                 grid([[strong("Refleksi"),
                        plain("____ / ____ murid mencapai objektif. Tindakan susulan: ____________")]],
                      (43, 143)), Spacer(1, 2 * mm),
                 Paragraph("CikguLaju | DRAF - Aktiviti khas tanpa SK/SP rasmi", body)]
        pdf.build(story)
        content = buf.getvalue()
        if len(PdfReader(io.BytesIO(content)).pages) == 1:
            return content
    raise SourceUnavailable("One-page PDF cannot be produced safely")


def render(row, year, teacher, fmt, subject=None):
    if fmt not in MIMES:
        raise ValueError("Unsupported format")
    fields = fields_for(row, year, teacher, subject=subject)
    return render_word(fields) if fmt == "word" else render_pdf(fields)
