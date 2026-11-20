"""Print the Unit 2 allocation from the same catalog as the individual RPH."""
from io import BytesIO
from xml.sax.saxutils import escape

from staging.ppki.catalog import catalog
from staging.ppki.render_pengurusan_kehidupan import PPKI_LABEL_FILL


def render_rpt():
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from web.rph_document_style import pdf_fonts

    source = catalog()
    regular, bold, _ = pdf_fonts()
    normal = ParagraphStyle("RPT cell", fontName=regular, fontSize=9, leading=11)
    header = ParagraphStyle("RPT heading", parent=normal, fontName=bold)
    title = ParagraphStyle("RPT title", parent=header, fontSize=16, leading=19)
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
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=landscape(A4), title="RPT PPKI Tahun 2 · Agihan PdP Unit 2",
                            leftMargin=15 * mm, rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=12 * mm)
    doc.build([
        Paragraph("RPT 2027 · Agihan PdP Unit 2", title),
        Paragraph("PPKI · Pengurusan Kehidupan Tahun 2 · Pengurusan Diri", header),
        Paragraph(escape(source["unit"]), header),
        Spacer(1, 3 * mm),
        Paragraph("Guru menetapkan tarikh PdP mengikut jadual sekolah dan keperluan kelas.", normal),
        Spacer(1, 3 * mm),
        table,
    ])
    return stream.getvalue()
