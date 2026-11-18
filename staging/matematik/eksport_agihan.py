"""Validate and export the SK Mathematics 2027 weekly allocation for teacher review."""

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Table, TableStyle


SOURCE = Path(__file__).with_name('rpt_2027_agihan.json')
MONTHS = ('Jan', 'Feb', 'Mac', 'Apr', 'Mei', 'Jun', 'Jul', 'Ogo', 'Sep', 'Okt', 'Nov', 'Dis')
SHORT_WEEKS = {1, 5, 10, 20, 30, 33, 35}
NON_TEACHING = {6, 18, 19, 39, 40, 41, 42, 43, 44}
TEACHING = set(range(1, 45)) - NON_TEACHING
INK = colors.HexColor('#153449')
SECONDARY = colors.HexColor('#3D5260')
TEAL = colors.HexColor('#08645D')
GRID = colors.HexColor('#D6E1E5')
FONTS = Path('/usr/share/fonts/truetype/dejavu')
REGULAR = 'AgihanSans'
BOLD = 'AgihanSansBold'


def read_agihan(path=SOURCE):
    data = json.loads(path.read_text(encoding='utf-8'))
    if (data['tahun_rpt'], data['subjek'], data['status']) != (2027, 'Matematik SK', 'DRAF SEMAKAN GURU'):
        raise ValueError('Agihan Matematik SK 2027 yang sah diperlukan.')
    weeks = data['takwim']
    if [row['minggu'] for row in weeks] != list(range(1, 45)):
        raise ValueError('Takwim Kumpulan A/B mesti mempunyai 44 minggu mengikut urutan.')
    for row in weeks:
        for group in ('A', 'B'):
            start, end = map(date.fromisoformat, row[group])
            if start.year != 2027 or end.year != 2027 or not 0 <= (end - start).days <= 4:
                raise ValueError(f"Tarikh Kumpulan {group} pada M{row['minggu']:02d} tidak sah.")
        if (row['minggu'] in NON_TEACHING) != bool(row.get('catatan')):
            raise ValueError(f"Semak catatan pada M{row['minggu']:02d}.")
    if weeks[9]['A'] != ['2027-03-15', '2027-03-18']:
        raise ValueError('M10 Kumpulan A perlu mengambil kira cuti tambahan Aidilfitri pada 14 Mac.')

    years = data['tahun']
    if years.keys() != {'2', '3', '4', '5', '6'}:
        raise ValueError('Agihan mesti merangkumi Tahun 2–6.')
    for year, annual in years.items():
        by_week = {int(week): lessons for week, lessons in annual['minggu'].items()}
        if by_week.keys() != TEACHING:
            raise ValueError(f'Tahun {year} mesti tamat M38 dengan M06, M18 dan M19 kosong.')
        lessons = [item for week in sorted(by_week) for item in by_week[week]]
        if [number for number, _ in lessons] != list(range(1, 118)):
            raise ValueError(f'Tahun {year} mesti mengekalkan urutan Lesson 001–117.')
        if Counter(minutes for _, minutes in lessons) != {30: 42, 60: 75}:
            raise ValueError(f'Tahun {year} mesti mempunyai 5,760 minit.')
        for week, sessions in by_week.items():
            count, minutes = len(sessions), sum(duration for _, duration in sessions)
            valid = (count, minutes) == (2, 120) if week in SHORT_WEEKS else (count, minutes) in {
                (3, 150), (3, 180), (4, 180),
            }
            if not valid:
                raise ValueError(f'Tahun {year} mempunyai agihan di luar slot pada M{week:02d}.')
    return data


def display_dates(window):
    start, end = map(date.fromisoformat, window)
    end_label = f'{end.day} {MONTHS[end.month - 1]}'
    start_label = str(start.day) if start.month == end.month else f'{start.day} {MONTHS[start.month - 1]}'
    return f'{start_label} - {end_label}'


def page_table(weeks, lessons_by_week):
    cells = [['Minggu', 'Kumpulan A', 'Kumpulan B', 'Lesson 30 min', 'Lesson 60 min', 'Jumlah min']]
    shaded = []
    for row in weeks:
        week = row['minggu']
        sessions = lessons_by_week.get(str(week), [])
        label_a, label_b = display_dates(row['A']), display_dates(row['B'])
        if sessions:
            durations = [', '.join(f'{n:03d}' for n, duration in sessions if duration == minutes)
                         for minutes in (30, 60)]
            cells.append([f'M{week:02d}', label_a, label_b, *durations, sum(m for _, m in sessions)])
        else:
            shaded.append(len(cells))
            cells.append([f'M{week:02d}', label_a, label_b, row['catatan'], '', ''])
    table = Table(cells, colWidths=(44, 91, 91, 104, 104, 85), rowHeights=(28, *[24] * len(weeks)))
    style = [
        ('FONTNAME', (0, 0), (-1, -1), REGULAR),
        ('FONTNAME', (0, 0), (-1, 0), BOLD),
        ('FONTNAME', (0, 1), (0, -1), BOLD),
        ('FONTNAME', (-1, 1), (-1, -1), BOLD),
        ('BACKGROUND', (0, 0), (-1, 0), TEAL), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5), ('TEXTCOLOR', (0, 1), (-1, -1), INK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), (colors.white, colors.HexColor('#F4F8F9'))),
        ('LINEBELOW', (0, 1), (-1, -1), 0.35, GRID),
    ]
    for row in shaded:
        style.extend([
            ('SPAN', (3, row), (5, row)), ('BACKGROUND', (0, row), (-1, row), colors.HexColor('#E8F3EE')),
            ('FONTNAME', (3, row), (5, row), REGULAR),
        ])
    table.setStyle(TableStyle(style))
    return table


def export(data, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont(REGULAR, str(FONTS / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont(BOLD, str(FONTS / 'DejaVuSans-Bold.ttf')))
    pdf = Canvas(str(target), pagesize=A4)
    pdf.setTitle('CikguLaju | Agihan RPT Matematik SK 2027')
    pdf.setAuthor('CikguLaju')
    width, height = A4
    for year, annual in sorted(data['tahun'].items()):
        for part, start in enumerate((0, 22), 1):
            if part == 1:
                anchor = f'tahun-{year}'
                pdf.bookmarkPage(anchor)
                pdf.addOutlineEntry(f'Tahun {year}', anchor)
            pdf.setFillColor(TEAL)
            pdf.setFont(BOLD, 10)
            pdf.drawString(38, height - 47, 'CIKGULAJU  /  DRAF SEMAKAN GURU')
            pdf.setFillColor(INK)
            pdf.setFont(BOLD, 24)
            pdf.drawString(38, height - 79, f'Matematik SK Tahun {year}')
            pdf.setFont(REGULAR, 13)
            pdf.drawString(38, height - 101, f'Agihan RPT 2027   |   Minggu {start + 1:02d}-{start + 22:02d}')
            pdf.setFillColor(SECONDARY)
            pdf.setFont(REGULAR, 9.5)
            pdf.drawString(38, height - 125, '117 Lesson  ·  96 jam  ·  PdP terakhir pada Minggu 38')
            pdf.drawString(38, height - 141, 'Ikut turutan nombor Lesson. Slot 30 min memerlukan penyesuaian RPH v60.')
            table = page_table(data['takwim'][start:start + 22], annual['minggu'])
            _, table_height = table.wrap(width - 76, height)
            table.drawOn(pdf, 38, height - 157 - table_height)
            pdf.setStrokeColor(GRID)
            pdf.line(38, 59, width - 38, 59)
            pdf.setFont(REGULAR, 9)
            pdf.drawString(38, 43, 'Kalendar Akademik KPM 2027 dan RPT Matematik v28')
            pdf.linkURL('https://www.moe.gov.my/kalendar-akademik-semasa', (38, 42, 185, 55))
            pdf.drawRightString(width - 38, 43, f'Tahun {year}  |  {part}/2')
            pdf.showPage()
    pdf.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write the combined teacher-review PDF.')
    args = parser.parse_args()
    data = read_agihan()
    if args.output:
        export(data, args.output)
    print('585 Lesson disahkan. Setiap tahun ada 117 Lesson dan 96 jam hingga Minggu 38.')


if __name__ == '__main__':
    main()
