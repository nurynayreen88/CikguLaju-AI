"""Student-copy PDF for the four teacher-authored English Year 4 worksheets.

Exact Lesson registry comes from the supplementary Telegram source. This module
does not synthesize new exercises, call the Telegram backend, or touch credits.
It deliberately excludes teacher-only answers and assessment notes.
"""
from io import BytesIO
from pathlib import Path
import re

from english_supplementary_materials import available, ROOT, YEAR4

MAX_SOURCE_BYTES = 16000
ALLOWED_LESSONS = frozenset((4, 79, 89, 90))
# Teacher metadata is a trailing section, not just a single line.
# Stop at its first heading to block accidental multi-line answer key leaks.
_TEACHER_ONLY = re.compile(
    r"^\s*(?:(?:\*\*)|(?:#{1,6}\s+))?"
    r"(?:Teacher(?:-only)?\s+(?:assessment|notes?|guidance)|"
    r"Answer\s+key(?:\s*\([^)]*\))?|Suggested\s+answers?|"
    r"Model\s+answers?|Solutions?)\b", re.I
)
_PURPOSE_ONLY = re.compile(r"^\s*(?:\*\*)?Purpose\s*:", re.I)
_DOC_TITLE = re.compile(r"^#\s+English Year 4\s+—\s+Lesson\s+(\d{3})\s+—\s+(.+)$")


def _source(year, lesson):
    """Read only an exact, non-symlinked registered source in our own repo."""
    if type(year) is not int or year != 4 or type(lesson) is not int or lesson not in ALLOWED_LESSONS:
        return None
    rows = available({"subject": "English", "year": "Year 4", "lesson_no": lesson})
    if len(rows) != 1 or rows[0].get("lesson") != lesson:
        return None
    root = (ROOT / "year4").resolve()
    expected = root / ("lesson_%03d_worksheet.md" % lesson)
    path = Path(rows[0]["path"])
    if path.is_symlink() or path.resolve() != expected or not path.is_file():
        return None
    if path.stat().st_size > MAX_SOURCE_BYTES:
        return None
    raw = path.read_text(encoding="utf-8")
    header = raw.splitlines()[0] if raw else ""
    match = _DOC_TITLE.fullmatch(header)
    if not match or int(match.group(1)) != lesson:
        return None
    return rows[0]["title"], raw


def worksheet_metadata(year, lesson):
    record = _source(year, lesson)
    if record is None:
        return None
    title, _ = record
    return "Lembaran Kerja Tambahan English Tahun 4 • Lesson %03d — %s" % (lesson, title)


def _student_lines(raw):
    """Never put source-side teacher notes/answer keys in pupil PDF bytes."""
    lines = []
    for original in raw.splitlines():
        line = original.rstrip()
        if _TEACHER_ONLY.match(line):
            break
        if _PURPOSE_ONLY.match(line):
            continue
        # Strip simple Markdown presentation syntax from teacher-authored text.
        line = line.replace("**", "").replace("*", "").replace("  ", " ")
        if line.startswith("- [ ] "):
            line = "[ ] " + line[6:]
        elif line.startswith("- "):
            line = "- " + line[2:]
        lines.append(line)
    return lines


def _pdf_text(s):
    # ReportLab base Helvetica is intentionally selected to avoid dynamic
    # fonts. Fold punctuation unsupported by that core PDF font.
    translate = str.maketrans({
        "—": "-", "–": "-", "‘": "'", "’": "'", "“": '"', "”": '"',
        "•": "-", "…": "...", "\u00a0": " ", "✓": "v",
    })
    return str(s).translate(translate)


def worksheet_pdf(year, lesson):
    """Return one-page A4 pupil worksheet, or None when source is unapproved."""
    record = _source(year, lesson)
    if record is None:
        return None
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfgen import canvas

    _title, raw = record
    width, height = A4
    left, right = 44, 44
    usable = width - left - right
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=A4, pageCompression=1)
    pdf.setTitle("CikguLaju English Year 4 Lesson %03d - Supplementary Worksheet" % lesson)
    pdf.setAuthor("CikguLaju AI")
    pdf.setSubject("Teacher-authored additional pupil activity; not official textbook")
    pdf.setStrokeColor(colors.HexColor("#d5e7e1"))
    pdf.line(left, height - 47, width - right, height - 47)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.setFillColor(colors.HexColor("#12594c"))
    pdf.drawString(left, height - 39, "CIKGULAJU AI | ENGLISH YEAR 4")
    pdf.setFillColor(colors.black)
    y = height - 69

    def draw(line, *, kind="normal", leading=13.7):
        nonlocal y
        if kind == "title":
            font, size, space = "Helvetica-Bold", 12, 8
        elif kind == "section":
            font, size, space = "Helvetica-Bold", 10.2, 4
        else:
            font, size, space = "Helvetica", 9.5, 0
        content = _pdf_text(line)
        if kind == "normal" and not content.strip():
            y -= 5
            return
        if kind != "normal":
            y -= space
        if kind == "title" and content.startswith("# "):
            content = content[2:]
        if kind == "section" and content.startswith("## "):
            content = content[3:]
        parts = simpleSplit(content, font, size, usable)
        for part in parts:
            if y < 58:
                raise ValueError("Worksheet cannot fit on A4 without truncation")
            pdf.setFillColor(colors.HexColor("#12594c") if kind != "normal" else colors.black)
            pdf.setFont(font, size)
            pdf.drawString(left, y, part)
            y -= leading if kind == "normal" else (15.5 if kind == "section" else 16.5)

    for raw_line in _student_lines(raw):
        if raw_line.startswith("## "):
            draw(raw_line, kind="section")
        elif raw_line.startswith("# "):
            draw(raw_line, kind="title")
        else:
            draw(raw_line)
    pdf.setStrokeColor(colors.HexColor("#d5e7e1"))
    pdf.line(left, 39, width - right, 39)
    pdf.setFont("Helvetica", 7.5)
    pdf.setFillColor(colors.HexColor("#4c625d"))
    pdf.drawString(left, 26, "Teacher-created supplementary worksheet. Not an official textbook page.")
    pdf.drawRightString(width - right, 26, "Lesson %03d  |  1 / 1" % lesson)
    pdf.showPage()
    pdf.save()
    result = stream.getvalue()
    if not result.startswith(b"%PDF-") or len(result) < 900 or len(result) > 300000:
        raise ValueError("Worksheet PDF generation failed")
    return result
