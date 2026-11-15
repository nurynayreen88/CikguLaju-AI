"""Reflow the five English Web RPTs using the 2027 KPM teaching windows."""
from collections import Counter
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory

import fitz

from .build_web_rpt_weekly_suggestions import ROOT, read_weeks


CALENDAR = Path('rpt_2027/pendidikan_moral/induk_minggu_2027_ab.json')
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
CLOSED_WEEKS = {6: 'Chinese New Year and KPM school holidays',
                19: 'Hari Raya Aidiladha, Wesak and KPM school holidays'}
THREE_LESSON_WEEKS = {1, 5, 10, 11, 20, 35}
TWO_LESSON_WEEKS = {39}
LEFT, TOP, BOTTOM = 35, 78.7, 556
COLUMNS = (LEFT, 140, 320, 445, 655, 818.89)
INK = (0.15, 0.23, 0.31)
BORDER = (0.77, 0.81, 0.77)
WEEK_FILL = (0.918, 0.945, 0.890)
ROW_FILL = (0.988, 0.988, 0.973)
HEADER_FILL = (1, 0.957, 0.733)


def teaching_plan():
    calendar = json.loads(CALENDAR.read_text(encoding='utf-8'))['weeks']
    if any(len(calendar[group]) != 44 for group in ('A', 'B')):
        raise ValueError('Expected 44 paired teaching windows in the KPM calendar')
    start = 1
    result = []
    for week, (group_a, group_b) in enumerate(zip(calendar['A'], calendar['B']), 1):
        if group_a['week'] != group_b['week'] or group_a['week'] != f'M{week:02d}':
            raise ValueError(f'Misaligned teaching window {week}')
        dates = tuple(group[key] for group in (group_a, group_b) for key in ('start', 'end'))
        count = (0 if week in CLOSED_WEEKS else 2 if week in TWO_LESSON_WEEKS
                 else 3 if week in THREE_LESSON_WEEKS else 4)
        end = start + count
        result.append((week, dates, list(range(start, end))))
        start = end
    if start != 161:
        raise ValueError('The English plan must cover Lessons 001–160')
    return result


def get_source_rows(doc):
    rows = []
    for page in list(doc)[1:]:
        rects = [d['rect'] for d in page.get_drawings()
                 if d['type'] == 'f' and abs(d['rect'].width - (COLUMNS[-1] - LEFT)) < 0.1
                 and d['rect'].y0 > TOP - 0.1 and d['rect'].height > 35]
        for rect in rects:
            clip = fitz.Rect(COLUMNS[1], rect.y0, rect.x1, rect.y1)
            spans = [s for b in page.get_text('dict', clip=clip)['blocks']
                     for line in b.get('lines', ()) for s in line['spans']]
            heading = [s['text'] for s in spans if re.fullmatch(r'Lesson \d{3}', s['text'])]
            if heading != [f'Lesson {len(rows) + 1:03d}']:
                raise ValueError(f'Unexpected source English row on page {page.number + 1}: {heading}')
            rows.append((rect, spans))
    if len(rows) != 160:
        raise ValueError(f'Expected 160 source rows, found {len(rows)}')
    return rows


def new_page(pdf, width, height, year):
    page = pdf.new_page(width=width, height=height)
    page.insert_font(fontname='RPTRegular', fontfile=str(FONT_DIR / 'DejaVuSans.ttf'))
    page.insert_font(fontname='RPTBold', fontfile=str(FONT_DIR / 'DejaVuSans-Bold.ttf'))
    page.draw_line((29, 32), (width - 29, 32), color=BORDER, width=0.5)
    page.draw_line((29, 564), (width - 29, 564), color=BORDER, width=0.5)
    write(page, 29, 24, f'ENGLISH (SK)  |  YEAR {year}  |  RPT 2027', bold=True)
    write(page, 29, 574, 'SOW Lessons follow the weekly date ranges. Use your class timetable to place each Lesson.', size=7)
    write(page, 29, 586, 'Four SOW Lessons need 240 minutes. Adjust the plan if your class slots provide less teaching time.', size=7)
    write(page, 775, 574, f'Page {page.number + 1}', size=7)
    page.draw_rect(fitz.Rect(LEFT, 49, COLUMNS[-1], TOP), fill=HEADER_FILL, color=BORDER, width=0.5)
    for x, title in zip(COLUMNS, ('WEEK / DATE', 'UNIT / TOPIC / LESSON', 'CONTENT STANDARD', 'LEARNING STANDARD', 'NOTES / MATERIALS')):
        write(page, x + 7, 66, title, bold=True)
        page.draw_line((x, 49), (x, TOP), color=BORDER, width=0.5)
    return page


def write(page, x, y, value, *, size=8, bold=False, color=INK):
    page.insert_text((x, y), value, fontsize=size,
                     fontname='RPTBold' if bold else 'RPTRegular', color=color)


def draw_rows(page, y, rows):
    for source_rect, spans in rows:
        height = source_rect.height
        page.draw_rect(fitz.Rect(COLUMNS[1], y, COLUMNS[-1], y + height),
                       color=BORDER, fill=ROW_FILL, width=0.5)
        for x in COLUMNS[2:-1]:
            page.draw_line((x, y), (x, y + height), color=BORDER, width=0.5)
        for span in spans:
            x, source_y = span['origin']
            color = tuple(((span['color'] >> shift) & 255) / 255 for shift in (16, 8, 0))
            write(page, x, y + source_y - source_rect.y0, span['text'], size=span['size'],
                  bold='Bold' in span['font'], color=color)
        y += height
    return y


def draw_week(page, top, bottom, week, dates, lessons):
    rect = fitz.Rect(LEFT, top, COLUMNS[1], bottom)
    page.draw_rect(rect, color=None, fill=WEEK_FILL)
    page.draw_rect(rect, color=BORDER, width=0.5)
    write(page, LEFT + 7, top + 12, f'M{week:02d}', bold=True)
    if lessons:
        label = f'{len(lessons)} Lessons {lessons[0]:03d}-{lessons[-1]:03d}'
    else:
        label = 'School closed'
    write(page, LEFT + 7, top + 22, label, size=7, bold=True)
    formatted = [date.fromisoformat(value).strftime('%d/%m/%Y') for value in dates]
    for offset, group in ((0, 'A'), (2, 'B')):
        write(page, LEFT + 7, top + 34 + 5 * offset,
              f'{group}  {formatted[offset]} - {formatted[offset + 1]}', size=6.7)


def render(source, destination, year, plan):
    with fitz.open(source) as original, fitz.open() as result:
        rows = get_source_rows(original)
        result.insert_pdf(original, from_page=0, to_page=0)
        result.set_metadata(original.metadata)
        width, height = original[0].rect.br
        page = new_page(result, width, height, year)
        y = TOP
        for week, dates, lessons in plan:
            pending = [rows[number - 1] for number in lessons]
            total_height = sum(rect.height for rect, _ in pending) or 62
            if y > TOP and y + total_height > BOTTOM:
                page = new_page(result, width, height, year)
                y = TOP
            if not pending:
                page.draw_rect(fitz.Rect(COLUMNS[1], y, COLUMNS[-1], y + 62),
                               color=BORDER, fill=ROW_FILL, width=0.5)
                write(page, COLUMNS[1] + 7, y + 24, CLOSED_WEEKS[week], bold=True)
                draw_week(page, y, y + 62, week, dates, lessons)
                y += 62
                continue
            while pending:
                fitting = []
                used = y
                for row in pending:
                    height_needed = row[0].height
                    if used + height_needed > BOTTOM:
                        break
                    fitting.append(row)
                    used += height_needed
                if not fitting:
                    raise ValueError(f'English row does not fit on a page for M{week:02d}')
                end = draw_rows(page, y, fitting)
                draw_week(page, y, end, week, dates, lessons)
                y = end
                pending = pending[len(fitting):]
                if pending:
                    page = new_page(result, width, height, year)
                    y = TOP
        result.subset_fonts()
        result.save(destination, garbage=4, deflate=True, clean=True)

    with fitz.open(destination) as updated, fitz.open(source) as original:
        before = Counter(span['text'] for _, row in get_source_rows(original) for span in row)
        after = Counter(span['text'] for page in list(updated)[1:]
                        for b in page.get_text('dict')['blocks'] for line in b.get('lines', ())
                        for span in line['spans']
                        if COLUMNS[1] <= span['origin'][0] <= COLUMNS[-1] and TOP < span['origin'][1] < BOTTOM
                        and span['text'] not in CLOSED_WEEKS.values())
        if before != after:
            raise ValueError(f'English Year {year} content changed: {before - after}, {after - before}')
        if original[0].get_pixmap().samples != updated[0].get_pixmap().samples:
            raise ValueError(f'English Year {year} cover changed visually')
        return updated.page_count


def update_english_pdfs():
    manifest_path = ROOT / 'manifest.json'
    cover_path = ROOT / 'original_cover_layout_verified.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    cover = json.loads(cover_path.read_text(encoding='utf-8'))
    plan = teaching_plan()
    with TemporaryDirectory(dir=ROOT) as temporary:
        pending = []
        for year in range(2, 7):
            key = f'english:{year}'
            record = manifest['files'][key]
            source = ROOT / record['path']
            digest = sha256(source.read_bytes()).hexdigest()
            if digest != record['sha256'] or digest != cover['source_sha256_by_subject_year'][key]:
                raise ValueError(f'Unexpected source or cover hash for {source}')
            if record.get('weekly_allocation_20261115'):
                continue
            target = Path(temporary) / source.name
            pages = render(source, target, year, plan)
            dates, weeks = read_weeks(target, 'ENGLISH')
            if dates != {week: window for week, window, ids in plan if ids}:
                raise ValueError(f'Incorrect dates for {source}')
            if dict(weeks) != {week: {'': ids} for week, _, ids in plan if ids}:
                raise ValueError(f'Incorrect Lesson ranges for {source}')
            raw = target.read_bytes()
            digest = sha256(raw).hexdigest()
            manifest['pages'] += pages - record['pages']
            record.update(sha256=digest, pages=pages, bytes=len(raw), weekly_allocation_20261115=True)
            cover['source_sha256_by_subject_year'][key] = digest
            pending.append((target, source))
        if pending:
            for target, source in pending:
                target.replace(source)
            for path, data in ((manifest_path, manifest), (cover_path, cover)):
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    update_english_pdfs()
