"""Export the reviewed half-hour RPH for SK Mathematics Years 5 and 6."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from dlp_year2_rph import _pdf, _word
from rph_standalone.matematik.v60_source_loader import load_year
from staging.matematik.eksport_agihan import display_dates, read_agihan
from staging.matematik.eksport_rpt_dpk import export_table
from staging.matematik.rph_text import FIELD, STANDARD


DATA = Path(__file__).parent
UNITS = (
    'Nombor bulat dan operasi', 'Pecahan, perpuluhan dan peratus',
    'Wang', 'Masa dan waktu', 'Ukuran dan sukatan', 'Ruang',
    'Koordinat, nisbah dan kadaran', 'Pengurusan data',
)
PHASES = (
    ('Set induksi · 3 minit', 'Paparkan bahan dan minta murid kenal pasti maklumat yang diberi.',
     'Nyatakan maklumat yang akan digunakan dalam contoh.'),
    ('Penutup · 4 minit', 'Pilih satu jawapan individu dan semak langkah bersama kelas.',
     'Jelaskan satu langkah dan betulkan respons jika perlu.'),
)


def unit_name(year, unit):
    if (year, unit) == (6, 8):
        return 'Pengurusan data dan kebolehjadian'
    return UNITS[unit - 1]


@dataclass(frozen=True)
class Plan:
    lesson: int
    sp: str
    pages: str
    title: str
    materials: str
    model: str
    pupil_action: str
    task: str
    evidence: str

    @property
    def heading(self):
        return self.title[0].upper() + self.title[1:]


def load(year):
    draft = read_agihan()
    weeks = {str(row['minggu']): row for row in draft['takwim']}
    schedule = {n: weeks[week] for week, entries in draft['tahun'][str(year)]['minggu'].items()
                for n, minutes in entries if minutes == 30}
    sources = [dict(FIELD.findall(text)) for text in load_year(year)]
    path = DATA / f'tahun{year}' / 'slot_30_minit.tsv'
    plans = []
    for line in path.read_text(encoding='utf-8').splitlines():
        raw_lesson, *fields = line.split('|')
        plan = Plan(int(raw_lesson), *map(str.strip, fields))
        if not all(field.strip() for field in fields) or plan.lesson not in schedule:
            raise ValueError(f'Tahun {year} · Lesson {plan.lesson:03d} mempunyai kandungan atau agihan yang tidak sah.')
        original = STANDARD.findall(sources[plan.lesson - 1]['SP'])
        if original != [plan.sp]:
            raise ValueError(f'Tahun {year} · SP Lesson {plan.lesson:03d} berbeza daripada RPT.')
        plans.append(plan)
    if [plan.lesson for plan in plans] != list(schedule):
        raise ValueError(f'Tahun {year} mesti mempunyai tepat satu RPH untuk setiap slot 30 minit.')
    return plans, schedule, sources


def rpt_details(year, plans, sources):
    short = {plan.lesson: plan for plan in plans}
    details = {}
    for number, source in enumerate(sources, 1):
        sk = source['SK'].strip()
        unit = int(sk.split('.')[0])
        plan = short.get(number)
        title = plan.heading if plan else source['Tajuk'].strip()
        codes = ', '.join(STANDARD.findall(source['SP']))
        pages = plan.pages if plan else None
        evidence = plan.evidence if plan else 'Tugasan dan evidens PBD dalam semakan.'
        details[number] = (unit, unit_name(year, unit), title, sk, codes, None, None, pages, evidence)
    return details


def short_document(year, plan, week, source):
    unit = int(plan.sp.split('.')[0])
    sk = source['SK'].strip()
    heading = ('Rancangan Pengajaran Harian', f'Matematik SK Tahun {year} · 2027', plan.heading)
    details = [
        ('Unit', f'Unit {unit} {unit_name(year, unit)}'),
        ('Lesson / tempoh', f'Lesson {plan.lesson:03d} · 30 minit'),
        ('Tarikh RPT', f"M{week['minggu']:02d} · A {display_dates(week['A'])} · B {display_dates(week['B'])}"),
        ('Maklumat kelas', 'Kelas ______ · Tarikh ______ · Masa ______ · Murid ______'),
        ('SK / SP', f'SK {sk} · SP {plan.sp}'),
        ('Rujukan', f'DSKP Matematik Tahun {year} · Buku Teks SK, hlm. {plan.pages}'),
        ('Objektif', f'Murid dapat {plan.title} seperti diperincikan dalam evidens PBD.'),
        ('Bahan', plan.materials),
    ]
    activities = [
        ('Fasa', 'Tindakan guru', 'Tindakan murid'),
        PHASES[0],
        ('Aktiviti 1 · 10 minit', plan.model, plan.pupil_action),
        ('Aktiviti 2 / PBD · 13 minit', 'Edarkan tugasan dan rekod respons individu.', plan.task),
        PHASES[1],
    ]
    reflection = [
        ('Evidens PBD', plan.evidence),
        ('Refleksi', '___ / ___ murid mencapai objektif. Catat item untuk bimbingan susulan.'),
    ]
    return heading, details, activities, reflection


def export_plans(year, plans, schedule, sources, output):
    output.mkdir(parents=True, exist_ok=True)
    for plan in plans:
        parts = short_document(year, plan, schedule[plan.lesson], sources[plan.lesson - 1])
        stem = f'CikguLaju_Matematik_T{year}_Lesson_{plan.lesson:03d}'
        for extension, renderer in (('docx', _word), ('pdf', _pdf)):
            with (output / f'{stem}.{extension}').open('wb') as stream:
                renderer(stream, *parts)


def export(year, output):
    plans, schedule, sources = load(year)
    export_plans(year, plans, schedule, sources, output)
    export_table(
        output / f'CikguLaju_RPT_Matematik_SK_Tahun_{year}_2027_Semakan.pdf',
        year, rpt_details(year, plans, sources), kssr_dskp=True,
        review_note='42 sesi 30 minit sepadan dengan RPH. Kandungan 75 sesi 60 minit dalam semakan.',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tahun', required=True, type=int, choices=(5, 6))
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    export(args.tahun, args.output)
    print(f'RPT dan 42 RPH Matematik SK Tahun {args.tahun} dieksport.')


if __name__ == '__main__':
    main()
