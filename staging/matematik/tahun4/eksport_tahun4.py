"""Export the complete SK Mathematics Year 4 RPT and 117 review lesson plans."""

import argparse
from collections import Counter
import csv
from pathlib import Path
import re

from dlp_year2_rph import _pdf, _word
from rph_standalone.matematik.v60_source_loader import load_year
from staging.matematik.eksport_agihan import display_dates, read_agihan
from staging.matematik.eksport_rpt_dpk import export_table
from staging.matematik.tahun4 import eksport_slot_30 as slot_30


SOURCE = Path(__file__).with_name('slot_60_minit.tsv')
YEAR = 4
FIELD = re.compile(r'^\*\*(.+?):\*\* (.+)$', flags=re.MULTILINE)
STANDARD = re.compile(r'\b\d+\.\d+\.\d+(?=\s+—)')
TEACHER_ACTION = re.compile(r'(?<!\w)(?:Guru|guru) ')
ACTOR_BOUNDARY = re.compile(r'(?<=[.;])\s+(?=[Mm]urid |[Mm]ereka |[Gg]uru |Secara berpasangan, murid )')
PHASE_MAP = (
    ('Set induksi · 5 minit', 'Set induksi (5 minit)',
     'Paparkan rangsangan yang sesuai dan periksa pengetahuan awal.', 'Perhatikan rangsangan dan jawab soalan secara lisan.'),
    ('Aktiviti 1 · 20 minit', 'Aktiviti 1 — Penerokaan/Model (20 minit)',
     'Tunjukkan satu contoh dengan bahan yang disediakan.', 'Ikuti contoh dan jelaskan satu langkah menggunakan model.'),
    ('Aktiviti 2 · 20 minit', 'Aktiviti 2 — Aplikasi/Latihan (20 minit)',
     'Pantau latihan dan semak langkah atau hasil bersama murid.', 'Gunakan contoh berpandu untuk menyiapkan latihan.'),
)


def load():
    agihan = read_agihan()
    weeks = {str(week['minggu']): week for week in agihan['takwim']}
    schedule = {number: (weeks[week], minutes)
                for week, sessions in agihan['tahun'][str(YEAR)]['minggu'].items()
                for number, minutes in sessions}
    if list(schedule) != list(range(1, 118)) or Counter(minutes for _, minutes in schedule.values()) != {30: 42, 60: 75}:
        raise ValueError('Agihan Tahun 4 mesti meliputi 117 Lesson dan 96 jam.')

    with SOURCE.open(encoding='utf-8', newline='') as file:
        rows = list(csv.reader(file, delimiter='|'))
    plans_60 = {}
    for raw_number, textbook, task, evidence in rows:
        number = int(raw_number)
        if number in plans_60 or not all((textbook.strip(), task.strip(), evidence.strip())):
            raise ValueError(f'RPH Tahun 4 Lesson {number:03d} tidak lengkap atau berulang.')
        plans_60[number] = (textbook, task, evidence)
    if list(plans_60) != [number for number, (_, minutes) in schedule.items() if minutes == 60]:
        raise ValueError('Senarai RPH 60 minit mesti sepadan dengan RPT Tahun 4.')

    short_rows, short_schedule = slot_30.load()
    plans_30 = {number: (codes, textbook, title, evidence)
                for number, codes, textbook, title, _, _, evidence in short_rows}
    originals = {number: dict(FIELD.findall(text)) for number, text in enumerate(load_year(YEAR), 1)}
    details = {}
    for number, fields in originals.items():
        standard = fields['SK'].strip()
        unit = int(standard.partition('.')[0])
        unit_name = slot_30.UNITS[unit - 1][1]
        codes = STANDARD.findall(fields['SP'])
        if not codes or any(not code.startswith(f'{unit}.') for code in codes):
            raise ValueError(f'Kod SP sumber tidak lengkap untuk Lesson {number:03d}.')
        title = fields['Tajuk'].strip()
        if number in plans_30:
            short_codes, textbook, title, evidence = plans_30[number]
            if short_codes != codes:
                raise ValueError(f'Kod SP RPH 30 minit berubah pada Lesson {number:03d}.')
        else:
            textbook, _, evidence = plans_60[number]
        details[number] = (unit, unit_name, title, standard, ', '.join(codes), None, None, textbook, evidence)
    return originals, schedule, plans_60, short_rows, short_schedule, details


def existing_actions(text, default_teacher, default_pupil):
    teacher, pupil = [], []
    for sentence in ACTOR_BOUNDARY.split(text):
        if TEACHER_ACTION.match(sentence):
            teacher.append(sentence[5:])
        else:
            pupil.append(sentence.removeprefix('Murid ').removeprefix('murid '))
    teacher_text = ' '.join(teacher) or default_teacher
    pupil_text = ' '.join(pupil) or default_pupil
    return teacher_text[0].upper() + teacher_text[1:], pupil_text[0].upper() + pupil_text[1:]


def export_hour_plans(originals, schedule, plans, details, output):
    output.mkdir(parents=True, exist_ok=True)
    for number, (textbook, task, evidence) in plans.items():
        unit, unit_name, title, sk, sp, *_ = details[number]
        source = originals[number]
        week, minutes = schedule[number]
        objective = source['Objektif'].split(' dan memberikan sekurang-kurangnya', 1)[0].rstrip('.')
        heading = ('Rancangan Pengajaran Harian', 'Matematik SK Tahun 4 · Draf semakan guru', title)
        fields = [
            ('Unit', f'Unit {unit} {unit_name}'),
            ('Lesson / tempoh', f'Lesson {number:03d} · {minutes} minit'),
            ('Tarikh RPT', f"M{week['minggu']:02d} · A {display_dates(week['A'])} · B {display_dates(week['B'])}"),
            ('Maklumat kelas', 'Kelas ______ · Tarikh ______ · Masa ______ · Murid ______'),
            ('SK / SP', f'SK {sk} · SP {sp}'),
            ('Rujukan', f'DSKP Matematik Tahun 4 · Buku Teks SK, hlm. {textbook}'),
            ('Objektif', f'{objective} mengikut evidens PBD.'),
            ('Bahan', source['BBM']),
        ]
        activities = [('Fasa', 'Tindakan guru', 'Tindakan murid')]
        activities.extend((label, *existing_actions(source[key], teacher, pupil))
                          for label, key, teacher, pupil in PHASE_MAP)
        activities.extend([
            ('Pengukuhan / PBD · 10 minit', 'Paparkan tugasan. Rekod hasil kerja individu.', task),
            ('Penutup · 5 minit', 'Semak satu respons PBD dan tunjuk cara menambah baik jawapan.',
             'Jelaskan satu langkah yang digunakan dan betulkan respons jika perlu.'),
        ])
        reflection = [
            ('Evidens PBD', evidence),
            ('Refleksi', '___ / ___ murid mencapai objektif. Catat item yang perlu diajar semula.'),
        ]
        for extension, render in (('docx', _word), ('pdf', _pdf)):
            with (output / f'CikguLaju_Matematik_T4_Lesson_{number:03d}.{extension}').open('wb') as stream:
                render(stream, heading, fields, activities, reflection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    originals, schedule, plans, short_rows, short_schedule, details = load()
    slot_30.export(short_rows, short_schedule, args.output)
    export_hour_plans(originals, schedule, plans, details, args.output)
    export_table(args.output / 'CikguLaju_RPT_Matematik_SK_Tahun_4_2027_Semakan.pdf', YEAR, details, kssr_dskp=True)
    print('117 RPH dan RPT Matematik SK Tahun 4 dieksport.')


if __name__ == '__main__':
    main()
