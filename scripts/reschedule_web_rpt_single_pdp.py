"""Move weekly Music and RBT sessions out of full school closures."""

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import fitz

from .build_english_rpt_weekly_allocation import CALENDAR, FONT_DIR
from .build_web_rpt_weekly_suggestions import DATE, ROOT, SUBJECTS, WEEK, read_weeks


def teaching_weeks(subject, original_weeks):
    if subject == 'muzik':
        return [week for week in range(1, 45) if week not in {6, 19}][:len(original_weeks)]
    shifts = {19: 20, 20: 21, 21: 22, 39: 40, 40: 41, 41: 42}
    return [shifts.get(week, week) for week in original_weeks]


def update_dates(pdf, moves, expected_dates):
    for page in list(pdf)[1:]:
        replacements = []
        for drawing in page.get_drawings():
            cell = drawing['rect']
            if (drawing['type'] not in ('f', 'fs') or abs(cell.x0 - 35) > 0.1
                    or abs(cell.width - 105) > 0.1):
                continue
            lines = [span for block in page.get_text('dict', clip=cell)['blocks']
                     for line in block.get('lines', ()) for span in line['spans']]
            number = next(int(m[1]) for span in lines if (m := WEEK.fullmatch(span['text'].strip())))
            target = moves[number]
            if target == number:
                continue
            dates = expected_dates[target]
            dates_printed = iter((' - '.join(dates[:2]), ' - '.join(dates[2:])))
            for span in lines:
                value = span['text'].strip()
                if WEEK.fullmatch(value):
                    text = f'M{target:02d}'
                elif len(DATE.findall(value)) == 2:
                    text = next(dates_printed)
                else:
                    continue
                replacements.append((span, text))
                page.add_redact_annot(fitz.Rect(span['bbox']), fill=False, cross_out=False)
        if replacements:
            page.apply_redactions(images=0, graphics=0, text=0)
            page.insert_font(fontname='rptdates', fontfile=str(FONT_DIR / 'DejaVuSans.ttf'))
            for span, text in replacements:
                colour = tuple(((span['color'] >> shift) & 255) / 255 for shift in (16, 8, 0))
                page.insert_text(span['origin'], text, fontsize=span['size'],
                                 fontname='rptdates', color=colour)


def main():
    windows = json.loads(CALENDAR.read_text())['weeks']
    iso_dates = {i: tuple(g[key] for g in (a, b) for key in ('start', 'end'))
                 for i, (a, b) in enumerate(zip(windows['A'], windows['B'], strict=True), 1)}
    dates = {week: [date.fromisoformat(d).strftime('%d/%m/%Y') for d in values]
             for week, values in iso_dates.items()}
    manifest_path = ROOT / 'manifest.json'
    cover_path = ROOT / 'original_cover_layout_verified.json'
    manifest = json.loads(manifest_path.read_text())
    covers = json.loads(cover_path.read_text())
    with TemporaryDirectory(dir=ROOT) as folder:
        pending = []
        for key, item in manifest['files'].items():
            subject = key.split(':')[0]
            if subject not in {'muzik', 'rbt'}:
                continue
            source = ROOT / item['path']
            previous_hash = sha256(source.read_bytes()).hexdigest()
            if previous_hash != item['sha256'] or previous_hash != covers['source_sha256_by_subject_year'][key]:
                raise ValueError(f'Manifest does not match {key}')
            code = SUBJECTS[subject]
            _, lessons = read_weeks(source, code)
            if not ({6, 19, 39} & lessons.keys()):
                continue
            if any(len(content['']) != 1 for content in lessons.values()):
                raise ValueError(f'Expected a single PdP per teaching week for {key}')
            original_weeks = sorted(lessons)
            moves = dict(zip(original_weeks, teaching_weeks(subject, original_weeks), strict=True))
            if len(set(moves.values())) != len(moves) or {6, 19, 39}.intersection(moves.values()):
                raise ValueError(f'Invalid holiday allocation for {key}')
            candidate = Path(folder) / (key.replace(':', '_') + '.pdf')
            with fitz.open(source) as pdf:
                text_before = [page.get_text(clip=fitz.Rect(140, 49, page.rect.width, 556))
                               for page in list(pdf)[1:]]
                cover_before = pdf[0].get_pixmap().samples
                update_dates(pdf, moves, dates)
                pdf.subset_fonts()
                pdf.save(candidate, garbage=4, deflate=True)
            with fitz.open(candidate) as pdf:
                assert cover_before == pdf[0].get_pixmap().samples, key
                assert text_before == [page.get_text(clip=fitz.Rect(140, 49, page.rect.width, 556))
                                       for page in list(pdf)[1:]], key
            new_dates, new_lessons = read_weeks(candidate, code)
            assert new_dates == {target: iso_dates[target] for target in moves.values()}, key
            assert new_lessons == {moves[week]: content for week, content in lessons.items()}, key
            data = candidate.read_bytes()
            updated = sha256(data).hexdigest()
            item.update(sha256=updated, bytes=len(data))
            covers['source_sha256_by_subject_year'][key] = updated
            pending.append((source, candidate))
        for source, candidate in pending:
            candidate.replace(source)
        if pending:
            for path, data in ((manifest_path, manifest), (cover_path, covers)):
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
