"""Export the complete 117-lesson SK Mathematics Year 2 review set."""

import argparse
from collections import Counter
from pathlib import Path

from dlp_year2_rph import _pdf, _word
from staging.matematik.eksport_agihan import display_dates
from staging.matematik.tahun2 import eksport_unit_01 as unit_one


SOURCE = Path(__file__).resolve().parent
UNITS = (
    ('Nombor hingga 1000', 1, 14),
    ('Tambah, tolak, darab dan bahagi', 1, 30),
    ('Pecahan dan perpuluhan', 2, 56),
    ('Wang', 2, 75),
    ('Masa dan waktu', 2, 86),
    ('Panjang, jisim dan isi padu cecair', 2, 105),
    ('Bentuk', 2, 112),
    ('Data', 2, 117),
)
STANDARDS = {
    '2.1': ('Tambah dalam lingkungan 1000', 23, 'Blok asas sepuluh dan carta nilai tempat'),
    '2.2': ('Tolak dalam lingkungan 1000', 24, 'Blok asas sepuluh dan carta nilai tempat'),
    '2.3': ('Darab dalam lingkungan 1000', 25, 'Pembilang, piring kecil dan kad ayat darab'),
    '2.4': ('Bahagi dalam lingkungan 1000', 26, 'Pembilang, dulang dan kad ayat bahagi'),
    '3.1': ('Konsep perdua dan perempat pecahan wajar', 27, 'Kertas lipat dan jalur berpetak'),
    '3.2': ('Pecahan wajar', 27, 'Jalur pecahan sama panjang dan kad simbol'),
    '3.3': ('Perpuluhan', 27, 'Jalur persepuluh, kad nombor dan garis nombor'),
    '4.1': ('Wang kertas dan duit syiling', 28, 'Wang contoh dan kad nilai'),
    '4.2': ('Tambah wang', 28, 'Wang contoh dan tag harga'),
    '4.3': ('Tolak wang', 29, 'Wang contoh dan tag harga'),
    '4.4': ('Darab wang', 29, 'Wang contoh dan kad harga seunit'),
    '4.5': ('Bahagi wang', 30, 'Wang contoh dan sampul'),
    '5.1': ('Waktu dalam jam dan minit', 31, 'Jam analog model dan kad waktu'),
    '5.2': ('Perkaitan dalam masa dan waktu', 31, 'Jam model dan jalur satu hari'),
    '6.1': ('Panjang', 32, 'Jalur rujukan, pembaris dan pita ukur'),
    '6.2': ('Jisim', 32, 'Penimbang dan bungkusan rujukan'),
    '6.3': ('Isi padu cecair', 33, 'Bekas, air dan alat penyukat'),
    '7.1': ('Bentuk tiga dimensi', 34, 'Model bentuk, kad gambar dan bentangan kertas'),
    '7.2': ('Bentuk dua dimensi', 34, 'Kad bentuk, model pepejal, kertas dan pensel'),
    '8.1': ('Mengumpul, mengelas dan menyusun data', 35, 'Kad respons dan jadual gundalan'),
    '8.2': ('Carta palang', 35, 'Carta palang bergambar dan kad soalan'),
}
DPK_SP = {
    f'{code}.{index}'
    for code, count in (
        ('2.1', 1), ('2.2', 1), ('2.3', 2), ('2.4', 2),
        ('3.1', 1), ('3.2', 2), ('3.3', 3),
        ('4.1', 2), ('4.2', 1), ('4.3', 1), ('4.4', 1), ('4.5', 1),
        ('5.1', 2), ('5.2', 1), ('6.1', 3), ('6.2', 3), ('6.3', 3),
        ('7.1', 3), ('7.2', 2), ('8.1', 1), ('8.2', 1),
    ) for index in range(1, count + 1)
}
PAGE_OVERRIDES = {'6.2.3': 33}
PHASE_MINUTES = {30: (3, 10, 13, 4), 60: (5, 23, 25, 7)}
INTRO = {
    2: ('Paparkan nombor dalam model. Minta murid kenal pasti kuantiti yang hendak dicari.',
        'Nyatakan nilai yang diketahui dan ramalkan cara mengira.'),
    3: ('Paparkan model bahagian dan keseluruhan sebelum menunjukkan label.',
        'Nyatakan bilangan bahagian sama besar dan bahagian yang ditandakan.'),
    4: ('Paparkan kad wang atau tag harga daripada situasi yang akan digunakan.',
        'Baca nilai wang serta unit yang tertera.'),
    5: ('Paparkan muka jam bagi situasi. Minta murid bezakan jarum jam dengan jarum minit.',
        'Tunjukkan kedua-dua jarum dan nyatakan bacaan awal.'),
    6: ('Paparkan objek, unit atau alat dalam tugasan. Minta murid nyatakan sifat yang dinilai.',
        'Pilih panjang, jisim atau isi padu dan nyatakan unit yang sesuai.'),
    7: ('Paparkan satu daripada objek atau kad bentuk yang akan digunakan.',
        'Tunjukkan satu ciri pada sempadan atau permukaan bentuk.'),
    8: ('Paparkan dua kategori daripada set data. Tanya bagaimana satu maklumat perlu dikelaskan atau dibaca.',
        'Nyatakan kategori yang dipilih dan tunjuk lokasi catatannya.'),
}
CHECK = {
    2: ('Minta murid tunjuk satu langkah semakan yang sesuai dengan operasi.',
        'Semak menggunakan model, anggaran atau operasi songsang yang sesuai.'),
    3: ('Minta murid padankan semula satu jawapan dengan model yang mempunyai keseluruhan sama saiz.',
        'Tunjukkan bahagian yang membuktikan jawapan pada jalur, rajah atau garis nombor.'),
    4: ('Minta murid baca semula satu jawapan lengkap dengan unit wang.',
        'Sebut hasil dalam ringgit atau sen dan terangkan maksudnya dalam situasi.'),
    5: ('Tunjukkan semula satu catatan. Minta murid nyatakan kaitannya dengan muka jam.',
        'Padankan catatan dengan jarum sebenar atau jalur masa.'),
    6: ('Minta murid tunjuk cara memilih alat atau membaca tanda yang berkaitan.',
        'Sebut unit dan tunjuk tanda rujukan yang menyokong jawapan.'),
    7: ('Minta murid semak satu jawapan dengan menjejak tepi, memusing atau melipat model.',
        'Terangkan satu ciri berdasarkan pemerhatian terhadap model.'),
    8: ('Minta murid ulang satu bacaan mengikut label kategori atau paksi.',
        'Tunjuk kategori dan sebut bilangan atau perbandingan yang diperoleh.'),
}


def load():
    first, schedule = unit_one.load()
    chapters = [(1, UNITS[0], first)]
    ids = [plan['lesson'] for plan in first]
    all_codes = set()
    for unit, info in enumerate(UNITS[1:], 2):
        rows = []
        for line in (SOURCE / f'unit_{unit:02d}.tsv').read_text(encoding='utf-8').splitlines():
            number, codes, pages, title, model, task, evidence = line.split('|')
            number = int(number)
            codes = codes.split(',')
            if not all((pages, title, model, task, evidence)) or not set(codes) <= DPK_SP:
                raise ValueError(f'Incomplete or unsupported Year 2 Lesson {number:03d}.')
            rows.append((number, codes, pages, title, model, task, evidence))
            all_codes.update(codes)
            ids.append(number)
        if not rows or rows[-1][0] != info[2]:
            raise ValueError(f'Unexpected end of Unit {unit}.')
        chapters.append((unit, info, rows))
    if ids != list(range(1, 118)) or all_codes != DPK_SP:
        raise ValueError('Year 2 must contain Lessons 001–117 and cover all DPK standards.')
    times = Counter(schedule[number][1] for number in ids)
    if times != {30: 42, 60: 75}:
        raise ValueError('Year 2 must cover 42 half-hour and 75 one-hour sessions.')
    return chapters, schedule


def standards(codes):
    keys = dict.fromkeys(code.rsplit('.', 1)[0] for code in codes)
    sk = ' / '.join(f'{key} {STANDARDS[key][0]}' for key in keys)
    pages = ', '.join(map(str, sorted({PAGE_OVERRIDES.get(code, STANDARDS[code.rsplit('.', 1)[0]][1]) for code in codes})))
    materials = STANDARDS[next(iter(keys))][2]
    return sk, pages, materials


def export(chapters, schedule, output):
    output.mkdir(parents=True, exist_ok=True)
    unit_one.export(chapters[0][2], schedule, output)
    for unit, (unit_name, book, _), rows in chapters[1:]:
        for number, codes, textbook, title, model, task, evidence in rows:
            week, minutes = schedule[number]
            sk, dpk, materials = standards(codes)
            heading = ('Rancangan Pengajaran Harian', 'Matematik SK Tahun 2 · Draf semakan guru', title)
            details = [
                ('Unit', f'Unit {unit} {unit_name}'),
                ('Lesson / tempoh', f'Lesson {number:03d} · {minutes} minit'),
                ('Tarikh RPT', f"M{week['minggu']:02d} · A {display_dates(week['A'])} · B {display_dates(week['B'])}"),
                ('Maklumat kelas', 'Kelas ______ · Tarikh ______ · Masa ______ · Murid ______'),
                ('SK / SP', f"SK {sk} · SP {', '.join(codes)}"),
                ('Rujukan', f'DPK Edisi 3, hlm. {dpk} · Buku Teks Jilid {book}, hlm. {textbook}'),
                ('Objektif', f'Murid dapat {title[0].lower() + title[1:]} dan menunjukkan hasil yang sepadan dalam tugasan PBD.'),
                ('Bahan', materials),
            ]
            activities = [('Fasa', 'Tindakan guru', 'Tindakan murid')]
            actions = (
                INTRO[unit],
                (model, 'Ikuti contoh dengan bahan yang disediakan. Tunjukkan satu langkah atau padanan kepada rakan.'),
                (task, 'Jawab atau tunjuk hasil secara individu. Semak unit, model atau label sebelum dihantar.'),
                CHECK[unit],
            )
            activities.extend((f'{phase} · {time} minit', *action)
                              for phase, time, action in zip(unit_one.PHASES, PHASE_MINUTES[minutes], actions, strict=True))
            reflection = [('Evidens PBD', evidence), ('Refleksi', '___ / ___ murid mencapai objektif. Ulang item yang belum dikuasai bersama murid berkaitan.')]
            for extension, renderer in (('docx', _word), ('pdf', _pdf)):
                with (output / f'CikguLaju_Matematik_T2_Lesson_{number:03d}.{extension}').open('wb') as stream:
                    renderer(stream, heading, details, activities, reflection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    chapters, schedule = load()
    export(chapters, schedule, args.output)
    print('117 RPH Tahun 2 dieksport, termasuk 42 sesi 30 minit.')


if __name__ == '__main__':
    main()
