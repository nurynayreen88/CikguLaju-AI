"""Print allocations from the same catalog as the individual PPKI RPH."""
from io import BytesIO
from xml.sax.saxutils import escape

from staging.ppki.catalog import (
    MANIPULATIVE_UNIT_LESSONS, RPT_COMBINED_EDITION, RPT_YEAR3_EDITION, UNIT, UNIT_LESSONS,
    YEAR, YEAR3_LESSONS, YEAR3_MANIPULATIVE_UNIT_LESSONS, RPT_YEAR4_EDITION, YEAR4_LESSONS, catalog,
)
from staging.ppki.render_pengurusan_kehidupan import PPKI_LABEL_FILL


def render_rpt(*, combined=False, manipulative=False, year=YEAR):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from web.rph_document_style import pdf_fonts

    regular, bold, _ = pdf_fonts()
    font_size, leading, cell_padding = (8.5, 10, 3) if manipulative or year == 3 else (9, 11, 4)
    normal = ParagraphStyle("RPT cell", fontName=regular, fontSize=font_size, leading=leading)
    header = ParagraphStyle("RPT heading", parent=normal, fontName=bold)
    title = ParagraphStyle("RPT title", parent=header, fontSize=16, leading=19)

    def unit_story(unit, number):
        source = catalog(unit, year=year)
        padding = 1 if year in (3, 4) and unit == UNIT else cell_padding
        rows = [[Paragraph(label, header) for label in ("PdP", "Fokus", "SK", "SP", "Buku Teks")]]
        for lesson in source["lessons"]:
            sp = lesson["sp"]
            sk = sp.rsplit(".", 1)[0]
            values = (
                lesson["pdp"], lesson["title"], f"{sk} {source['content_standards'][sk]}",
                f"{sp} {source['learning_standards'][sp]}", lesson["book"].removeprefix("Buku Teks "),
            )
            rows.append([Paragraph(escape(v), normal) for v in values])
        table = Table(rows, colWidths=[16 * mm, 68 * mm, 51 * mm, 102 * mm, 26 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#" + PPKI_LABEL_FILL)),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#80758A")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ]))
        return [
            Paragraph(f"RPT 2027 · Agihan PdP Unit {number}", title),
            Paragraph(escape(f"PPKI · Pengurusan Kehidupan Tahun {year} · {source['component']}"), header),
            Paragraph(escape(source["unit"]), header),
            Spacer(1, 3 * mm),
            Paragraph("Guru menetapkan tarikh PdP mengikut jadual sekolah dan keperluan kelas.", normal),
            Spacer(1, 3 * mm),
            table,
        ]

    if year == 3 and manipulative:
        units = YEAR3_MANIPULATIVE_UNIT_LESSONS
        edition = "Kemahiran Manipulatif Unit 1–3"
    elif year == 3:
        units = YEAR3_LESSONS
        edition = RPT_YEAR3_EDITION
    elif year == 4 and not manipulative:
        units = YEAR4_LESSONS
        edition = RPT_YEAR4_EDITION
    elif year != YEAR:
        raise ValueError("Unknown PPKI RPT")
    elif manipulative:
        units = MANIPULATIVE_UNIT_LESSONS
        edition = "Kemahiran Manipulatif Unit 1–3"
    else:
        units = UNIT_LESSONS if combined else (UNIT,)
        edition = RPT_COMBINED_EDITION if combined else "Unit 2"
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=landscape(A4), title=f"RPT PPKI Tahun {year} · Agihan PdP {edition}",
                            leftMargin=15 * mm, rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    story = []
    for unit in units:
        if story:
            story.append(PageBreak())
        story.extend(unit_story(unit, int(unit[1:3])))
    doc.build(story)
    return stream.getvalue()
