"""Export the 42 Year 4 SK Mathematics half-hour RPH for teacher review."""

import argparse
from pathlib import Path

from dlp_year2_rph import _pdf, _word
from staging.matematik.eksport_agihan import display_dates, read_agihan


SOURCE = Path(__file__).with_name('slot_30_minit.tsv')
UNITS = (
    (21, 'Nombor dan operasi', 'Kad nombor, garis nombor dan carta tempat'),
    (40, 'Pecahan, perpuluhan dan peratus', 'Jalur pecahan dan petak seratus'),
    (61, 'Wang', 'Wang contoh, kad situasi dan bahan bergambar'),
    (73, 'Masa dan waktu', 'Jam model dan garis masa'),
    (92, 'Panjang, jisim dan isi padu cecair', 'Alat ukur, model sukatan dan kad unit'),
    (100, 'Ruang', 'Grid, pembaris dan model bentuk'),
    (108, 'Koordinat, nisbah dan kadaran', 'Grid koordinat dan kad nilai'),
    (117, 'Pengurusan data', 'Grid carta, kad data dan petunjuk'),
)


def load():
    draft = read_agihan()
    weeks = {str(item['minggu']): item for item in draft['takwim']}
    schedule = {n: weeks[week] for week, slots in draft['tahun']['4']['minggu'].items() for n, m in slots if m == 30}
    plans = []
    for line in SOURCE.read_text(encoding='utf-8').splitlines():
        number, standards, pages, title, model, task, evidence = line.split('|')
        if not all((standards, pages, title, model, task, evidence)):
            raise ValueError(f'Incomplete Year 4 review Lesson {number}.')
        plans.append((int(number), standards.split(','), pages, title, model, task, evidence))
    if len(plans) != 42 or [row[0] for row in plans] != sorted(schedule):
        raise ValueError('Year 4 review drafts must cover every 30-minute 2027 RPT slot.')
    return plans, schedule


def export(plans, schedule, output):
    output.mkdir(parents=True, exist_ok=True)
    for number, sp, pages, title, model, task, evidence in plans:
        unit, (_, name, materials) = next((index, row) for index, row in enumerate(UNITS, 1) if number <= row[0])
        week = schedule[number]
        sk = ', '.join(dict.fromkeys(code.rsplit('.', 1)[0] for code in sp))
        heading = ('Rancangan Pengajaran Harian', 'Matematik SK Tahun 4 · Draf semakan guru', title)
        details = [
            ('Unit', f'Unit {unit} {name}'),
            ('Lesson / tempoh', f'Lesson {number:03d} · 30 minit'),
            ('Tarikh RPT', f"M{week['minggu']:02d} · A {display_dates(week['A'])} · B {display_dates(week['B'])}"),
            ('Maklumat kelas', 'Kelas ______ · Tarikh ______ · Masa ______ · Murid ______'),
            ('SK / SP', f"SK {sk} · SP {', '.join(sp)}"),
            ('Rujukan', f'DSKP Matematik Tahun 4 · Buku Teks SK, hlm. {pages}'),
            ('Objektif', f'Murid dapat {title[0].lower() + title[1:]} berdasarkan tugasan PBD.'),
            ('Bahan', materials),
        ]
        activities = [
            ('Fasa', 'Tindakan guru', 'Tindakan murid'),
            ('Set induksi · 3 minit', f'Paparkan bahan daripada unit {name.lower()} dan kenal pasti maklumat yang diberi.',
             'Nyatakan satu perkara yang diketahui daripada situasi atau model.'),
            ('Aktiviti 1 · 10 minit', model, 'Bina model atau jalankan contoh bersama. Terangkan satu langkah kepada rakan.'),
            ('Aktiviti 2 / PBD · 13 minit', task, 'Jawab secara individu dan serahkan pengiraan atau hasil kerja kepada guru.'),
            ('Penutup · 4 minit', 'Semak satu respons menggunakan model atau cara songsang yang sesuai.',
             'Terangkan semakan dan betulkan satu langkah yang tersilap jika perlu.'),
        ]
        reflection = [('Evidens PBD', evidence), ('Refleksi', '___ / ___ murid mencapai objektif. Semak semula item yang sukar.')]
        for ext, renderer in (('docx', _word), ('pdf', _pdf)):
            with (output / f'CikguLaju_Matematik_T4_Lesson_{number:03d}.{ext}').open('wb') as stream:
                renderer(stream, heading, details, activities, reflection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plans, schedule = load()
    export(plans, schedule, args.output)
    print('42 RPH Matematik SK Tahun 4 disahkan dan dieksport.')


if __name__ == '__main__':
    main()
