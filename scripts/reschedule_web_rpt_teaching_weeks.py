"""Reassign the six remaining Web RPT subjects around 2027 school closures."""

from collections import Counter, defaultdict
from datetime import date
from hashlib import sha256
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import fitz

from .build_english_rpt_weekly_allocation import CALENDAR, CLOSED_WEEKS, FONT_DIR
from .build_web_rpt_weekly_suggestions import (
    LESSON, ROOT, RTL_SUBJECTS, SUBJECTS, WEEK, read_weeks,
)

SLUGS = ('bahasa_melayu', 'sains', 'pendidikan_islam', 'pendidikan_moral', 'pjpk', 'bahasa_arab')
AUDIT = Path('audits/rpt_2027_weekly_allocation_20261115.csv')
TOP, BOTTOM = 78.7, 556
LEFT, MARGIN = 35, 23
CELL_WIDTH = 105
GREEN, INK, LINE = (0.918, 0.945, 0.890), (0.15, 0.23, 0.31), (0.77, 0.81, 0.77)
SHORT = {1, 5, 20, 35}
FOUR_DAY = {2, 3, 8, 9, 10, 11, 12, 16, 17, 22, 24, 25, 26, 27, 30, 31, 33, 40}
REGULAR_CAP = {'BM': 5, 'SCIENCE': 3, 'PI': 4, 'MORAL': 3, 'ARAB': 2}
SHORT_CAP = {'BM': 3, 'SCIENCE': 2, 'PI': 3, 'MORAL': 2, 'ARAB': 2}
DEEPAVALI_CAP = {'BM': 2, 'SCIENCE': 2, 'PI': 2, 'MORAL': 2, 'ARAB': 1}
HOLIDAY = {6: 'Cuti Tahun Baharu Cina', 19: 'Cuti Aidiladha dan Hari Wesak'}


def weekly_capacity(subject, week):
    if week in CLOSED_WEEKS:
        return 0
    if week == 39:
        return DEEPAVALI_CAP[subject]
    if week in SHORT:
        return SHORT_CAP[subject]
    if week in FOUR_DAY and subject == 'BM':
        return 4
    return REGULAR_CAP[subject]


def allocate(subject, original):
    if subject == 'PJPK':
        result = {}
        next_week = 1
        for old_week, lessons in sorted(original.items()):
            week = max(next_week, old_week)
            while week in CLOSED_WEEKS:
                week += 1
            if week > 44 or any(len(ids) != 1 for ids in lessons.values()):
                raise ValueError('PJ and PK require separate, consecutive session sequences')
            result[week] = lessons
            next_week = week + 1
        return result

    # Keep all IDs in their original sequence. Minimize displacement from the
    # existing weekly plan within the subject's full and shortened-week caps.
    total = sum(len(ids['']) for ids in original.values())
    ideal_position = 0
    candidates = {0: (0, ())}
    for week in range(1, 45):
        old_count = len(original.get(week, {}).get('', ()))
        ideal_position += old_count
        revised = {}
        for start, (cost, counts) in candidates.items():
            for count in range(min(weekly_capacity(subject, week), total - start) + 1):
                end = start + count
                score = cost + abs(ideal_position - end) + 3 * abs(count - old_count)
                if end not in revised or score < revised[end][0]:
                    revised[end] = score, (*counts, count)
        candidates = revised
    if total not in candidates:
        raise ValueError(f'{subject}: the existing PdP do not fit the available weeks')
    result = {}
    start = 1
    for week, count in enumerate(candidates[total][1], 1):
        if count:
            result[week] = {'': list(range(start, start + count))}
            start += count
    return result


def body_rect(page, rtl):
    right = page.rect.width - MARGIN
    x0, x1 = (LEFT, right - CELL_WIDTH) if rtl else (LEFT + CELL_WIDTH, right)
    return fitz.Rect(x0, TOP, x1, BOTTOM)


def pdf_rows(pdf, rtl):
    rows = []
    for page in list(pdf)[1:]:
        body = body_rect(page, rtl)
        for draw in page.get_drawings():
            rect = draw['rect']
            if (draw['type'] != 'f' or abs(rect.x0 - LEFT) > 0.1
                    or abs(rect.x1 - (page.rect.width - MARGIN)) > 0.1 or rect.y0 < TOP - 0.1):
                continue
            row = fitz.Rect(body.x0, rect.y0, body.x1, rect.y1)
            topic = fitz.Rect(510 if rtl else body.x0, row.y0,
                              body.x1 if rtl else 300, row.y1)
            identities = [LESSON.fullmatch(s['text'].strip())
                          for block in page.get_text('dict', clip=topic)['blocks']
                          for line in block.get('lines', ()) for s in line['spans']
                          if abs(s['size'] - 8.1) < 0.05]
            matches = [m for m in identities if m]
            if len(matches) != 1:
                raise ValueError(f'Unexpected source row on page {page.number + 1}: {row}')
            match = matches[0]
            rows.append(((match[1] or '', int(match[2])), page.number, row))
    return rows


def print_week(page, rect, week, dates, font, closed=False):
    page.draw_rect(rect, fill=GREEN, color=LINE, width=0.5)
    lines = [f'M{week:02d} - Cuti sekolah' if closed else f'M{week:02d}', 'Kumpulan A:',
             ' - '.join(dates[:2]), 'Kumpulan B:', ' - '.join(dates[2:])]
    space = min(11.3, (rect.height - 12) / 4)
    first = rect.y0 + (rect.height - space * 4) / 2 + 2.5
    for index, value in enumerate(lines):
        width = font.text_length(value, fontsize=7)
        x = rect.x1 - width - 5 if rect.x0 > 500 else rect.x0 + 7
        page.insert_text((x, first + index * space), value, fontsize=7, fontname='RPTWeek', color=INK)


def isolate_clip(fragments, source, page_no, clip):
    fragments.insert_pdf(source, from_page=page_no, to_page=page_no, links=False, annots=False)
    page = fragments[-1]
    full = page.rect
    outside = (fitz.Rect(full.x0, full.y0, full.x1, clip.y0),
               fitz.Rect(full.x0, clip.y1, full.x1, full.y1),
               fitz.Rect(full.x0, clip.y0, clip.x0, clip.y1),
               fitz.Rect(clip.x1, clip.y0, full.x1, clip.y1))
    for rect in outside:
        if not rect.is_empty:
            page.add_redact_annot(rect, fill=False, cross_out=False)
    page.apply_redactions(images=0, graphics=2, text=0)
    return page.number


def add_page(pdf, bands, path_font):
    original = bands[0]
    rect = original.rect
    page = pdf.new_page(width=rect.width, height=rect.height)
    header = fitz.Rect(0, 0, rect.width, TOP)
    page.show_pdf_page(header, bands, 0, clip=header)
    footer = fitz.Rect(0, 558, 755, rect.height)
    page.show_pdf_page(footer, bands, 1, clip=footer)
    page.insert_font(fontname='RPTWeek', fontfile=str(path_font))
    page.insert_text((775, 576), f'Halaman {page.number + 1}', fontsize=7,
                     fontname='RPTWeek', color=INK)
    return page


def append_row(page, original, fragments, row_fragments, row, y, copied):
    _, source_page, clip = row
    target = fitz.Rect(clip.x0, y, clip.x1, y + clip.height)
    fragment = row_fragments[row[0]]
    page.show_pdf_page(target, fragments, fragment, clip=clip)
    for link in original[source_page].get_links():
        hot_area = link['from']
        if not clip.contains(hot_area):
            continue
        if link['kind'] != fitz.LINK_URI:
            raise ValueError('Teaching row contains an unexpected link type')
        moved = hot_area + (0, y - clip.y0, 0, y - clip.y0)
        page.insert_link({'kind': fitz.LINK_URI, 'uri': link['uri'], 'from': moved})
    page.draw_rect(target, color=LINE, width=0.4)
    copied.append((page.number, target, source_page, clip))
    return target.y1


def render(source, target, rtl, assignments, dates):
    path_font = FONT_DIR / 'DejaVuSans.ttf'
    font = fitz.Font(fontfile=str(path_font))
    with fitz.open(source) as original, fitz.open() as output, fitz.open() as fragments:
        rows = pdf_rows(original, rtl)
        week_for_row = {(component, num): week for week, plan in assignments.items()
                        for component, ids in plan.items() for num in ids}
        if len(rows) != len(week_for_row) or set(row[0] for row in rows) != week_for_row.keys():
            raise ValueError(f'{source}: allocation and source row IDs differ')
        groups = defaultdict(list)
        for row in rows:
            groups[week_for_row[row[0]]].append(row)
        output.insert_pdf(original, from_page=0, to_page=0)
        output.set_metadata(original.metadata)
        copied = []
        rect = original[1].rect
        isolate_clip(fragments, original, 1, fitz.Rect(0, 0, rect.width, TOP))
        isolate_clip(fragments, original, 1, fitz.Rect(0, 558, 755, rect.height))
        row_fragments = {identity: isolate_clip(fragments, original, page_no, clip)
                         for identity, page_no, clip in rows}
        page = add_page(output, fragments, path_font)
        y = TOP
        for week in sorted(assignments.keys() | HOLIDAY.keys()):
            body = body_rect(page, rtl)
            x = body.x1 if rtl else LEFT
            if week in HOLIDAY:
                height = 59
                if y + height > BOTTOM:
                    page, y = add_page(output, fragments, path_font), TOP
                page.draw_rect(fitz.Rect(body.x0, y, body.x1, y + height), color=LINE, width=0.5)
                page.insert_text((body.x0 + 9, y + 30), HOLIDAY[week], fontsize=9,
                                 fontname='RPTWeek', color=INK)
                print_week(page, fitz.Rect(x, y, x + CELL_WIDTH, y + height),
                           week, dates[week], font, closed=True)
                y += height
                continue
            pending = groups[week]
            height = sum(row[2].height for row in pending)
            if y > TOP and y + height > BOTTOM:
                page, y = add_page(output, fragments, path_font), TOP
            start = y
            for row in pending:
                if y + row[2].height > BOTTOM:
                    print_week(page, fitz.Rect(x, start, x + CELL_WIDTH, y), week, dates[week], font)
                    page, y = add_page(output, fragments, path_font), TOP
                    start = y
                if y + row[2].height > BOTTOM:
                    raise ValueError(f'{source}: one source row exceeds a page')
                y = append_row(page, original, fragments, row_fragments, row, y, copied)
            print_week(page, fitz.Rect(x, start, x + CELL_WIDTH, y), week, dates[week], font)
        output.save(target, garbage=4, deflate=True, clean=True)
        with fitz.open(target) as reopened:
            if original[0].get_pixmap().samples != reopened[0].get_pixmap().samples:
                raise ValueError(f'{source}: cover changed')
            for page_no, clip, old_no, old_clip in copied:
                before = original[old_no].get_text(clip=old_clip)
                after = reopened[page_no].get_text(clip=clip)
                if before != after:
                    raise ValueError(f'{source}: text changed after moving row from p{old_no + 1}: '
                                     f'{before[:55]!r} / {after[:55]!r}')
            links_before = Counter(link['uri'] for p in original for link in p.get_links())
            links_after = Counter(link['uri'] for p in reopened for link in p.get_links())
            if links_before != links_after:
                raise ValueError(f'{source}: source links changed')
            return reopened.page_count


def update_audit(allocation):
    with AUDIT.open(encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)
        fields, records = reader.fieldnames, list(reader)
    for record in records:
        weeks = allocation.get((record['Subjek'], record['Tahun']))
        if weeks is None:
            continue
        component = record['Komponen']
        counts = {week: len(weeks.get(week, {}).get(component, ())) for week in range(1, 45)}
        record['Jumlah bernombor calon'] = str(sum(counts.values()))
        record['Agihan calon (PdP × minggu)'] = ' | '.join(
            f'{count} PdP × {freq}' for count, freq in sorted(Counter(counts.values()).items()))
        for week in (6, 19, 39):
            record[f'M{week:02d} calon'] = str(counts[week])
        record['Status'] = 'Agihan cuti penuh disemak'
    with AUDIT.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def main():
    calendar = json.loads(CALENDAR.read_text(encoding='utf-8'))['weeks']
    iso = {n: tuple(g[n - 1][field] for g in (calendar['A'], calendar['B'])
                   for field in ('start', 'end')) for n in range(1, 45)}
    dates = {n: [date.fromisoformat(value).strftime('%d/%m/%Y') for value in pair]
             for n, pair in iso.items()}
    manifest_path = ROOT / 'manifest.json'
    cover_path = ROOT / 'original_cover_layout_verified.json'
    manifest = json.loads(manifest_path.read_text())
    cover = json.loads(cover_path.read_text())
    allocations = {}
    with TemporaryDirectory(dir=ROOT) as folder:
        outputs = []
        for key, record in manifest['files'].items():
            slug, year = key.split(':')
            if slug not in SLUGS:
                continue
            path = ROOT / record['path']
            code = SUBJECTS[slug]
            digest = sha256(path.read_bytes()).hexdigest()
            if digest != record['sha256'] or digest != cover['source_sha256_by_subject_year'][key]:
                raise ValueError(f'Source and cover hashes disagree for {path}')
            _, old = read_weeks(path, code)
            if not (CLOSED_WEEKS.keys() & old.keys()):
                continue
            new = allocate(code, old)
            candidate = Path(folder) / f'{slug}_{year}.pdf'
            pages = render(path, candidate, code in RTL_SUBJECTS, new, dates)
            published_dates, published = read_weeks(candidate, code)
            if published != new or published_dates != {w: iso[w] for w in new}:
                raise ValueError(f'The new PDF does not match the proposed allocation for {path}')
            data = candidate.read_bytes()
            digest = sha256(data).hexdigest()
            manifest['pages'] += pages - record['pages']
            record.update(bytes=len(data), pages=pages, sha256=digest,
                          full_school_closures_rescheduled=True)
            cover['source_sha256_by_subject_year'][key] = digest
            outputs.append((candidate, path))
            allocations[code, year] = new
            print(f'{key}: {pages} pages, {sum(len(ids) for week in new.values() for ids in week.values())} PdP',
                  flush=True)
        if outputs:
            for candidate, path in outputs:
                candidate.replace(path)
            for path, data in ((manifest_path, manifest), (cover_path, cover)):
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            update_audit(allocations)


if __name__ == '__main__':
    main()
