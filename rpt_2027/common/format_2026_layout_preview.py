"""RPT 2027 teacher-first landscape table, modelled on 2026 RPT conventions.

PURE STAGING/PREVIEW renderer. Does not replace any live Telegram/Web PDF or
claim final curriculum/calendar approval. It accepts independently checked
source rows and will not fill unknown weeks, dates, SK or SP with guesses.
"""
from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
import re
from rpt_2027.common.teacher_display_projection import public_note, public_standard, public_topic, public_lesson_identity


SUBJECTS = {
    "psv": "PENDIDIKAN SENI VISUAL",
    "rbt": "REKA BENTUK DAN TEKNOLOGI",
    "moral": "PENDIDIKAN MORAL",
    "sejarah": "SEJARAH",
    "pjpk": "PENDIDIKAN JASMANI DAN PENDIDIKAN KESIHATAN",
    "english": "BAHASA INGGERIS",
    "bahasa_melayu": "BAHASA MELAYU",
    "matematik": "MATEMATIK",
    "pendidikan_islam": "PENDIDIKAN ISLAM",
    "bahasa_arab": "BAHASA ARAB",
    "muzik": "PENDIDIKAN MUZIK",
    "sains": "SAINS",
}
# Physical column order remains five columns; ONLY their displayed headings
# are localized. These are teaching-table headers, not editable source rows.
# PI uses Jawi terms found in school RPT examples; Arabic uses subject's
# Arabic pedagogical terminology; English uses source-SOW nomenclature.
LOCALIZED_TABLE_HEADINGS = {
    "pendidikan_islam": (
        "ميڠݢو / تاريخ", "بيدڠ / تاجوق / ڤدڤ",
        "ستندرد كاندوڠن", "ستندرد ڤمبالجرن", "چاتتن / باهن",
    ),
    "bahasa_arab": (
        "الأسبوع / التاريخ", "الوحدة / الموضوع / الدرس",
        "معيار المحتوى", "معيار التعلم", "الملاحظات / الوسائل",
    ),
    "english": (
        "WEEK / DATE", "UNIT / TOPIC / LESSON",
        "CONTENT STANDARD", "LEARNING STANDARD", "NOTES / MATERIALS",
    ),
}
DEFAULT_TABLE_HEADINGS = (
    "MINGGU / TARIKH", "UNIT / TAJUK / PDP",
    "SK", "SP", "CATATAN / BAHAN",
)
assert all(len(headings) == 5 and all(headings)
           for headings in LOCALIZED_TABLE_HEADINGS.values())

GROUP_A = "Kedah, Kelantan, Terengganu"
GROUP_B = "Negeri-negeri lain / Wilayah Persekutuan"
REQUIRED = ("id", "unit", "sk", "sp", "note")


def validate_rows(subject, year, records):
    if subject not in SUBJECTS or type(year) is not int or year not in range(2, 7):
        raise ValueError("Unsupported RPT subject/year")
    if subject in ("rbt", "sejarah") and year < 4:
        raise ValueError("RBT only for Year 4-6")
    if not isinstance(records, list) or not records or len(records) > 180:
        raise ValueError("RPT missing or oversized source rows")
    ids = []
    for row in records:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and
                                                 row[k].strip() for k in REQUIRED):
            raise ValueError("Incomplete sourced RPT row")
        if not re.fullmatch(r"\d{3}", row["id"]):
            raise ValueError("Invalid PdP number")
        if "display_id" in row and (not isinstance(row["display_id"], str) or not row["display_id"].strip()):
            raise ValueError("Invalid original-subject PdP identity")
        for field, source in (("sk_display", "sk"), ("sp_display", "sp")):
            if field in row and (not isinstance(row[field], str) or
                                 not row[field].strip() or
                                 not row[field].lstrip().startswith(re.split(r"\s*[/;,]\s*", row[source].strip())[0])):
                raise ValueError(f"Invalid enriched {field} for PdP {row['id']}")
        ids.append(int(row["id"]))
        for key in ("a_start", "a_end", "b_start", "b_end"):
            if row.get(key):
                try:
                    date.fromisoformat(row[key])
                except ValueError as exc:
                    raise ValueError("Invalid actual date range") from exc
    if ids != list(range(1, len(records) + 1)):
        raise ValueError("Missing, out-of-order or duplicate PdP numbers")
    display_ids = [row["display_id"] for row in records if row.get("display_id")]
    if len(display_ids) != len(set(display_ids)):
        raise ValueError("Duplicated original-subject PdP identity")
    for row in records:
        for prefix in ("a", "b"):
            a, b = row.get(prefix + "_start", ""), row.get(prefix + "_end", "")
            if bool(a) != bool(b) or (a and a > b):
                raise ValueError("Incomplete or reversed group date range")
    return True


def week_merge_ranges(records, *, max_rows_per_group=None, first_group_max_rows=None):
    """Contiguous table-row ranges (1-indexed; row 0 is the table header).

    Only merge records that share an *explicit* week label and identical A/B
    ranges. Missing/placeholder weeks must remain separate to prevent all
    unallocated PdP (for example RBT) being incorrectly grouped together.
    """
    ranges = []
    start = 0
    def key(row):
        week = (row.get("week") or "").strip()
        if week.casefold() in ("", "belum ditetapkan", "belum ditentukan", "agihan cadangan"):
            return None
        return (week, *(row.get(f"{group}_{end}") or "" for group in ("a", "b")
                        for end in ("start", "end")))
    while start < len(records):
        current = key(records[start])
        end = start
        if current is not None:
            # Preserve compact pages for all later weeks, while allowing the
            # teacher's first shorter school week to appear in one merged cell.
            max_rows = first_group_max_rows if start == 0 and first_group_max_rows is not None else max_rows_per_group
            while (end + 1 < len(records)
                   and key(records[end + 1]) == current
                   and (max_rows is None or end - start + 1 < max_rows)):
                end += 1
        ranges.append((start + 1, end + 1))
        start = end + 1
    return ranges


def normalize_pdf_text(value):
    """Render original DSKP private-use bullets without dropping their meaning.

    Original crosswalk text remains unchanged for source comparison. Unmapped
    PDF private-use characters must not silently produce blank glyphs.
    """
    source = str(value or "")
    printable = source.translate({
        0xF0B7: " • ",  # KPM DSKP PDF bullet character
        0xF02D: " - ",  # KPM DSKP PDF list hyphen
    })
    if any(0xE000 <= ord(char) <= 0xF8FF for char in printable):
        raise ValueError("Unmapped private-use glyph in DSKP statement")
    if any(ord(char) < 32 and char not in "\t\n\r" for char in printable):
        raise ValueError("Nonprinting control character in RPT text")
    return printable


def build_preview(subject, year, records, destination, *, logo_path=None, school_name="", teacher_name="", max_span_rows=None, first_week_span_rows=None):
    """Create compact, multi-page landscape PDF using only trusted row content.

    One 5-column table: MINGGU/TARIKH | UNIT/TAJUK/PDp | SK | SP | CATATAN.
    Never claims unknown weeks/tarikh as true. Dates are *guides*, not IDs.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Image, LongTable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
        TableStyle
    )

    validate_rows(subject, year, records)
    # Arabic/Jawi RPTs read their five columns from right to left.
    # All other subjects preserve the same LTR five-column source template.
    rtl_table = subject in ("pendidikan_islam", "bahasa_arab")
    out = Path(destination)
    out.parent.mkdir(parents=True, exist_ok=True)
    reg = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    heavy = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    font, bold = "Helvetica", "Helvetica-Bold"
    if reg.is_file() and heavy.is_file():
        if "RPTStandardRegular" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RPTStandardRegular", str(reg)))
        if "RPTStandardBold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RPTStandardBold", str(heavy)))
        font, bold = "RPTStandardRegular", "RPTStandardBold"
    amiri_reg = Path("/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf")
    amiri_bold = Path("/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf")
    if amiri_reg.is_file() and amiri_bold.is_file():
        if "RPTAmiriRegular" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RPTAmiriRegular", str(amiri_reg)))
        if "RPTAmiriBold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("RPTAmiriBold", str(amiri_bold)))
        arabic_font, arabic_heavy = "RPTAmiriRegular", "RPTAmiriBold"
    else:
        arabic_font, arabic_heavy = font, bold


    # The cover is a locked original LTR teacher-profile template for ALL
    # subjects; RTL applies only to the teaching table that follows.
    table_part = False
    ink = colors.HexColor("#293944")
    line = colors.HexColor("#adb7ba")
    soft = colors.HexColor("#fff4bb")
    paper = colors.HexColor("#fcfcf8")
    w, h = landscape(A4)
    lm, rm = 29, 29
    usable = w - lm - rm

    def p(text, *, size=7.5, leading=11.3, strong=False, color="#263b4e", center=False):
        uses_arabic = any("\u0600" <= ch <= "\u08ff" for ch in str(text))
        style = ParagraphStyle(
            "rpt", fontName=(arabic_heavy if strong else arabic_font) if uses_arabic
            else (bold if strong else font),
            fontSize=size, leading=leading, textColor=colors.HexColor(color),
            wordWrap="CJK", spaceBefore=0, spaceAfter=0,
            alignment=1 if center else (2 if rtl_table and table_part else 0)
        )
        printable = normalize_pdf_text(text)
        if any("\u0600" <= ch <= "\u08ff" for ch in printable):
            from arabic_reshaper import reshape
            from bidi.algorithm import get_display
            printable = "\n".join(
                get_display(reshape(piece), base_dir="R") if piece.strip() else piece
                for piece in printable.split("\n")
            )
        return Paragraph(escape(printable).replace("\n", "<br/>"), style)

    def source_pdf_link(url, page_number):
        """A user-clickable original source, without treating it as signoff."""
        if (not isinstance(url,str)
            or not re.fullmatch(r"https://drive\.google\.com/file/d/[A-Za-z0-9_-]{20,}/view",url)
            or type(page_number) is not int or not 1 <= page_number <= 300):
            raise ValueError("Invalid untrusted DSKP source link or PDF page")
        label=f"Buka DSKP asal (halaman PDF {page_number})"
        # Google Drive may not honor #page; explicit printed page label is
        # retained, and the link still opens the exact original source file.
        xml=f'<link href="{escape(url,quote=True)}" color="#075ba8">{escape(label)}</link>'
        return Paragraph(xml,ParagraphStyle(
            "source-link",fontName=font,fontSize=7.1,leading=11,
            textColor=colors.HexColor("#075ba8"),spaceBefore=3,spaceAfter=0))

    def cell(text, strong=False):
        return p(text, strong=strong)

    def range_text(row, prefix):
        first, last = row.get(prefix + "_start", ""), row.get(prefix + "_end", "")
        if first and last:
            start = date.fromisoformat(first).strftime("%d/%m/%Y")
            end = date.fromisoformat(last).strftime("%d/%m/%Y")
            return start if first == last else start + " - " + end
        return "—"

    doc = SimpleDocTemplate(
        str(out), pagesize=(w, h),
        leftMargin=lm, rightMargin=rm, topMargin=43, bottomMargin=38,
        title=f"RPT {SUBJECTS[subject]} Tahun {year} 2027",
        author="CikguLaju AI"
    )

    def header(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(line)
        canvas.line(lm, h-32, w-rm, h-32)
        canvas.setFont(bold, 8)
        canvas.setFillColor(ink)
        canvas.drawString(lm, h-24, f"RPT {SUBJECTS[subject]} - TAHUN {year} / 2027")
        canvas.setFont(font, 7)
        canvas.drawRightString(w-rm, h-24, "KUMPULAN A / B")
        canvas.line(lm, 31, w-rm, 31)
        canvas.drawString(lm, 20, "RANCANGAN PENGAJARAN TAHUNAN 2027")
        canvas.drawRightString(w-rm, 20, f"Halaman {doc.page}")
        canvas.restoreState()

    # Cover page deliberately contains ONLY the RPT title/subject/year plus
    # school logo, school name and teacher name. A/B guidance stays in tables.
    # Optional values can be supplied by a future authenticated profile flow;
    # they are never fetched or guessed by this staging renderer.
    for value, label in ((school_name, "school_name"), (teacher_name, "teacher_name")):
        if not isinstance(value, str) or len(value.strip()) > 180:
            raise ValueError(f"Invalid {label} on RPT cover")
    logo = p("LOGO SEKOLAH", size=9, leading=13, center=True, color="#67747d")
    if logo_path is not None:
        from reportlab.lib.utils import ImageReader
        filename = Path(logo_path)
        if not filename.is_file() or filename.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            raise ValueError("School logo must be a readable PNG/JPG file")
        iw, ih = ImageReader(str(filename)).getSize()
        if iw <= 0 or ih <= 0:
            raise ValueError("Invalid school logo dimensions")
        scale = min(114 / iw, 114 / ih)
        logo = Image(str(filename), width=iw * scale, height=ih * scale)
    logo_frame = Table([[logo]], colWidths=[130], rowHeights=[130], hAlign="CENTER")
    logo_frame.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.9, colors.HexColor("#94a3ab")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]))
    form = Table([
        [p("NAMA SEKOLAH", size=10, leading=16, strong=True),
         p(school_name.strip() or "__________________________________________",
           size=10, leading=16)],
        [p("NAMA GURU", size=10, leading=16, strong=True),
         p(teacher_name.strip() or "__________________________________________",
           size=10, leading=16)],
    ], colWidths=[170, 490], rowHeights=[56, 56], hAlign="CENTER")
    form.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f8f6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.HexColor("#cdd7d9")),
        ("BOX", (0, 0), (-1, -1), 0.55, colors.HexColor("#aabbbd")),
    ]))
    cover = [
        Spacer(1, 20),
        logo_frame,
        Spacer(1, 27),
        p("RANCANGAN PENGAJARAN TAHUNAN 2027",
          size=21, leading=28, strong=True, center=True),
        Spacer(1, 13),
        p(f"{SUBJECTS[subject]}  |  TAHUN {year}",
          size=15, leading=23, strong=True, center=True),
        Spacer(1, 28),
        form,
        PageBreak(),
    ]

    def blank_cover_header(canvas, doc):
        # No headers, footers, labels, status or extra metadata on cover.
        pass

    # All cover blocks are constructed in the original left-aligned
    # profile form before table alignment switches to right for Arabic/Jawi.
    table_part = True
    # The rightmost column in RTL is the first logical column
    # MINGGU -> UNIT/PdP -> SK -> SP -> CATATAN (read right to left).
    logical_headings = LOCALIZED_TABLE_HEADINGS.get(
        subject, DEFAULT_TABLE_HEADINGS)
    headings = tuple(reversed(logical_headings)) if rtl_table else logical_headings
    table_rows = [[p(t,size=8.0,leading=11.7,strong=True,color="#25323a") for t in headings]]
    if max_span_rows is not None and (type(max_span_rows) is not int or not 1 <= max_span_rows <= 8):
        raise ValueError("Invalid maximum merged week rows")
    if first_week_span_rows is not None and (type(first_week_span_rows) is not int or not 1 <= first_week_span_rows <= 8):
        raise ValueError("Invalid first-week merged rows")
    week_ranges = week_merge_ranges(
        records, max_rows_per_group=max_span_rows,
        first_group_max_rows=first_week_span_rows)
    grouped_followers = {index for first, last in week_ranges for index in range(first + 1, last + 1)}
    for index, row in enumerate(records, 1):
        week = row.get("week","").strip() or "—"
        weektext = (f"{week}\nKumpulan A:\n{range_text(row,'a')}"
                    f"\nKumpulan B:\n{range_text(row,'b')}")
        unit_lines=[
            p(public_lesson_identity(subject, row),size=8.1,leading=12,strong=True),
        ]
        unit_text=row["unit"].strip()
        # Separate Latin "Unit N:" from Arabic title to preserve reading order.
        # Both stay in the original Unit/Tajuk/PdP table cell.
        unit_match=(re.match(r"^(Unit\s+\d+)\s*:\s*(.+)$",unit_text)
                    if subject=="bahasa_arab" else None)
        if unit_match and any("\u0600"<=ch<="\u08ff" for ch in unit_match.group(2)):
            unit_lines.append(p(unit_match.group(1)+":",size=8,leading=12,strong=True))
            unit_lines.append(p(unit_match.group(2),size=8,leading=12,strong=True))
        else:
            unit_lines.append(p(unit_text,size=8,leading=12,strong=True))
        if row.get("topic","").strip():
            topic_text=public_topic(row)
            # Malay teacher-focus and Arabic words are separate paragraphs.
            topic_match=(re.match(r"^([^\u0600-\u08ff]+?)\s+([\u0600-\u08ff].+)$",topic_text)
                         if subject=="bahasa_arab" else None)
            if topic_match:
                unit_lines.append(p(topic_match.group(1).strip(),size=7.8,leading=11.6))
                unit_lines.append(p(topic_match.group(2).strip(),size=7.8,leading=11.6))
            else:
                unit_lines.append(p(topic_text,size=7.8,leading=11.6))
        note_cell=[p(public_note(row),size=7.6,leading=11.5)]
        if "source_sp_dskp_pdf_url" in row:
            if subject!="bahasa_arab" or row.get("source_sp_dskp_text_signoff") is not False:
                raise ValueError("DSKP URL link only supported for unapproved Arabic sources")
            note_cell.append(source_pdf_link(row["source_sp_dskp_pdf_url"],
                                             row["source_sp_dskp_pdf_page"]))
        logical_cells = [
            "" if index in grouped_followers else p(weektext,size=7.0,leading=11.3),
            unit_lines,
            p(public_standard(row, "sk"),size=7.5,leading=11.3),
            p(public_standard(row, "sp"),size=7.3,leading=10.8),
            note_cell
        ]
        table_rows.append(list(reversed(logical_cells)) if rtl_table else logical_cells)
    # Reserve more width for the newly expanded full DSKP SK/SP statements.
    logical_widths = [105, 180, 125, 210, usable - 105 - 180 - 125 - 210]
    widths = list(reversed(logical_widths)) if rtl_table else logical_widths
    if any(x < 0 for x in widths) or abs(sum(widths)-usable)>0.2:
        raise ValueError("RPT layout width overflows landscape A4")

    tbl = LongTable(table_rows, colWidths=widths, repeatRows=1, hAlign="LEFT",
                    splitByRow=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),soft),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,paper]),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),7),
        ("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,0),9),
        ("BOTTOMPADDING",(0,0),(-1,0),9),
        ("TOPPADDING",(0,1),(-1,-1),9),
        ("BOTTOMPADDING",(0,1),(-1,-1),9),
        ("LINEBELOW",(0,0),(-1,0),0.5,line),
        ("LINEBELOW",(1,1),(-1,-1),0.35,line),
        ("LINEBEFORE",(1,0),(-1,-1),0.3,line),
        ("BOX",(0,0),(-1,-1),0.6,ink)
    ]))
    # The week/date column is genuinely vertically merged, on the right for
    # Jawi/Arabic and on the left for all remaining subjects.
    week_col = 4 if rtl_table else 0
    for first, last in week_ranges:
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (week_col, first), (week_col, last), colors.HexColor("#eaf1e3")),
            ("VALIGN", (week_col, first), (week_col, last), "MIDDLE"),
            ("LINEBELOW", (week_col, last), (week_col, last), 0.35, line),
        ] + ([("SPAN", (week_col, first), (week_col, last))] if last > first else [])))
    story = cover + [tbl]
    doc.build(story, onFirstPage=blank_cover_header, onLaterPages=header)
    if not out.is_file() or out.stat().st_size < 5000:
        raise ValueError("RPT preview PDF output invalid")
    return out
