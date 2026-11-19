"""Validate and export SK Mathematics Year 2 Unit 1 for DPK Edisi 3."""

import argparse
import json
from pathlib import Path

from dlp_year2_rph import _pdf, _word
from staging.matematik.eksport_agihan import display_dates, read_agihan


SOURCE = Path(__file__).with_name('unit_01.json')
SUBTITLE = 'Matematik SK Tahun 2 · 2027'
PHASES = ('Set induksi', 'Aktiviti 1', 'Aktiviti 2 / PBD', 'Penutup')
MINUTES = {30: (5, 10, 12, 3), 60: (5, 25, 25, 5)}
STANDARDS = {
    '1.1': 'Nilai nombor', '1.2': 'Nilai tempat', '1.3': 'Pola nombor',
    '1.4': 'Menganggar', '1.5': 'Membundarkan nombor',
}
SP_PAGES = {
    '1.1.1(i)': '19', '1.1.1(ii)': '19', '1.1.2': '20', '1.1.3': '20',
    '1.2.1': '20–21', '1.3.1': '21', '1.3.2': '21', '1.4.1': '21', '1.5.1': '22',
}


def load():
    plans = json.loads(SOURCE.read_text(encoding='utf-8'))
    agihan = read_agihan()
    weeks = {str(row['minggu']): row for row in agihan['takwim']}
    schedule = {number: (weeks[week], minutes) for week, lessons in agihan['tahun']['2']['minggu'].items()
                for number, minutes in lessons}
    if [p['lesson'] for p in plans] != list(range(1, 15)):
        raise ValueError('Unit 1 mesti mengandungi Lesson 001–014.')
    if {code for p in plans for code in p['sp']} != SP_PAGES.keys():
        raise ValueError('Semak liputan kod SP Edisi 3 Unit 1.')
    for plan in plans:
        if not all(SP_PAGES[code] == plan['dpk'] for code in plan['sp']):
            raise ValueError(f"Halaman rujukan DPK tidak sepadan pada Lesson {plan['lesson']:03d}.")
        if len(plan['aktiviti']) != 4 or any(len(pair) != 2 or not all(pair) for pair in plan['aktiviti']):
            raise ValueError(f"Fasa guru dan murid tidak lengkap pada Lesson {plan['lesson']:03d}.")
        if not plan['evidens'].strip():
            raise ValueError(f"Evidens PBD tidak lengkap pada Lesson {plan['lesson']:03d}.")
    if [(p['lesson'], schedule[p['lesson']][1]) for p in plans if schedule[p['lesson']][1] < 60] != [(14, 30)]:
        raise ValueError('Semak tempoh Lesson Unit 1 jika agihan RPT berubah.')
    return plans, schedule


def document(plan, slot):
    week, minutes = slot
    number = plan['lesson']
    heading = ('Rancangan Pengajaran Harian', SUBTITLE, plan['tajuk'])
    standard_code = plan['sp'][0].rsplit('.', 1)[0]
    details = [
        ('Unit', 'Unit 1 Nombor hingga 1000'),
        ('Lesson / tempoh', f'Lesson {number:03d} · {minutes} minit'),
        ('Tarikh RPT', f"M{week['minggu']:02d} · A {display_dates(week['A'])} · B {display_dates(week['B'])}"),
        ('Maklumat kelas', 'Kelas ______ · Tarikh ______ · Masa ______ · Murid ______'),
        ('SK / SP', f"SK {standard_code} {STANDARDS[standard_code]} · SP {', '.join(plan['sp'])}"),
        ('Rujukan', f"DPK Edisi 3, hlm. {plan['dpk']} · Buku Teks Jilid 1, hlm. {plan['bt']}"),
        ('Objektif', plan['objektif']),
        ('Bahan', plan['bbm']),
    ]
    activities = [('Fasa', 'Tindakan guru', 'Tindakan murid')]
    activities.extend((f'{phase} · {length} minit', teacher, pupils)
                      for phase, length, (teacher, pupils) in zip(PHASES, MINUTES[minutes], plan['aktiviti'], strict=True))
    reflection = [
        ('Evidens PBD', plan['evidens']),
        ('Refleksi', '___ / ___ murid mencapai objektif.'),
        ('Susulan', plan['susulan']),
    ]
    return heading, details, activities, reflection


def export(plans, schedule, output):
    output.mkdir(parents=True, exist_ok=True)
    for plan in plans:
        number = plan['lesson']
        parts = document(plan, schedule[number])
        for extension, renderer in (('docx', _word), ('pdf', _pdf)):
            with (output / f'CikguLaju_Matematik_T2_Lesson_{number:03d}.{extension}').open('wb') as stream:
                renderer(stream, *parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Export 14 RPH in Word and PDF.')
    args = parser.parse_args()
    plans, schedule = load()
    export(plans, schedule, args.output)
    print('14 Lesson disemak dan dieksport. Lesson 014 menggunakan 30 minit.')


if __name__ == '__main__':
    main()
