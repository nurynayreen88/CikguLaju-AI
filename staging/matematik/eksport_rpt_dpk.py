"""Render a full SK Mathematics RPT from verified yearly DPK lesson details."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

from staging.matematik.eksport_agihan import display_dates, read_agihan


FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
REGULAR = 'RPTRegular'
BOLD = 'RPTBold'
TEAL = colors.HexColor('#08645D')
INK = colors.HexColor('#153449')
GRID = colors.HexColor('#D6E1E5')


def export_table(output, year, details):
    pdfmetrics.registerFont(TTFont(REGULAR, str(FONT_DIR / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont(BOLD, str(FONT_DIR / 'DejaVuSans-Bold.ttf')))
    body = ParagraphStyle('RPT body', fontName=REGULAR, fontSize=8.5, leading=12, textColor=INK)
    bold = ParagraphStyle('RPT bold', parent=body, fontName=BOLD)
    head = ParagraphStyle('RPT heading', parent=bold, textColor=colors.white)
    title = ParagraphStyle('RPT title', parent=bold, fontSize=21, leading=28)
    summary = ParagraphStyle('RPT summary', parent=body, fontSize=10, leading=14)

    def pair(value, style=body):
        return Paragraph(escape(value).replace('\n', '<br/>'), style)

    agihan = read_agihan()
    weeks = agihan['tahun'][str(year)]['minggu']
    columns = ('Minggu dan tarikh', 'Lesson', 'Unit dan tajuk', 'SK, SP dan rujukan', 'Evidens pentaksiran')
    data = [[pair(text, head) for text in columns]]
    off_rows = []
    week_boundaries = []
    for week in agihan['takwim']:
        week_number = week['minggu']
        sessions = weeks.get(str(week_number), [])
        label = f"M{week_number:02d}\nA {display_dates(week['A'])}\nB {display_dates(week['B'])}"
        week_boundaries.append(len(data))
        if not sessions:
            off_rows.append(len(data))
            data.append([pair(label, bold), pair(week['catatan']), '', '', ''])
        for number, time in sessions:
            unit, unit_name, topic, sk, sp, dpk, volume, textbook, evidence = details[number]
            reference = f'SK {sk}\nSP {sp}\nDPK hlm. {dpk} · BT Jilid {volume}, hlm. {textbook}'
            data.append([
                pair(label), pair(f'{number:03d}\n{time} min', bold),
                pair(f'Unit {unit} {unit_name}\n{topic}'), pair(reference), pair(evidence),
            ])

    table = LongTable(data, colWidths=(100, 57, 172, 206, 235), repeatRows=1, hAlign='LEFT')
    commands = [
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), (colors.white, colors.HexColor('#F5F8F9'))),
        ('LINEBELOW', (0, 1), (-1, -1), 0.35, GRID),
    ]
    commands.extend(('LINEABOVE', (0, n), (-1, n), 0.6, GRID) for n in week_boundaries)
    for row in off_rows:
        commands.extend([('SPAN', (1, row), (-1, row)), ('BACKGROUND', (0, row), (-1, row), colors.HexColor('#E8F3EE'))])
    table.setStyle(TableStyle(commands))

    width, _ = landscape(A4)

    def footer(canvas, document):
        canvas.setFont(REGULAR, 8)
        canvas.setFillColor(INK)
        canvas.drawString(35, 25, f'CikguLaju · Matematik SK Tahun {year} · 2027 · Draf semakan guru')
        canvas.drawRightString(width - 35, 25, f'Halaman {document.page}')

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = SimpleDocTemplate(str(output), pagesize=landscape(A4), leftMargin=35, rightMargin=35,
                            topMargin=32, bottomMargin=42, title=f'RPT Matematik SK Tahun {year} 2027')
    pdf.build([
        pair(f'RPT Matematik SK Tahun {year} 2027', title),
        pair('117 Lesson · 96 jam · Draf semakan guru · Dokumen Penjajaran Edisi 3', summary),
        pair('Gunakan julat Kumpulan A atau B mengikut sekolah. PdP terakhir dijadualkan pada Minggu 38.', summary),
        Spacer(1, 10), table,
    ], onFirstPage=footer, onLaterPages=footer)
