"""Reflow the original Telegram English PDFs to match the published Web ranges."""

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import fitz


COLUMNS = (37.6, 125.4, 288.8, 656.1, 804.4)
TABLE_TOP, CONTENT_TOP, CONTENT_BOTTOM = 49, 67.8, 548
INK = (0.15, 0.23, 0.31)
BORDER = (0.77, 0.81, 0.77)
FONTS = {
    'LiberationSans': 'LiberationSans-Regular.ttf',
    'LiberationSans-Bold': 'LiberationSans-Bold.ttf',
    'LiberationSans-Italic': 'LiberationSans-Italic.ttf',
    'LiberationSerif': 'LiberationSerif-Regular.ttf',
}
LESSON = re.compile(r'LESSON:\s*(\d+)')
WEEK = re.compile(r'WEEK \d{2}')
UNIT_SUMMARY = re.compile(r'Minggu (\d{2}(?:, \d{2})+)')


def spans(page, clip=None):
    return [span for block in page.get_text('dict', clip=clip)['blocks']
            for line in block.get('lines', ()) for span in line['spans']]


def lesson_rows(pdf):
    rows = []
    teaching_pages = []
    for page in pdf:
        if not any(WEEK.fullmatch(span['text']) for span in spans(page)):
            continue
        teaching_pages.append(page.number)
        boundaries = sorted({round(drawing['rect'].y0, 2) for drawing in page.get_drawings()
                             if drawing['rect'].width > 650 and drawing['rect'].height < 0.1
                             and 66 < drawing['rect'].y0 < CONTENT_BOTTOM})
        if len(boundaries) != 5 or page.get_links():
            raise ValueError(f'Unexpected lesson table on the original page {page.number + 1}')
        for top, bottom in zip(boundaries, boundaries[1:]):
            row = spans(page, fitz.Rect(COLUMNS[1], top, COLUMNS[-1], bottom))
            numbers = [int(match[1]) for span in row if (match := LESSON.fullmatch(span['text']))]
            if numbers != [len(rows) + 1]:
                raise ValueError(f'Unexpected Lesson order on the original page {page.number + 1}')
            rows.append((top, bottom, row))
    if len(rows) != 160 or len(teaching_pages) != 40:
        raise ValueError('Expected 160 original lessons in 40 teaching tables')
    return rows, teaching_pages[0], teaching_pages[-1]


def teaching_plan(calendar, web):
    weeks = []
    for a, b in zip(calendar['A'], calendar['B'], strict=True):
        if a['week'] != b['week']:
            raise ValueError('The Group A and Group B weeks do not match')
        week = int(a['week'][1:])
        dates = [group[key] for group in (a, b) for key in ('start', 'end')]
        item = web.get(str(week))
        if item and item[:4] != dates:
            raise ValueError(f'Calendar dates differ from the Web at M{week:02d}')
        weeks.append((week, dates, item[4][''] if item else []))
    if [number for _, _, numbers in weeks for number in numbers] != list(range(1, 161)):
        raise ValueError('The published Web plan must contain Lessons 1–160 in order')
    if [week for week, _, numbers in weeks if not numbers] != [6, 19]:
        raise ValueError('Expected two complete closure weeks in the published Web plan')
    return weeks


def write(page, x, y, text, size=8, bold=False):
    font = 'LiberationSans-Bold' if bold else 'LiberationSans'
    page.insert_text((x, y), text, fontname=font, fontsize=size, color=INK)


def register_fonts(page, fonts):
    for name, file in FONTS.items():
        page.insert_font(fontname=name, fontfile=str(fonts / file))


def new_week(pdf, size, year, week, dates, numbers, rows, fonts):
    page = pdf.new_page(width=size.width, height=size.height)
    register_fonts(page, fonts)
    write(page, COLUMNS[0], 28, f'ENGLISH (SK)  |  YEAR {year}  |  RPT 2027', 10, True)
    page.draw_rect(fitz.Rect(COLUMNS[0], TABLE_TOP, COLUMNS[-1], CONTENT_TOP),
                   color=BORDER, fill=(0.976, 0.945, 0.777), width=0.6)
    headings = ('WEEK / DATE', 'LESSON / THEME / TOPIC',
                'CONTENT STANDARD / LEARNING STANDARD', 'REFERENCE / BBM')
    for x, heading in zip(COLUMNS, headings):
        write(page, x + 5, 61.5, heading, 8.5, True)
    y = CONTENT_TOP
    for number in numbers:
        top, bottom, row = rows[number - 1]
        for span in row:
            x, old_y = span['origin']
            colour = tuple(((span['color'] >> shift) & 255) / 255 for shift in (16, 8, 0))
            page.insert_text((x, y + old_y - top), span['text'], fontname=span['font'],
                             fontsize=span['size'], color=colour)
        y += bottom - top
        page.draw_line((COLUMNS[1], y), (COLUMNS[-1], y), color=BORDER, width=0.6)
        actual = spans(page, fitz.Rect(COLUMNS[1], y - (bottom - top), COLUMNS[-1], y))
        before = Counter(' '.join(span['text'] for span in row).split())
        after = Counter(' '.join(span['text'] for span in actual).split())
        if before != after:
            raise ValueError(f'Lesson wording changed for Year {year}, Lesson {number}: '
                             f'{before - after} / {after - before}')
    if y > CONTENT_BOTTOM:
        raise ValueError(f'Year {year} week {week} does not fit on one page')
    if not numbers:
        y += 71
    page.draw_rect(fitz.Rect(COLUMNS[0], CONTENT_TOP, COLUMNS[1], y),
                   color=BORDER, fill=(0.918, 0.945, 0.890), width=0.6)
    page.draw_rect(fitz.Rect(COLUMNS[0], TABLE_TOP, COLUMNS[-1], y), color=BORDER, width=0.6)
    for x in COLUMNS[1:-1]:
        edge = y if numbers or x == COLUMNS[1] else CONTENT_TOP
        page.draw_line((x, TABLE_TOP), (x, edge), color=BORDER, width=0.6)
    x, top = COLUMNS[0] + 5, CONTENT_TOP
    write(page, x, top + 13, f'WEEK {week:02d}', 9, True)
    label = f'{len(numbers)} Lessons {numbers[0]:03d}-{numbers[-1]:03d}' if numbers else 'School closed'
    write(page, x, top + 25, label, 8, True)
    formatted = [date.fromisoformat(day).strftime('%d/%m/%Y') for day in dates]
    write(page, x, top + 39, f'A  {formatted[0][:5]} - {formatted[1]}', 7)
    write(page, x, top + 51, f'B  {formatted[2][:5]} - {formatted[3]}', 7)
    if not numbers:
        holiday = ('Chinese New Year and KPM school holidays' if week == 6
                   else 'Hari Raya Aidiladha, Wesak and KPM school holidays')
        write(page, COLUMNS[1] + 5, CONTENT_TOP + 18, holiday, 9, True)
    write(page, COLUMNS[0], 568, 'Place each SOW Lesson using your class timetable and school holidays.', 8)
    write(page, COLUMNS[0], 580, 'One SOW Lesson represents 60 minutes of teaching.', 8)
    write(page, 768, 580, f'Page {page.number + 1}', 8)


def update_unit_summary(page, weeks, fonts):
    replacements = []
    for span in spans(page):
        match = UNIT_SUMMARY.fullmatch(span['text'])
        if not match:
            continue
        old_weeks = [int(week) for week in match[1].split(', ')]
        first, last = old_weeks[0] * 4 - 3, old_weeks[-1] * 4
        new_weeks = [f'{week:02d}' for week, _, ids in weeks if any(first <= n <= last for n in ids)]
        replacements.append((span, 'Weeks ' + ', '.join(new_weeks)))
        page.add_redact_annot(fitz.Rect(span['bbox']), fill=False, cross_out=False)
    if replacements:
        page.apply_redactions(images=0, graphics=0, text=0)
        register_fonts(page, fonts)
        for span, label in replacements:
            write(page, *span['origin'], label, span['size'])


def render(source, target, plan, year, fonts):
    with fitz.open(source) as original, fitz.open() as result:
        rows, first, last = lesson_rows(original)
        result.insert_pdf(original, from_page=0, to_page=first - 1, links=True)
        result.set_metadata(original.metadata)
        for page in list(result)[1:]:
            update_unit_summary(page, plan, fonts)
        for week, dates, numbers in plan:
            new_week(result, original[0].rect, year, week, dates, numbers, rows, fonts)
        if last + 1 < original.page_count:
            result.insert_pdf(original, from_page=last + 1, links=True)
        result.subset_fonts()
        result.save(target, garbage=4, deflate=True, clean=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('published_web_catalog', type=Path)
    parser.add_argument('original_pdfs', type=Path)
    parser.add_argument('--fonts', type=Path, default=Path('/usr/share/fonts/truetype/liberation'))
    args = parser.parse_args()
    root = Path('rpt_2027')
    calendar = json.loads((root / 'pendidikan_moral/induk_minggu_2027_ab.json').read_text())['weeks']
    catalog = json.loads(args.published_web_catalog.read_text())
    with TemporaryDirectory(dir=root / 'english') as temporary:
        outputs = []
        for year in range(2, 7):
            name = f'RPT_ENGLISH_TAHUN_{year}_2027_UNTUK_GURU.pdf'
            source = args.original_pdfs / name
            target = Path(temporary) / name
            plan = teaching_plan(calendar, catalog[f'ENGLISH:{year}'])
            render(source, target, plan, year, args.fonts)
            outputs.append((root / 'english' / name, target))
        for source, target in outputs:
            target.replace(source)


if __name__ == '__main__':
    main()
