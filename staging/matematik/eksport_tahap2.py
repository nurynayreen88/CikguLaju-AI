"""Export the complete SK Mathematics Years 4 to 6 review sets."""

import argparse
from collections import Counter
from pathlib import Path
import re

from dlp_year2_rph import _pdf, _word
from staging.matematik.eksport_agihan import display_dates, read_agihan
from staging.matematik.eksport_rpt_dpk import export_table
from staging.matematik.eksport_slot_30_tahap2 import DATA, export_plans, load, rpt_details, unit_name
from staging.matematik.rph_text import PHASE_MAP, STANDARD, existing_actions


def load_hour(year, schedule):
    source = DATA / f'tahun{year}' / 'slot_60_minit.tsv'
    lessons = {}
    for line in source.read_text(encoding='utf-8').splitlines():
        raw_number, pages, title, task, evidence, *replacement = line.split('|')
        number = int(raw_number)
        if number in lessons or len(replacement) not in (0, 1, 3) or not all(
            value.strip() for value in (pages, title, task, evidence, *replacement)
        ):
            raise ValueError(f'RPH Tahun {year} Lesson {number:03d} tidak lengkap atau berulang.')
        lessons[number] = (pages, title, task, evidence, replacement)
    if list(lessons) != [number for number, (_, minutes) in schedule.items() if minutes == 60]:
        raise ValueError(f'Senarai RPH 60 minit mesti sepadan dengan RPT Tahun {year}.')
    return lessons


def sentence_case(text):
    return re.sub(r'[.;]\s+([a-z])', lambda match: f'. {match[1].upper()}', text).rstrip(';')


def hour_document(year, number, week, source, lesson):
    pages, title, task, evidence, replacement = lesson
    minutes = 60
    standard = source['SK'].strip()
    unit = int(standard.partition('.')[0])
    codes = STANDARD.findall(source['SP'])
    if not codes or any(code.rsplit('.', 1)[0] != standard.split()[0] for code in codes):
        raise ValueError(f'Kod SK/SP Tahun {year} Lesson {number:03d} tidak sepadan.')
    heading = ('Rancangan Pengajaran Harian', f'Matematik SK Tahun {year} · 2027', title)
    if year == 4:
        original = re.split(r' dan (?:memberikan|menjawab) sekurang-kurangnya', source['Objektif'], maxsplit=1)[0]
        objective = re.sub(r'\s*\[SP [^\]]+\]', '', original).rstrip('. ')
        if number == 22:
            objective = 'Murid dapat menolak dua nombor serta menolak dua nombor daripada satu nombor melibatkan pecahan.'
    else:
        objective = f'Murid dapat {title[0].lower() + title[1:]} mengikut evidens PBD.'
    fields = [
        ('Unit', f'Unit {unit} {unit_name(year, unit)}'),
        ('Lesson / tempoh', f'Lesson {number:03d} · {minutes} minit'),
        ('Tarikh RPT', f"M{week['minggu']:02d} · A {display_dates(week['A'])} · B {display_dates(week['B'])}"),
        ('Maklumat kelas', 'Kelas ______ · Tarikh ______ · Masa ______ · Murid ______'),
        ('SK / SP', f"SK {standard} · SP {source['SP'].strip()}"),
        ('Rujukan', f'DSKP Matematik Tahun {year} · Buku Teks SK, hlm. {pages}'),
        ('Objektif', objective),
        ('Bahan', source['BBM']),
    ]
    phases = [source[key] for _, key, _, _ in PHASE_MAP]
    if replacement:
        phases[-len(replacement):] = replacement
    activities = [('Fasa', 'Tindakan guru', 'Tindakan murid')]
    for (label, _, teacher, pupil), text in zip(PHASE_MAP, phases, strict=True):
        actions = existing_actions(text.strip(), teacher, pupil)
        activities.append((label, *(sentence_case(action) for action in actions)))
    activities.extend([
        ('Pengukuhan / PBD · 10 minit', 'Berikan tugasan berikut dan semak hasil kerja individu.', task),
        ('Penutup · 5 minit', 'Semak satu respons dan bincangkan langkah pembetulan.',
         'Terangkan satu langkah dan betulkan respons jika perlu.'),
    ])
    reflection = [
        ('Evidens PBD', evidence),
        ('Refleksi', '___ / ___ murid mencapai objektif. Catat item untuk bimbingan susulan.'),
    ]
    return heading, fields, activities, reflection


def export_hour(year, sources, schedule, lessons, output):
    for number, lesson in lessons.items():
        week, _ = schedule[number]
        parts = hour_document(year, number, week, sources[number - 1], lesson)
        stem = f'CikguLaju_Matematik_T{year}_Lesson_{number:03d}'
        for extension, render in (('docx', _word), ('pdf', _pdf)):
            with (output / f'{stem}.{extension}').open('wb') as stream:
                render(stream, *parts, mathematics=True)


def full_schedule(year):
    draft = read_agihan()
    weeks = {str(week['minggu']): week for week in draft['takwim']}
    schedule = {
        lesson: (weeks[week], minutes)
        for week, sessions in draft['tahun'][str(year)]['minggu'].items()
        for lesson, minutes in sessions
    }
    if list(schedule) != list(range(1, 118)) or Counter(m for _, m in schedule.values()) != {30: 42, 60: 75}:
        raise ValueError(f'Agihan Tahun {year} mesti meliputi 117 Lesson dan 96 jam.')
    return schedule


def complete_rpt_details(year, short, hour, sources):
    details = rpt_details(year, short, sources)
    for number, (pages, title, _, evidence, _) in hour.items():
        unit, name, _, sk, sp, dpk, volume, _, _ = details[number]
        details[number] = (unit, name, title, sk, sp, dpk, volume, pages, evidence)
    return details


def export(year, output):
    schedule = full_schedule(year)
    hour = load_hour(year, schedule)
    short, short_schedule, sources = load(year)
    export_plans(year, short, short_schedule, sources, output)
    export_hour(year, sources, schedule, hour, output)
    details = complete_rpt_details(year, short, hour, sources)
    export_table(output / f'CikguLaju_RPT_Matematik_SK_Tahun_{year}_2027_Semakan.pdf',
                 year, details, kssr_dskp=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tahun', type=int, choices=(4, 5, 6), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    export(args.tahun, args.output)
    print(f'117 RPH dan RPT Matematik SK Tahun {args.tahun} dieksport.')


if __name__ == '__main__':
    main()
