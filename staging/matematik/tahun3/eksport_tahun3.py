"""Export the 117 SK Mathematics Year 3 RPH for DPK Edisi 3."""

import argparse
from pathlib import Path

from dlp_year2_rph import _pdf, _word
from staging.matematik.eksport_agihan import display_dates, read_agihan


SOURCE = Path(__file__).resolve().parent
PHASE_MINUTES = {30: (3, 10, 13, 4), 60: (5, 23, 25, 7)}
UNITS = (
    (13, 'Nombor hingga 10 000', 'Kad nombor, blok asas sepuluh dan garis nombor'),
    (27, 'Operasi asas', 'Kad cerita, pembilang dan jadual nilai tempat'),
    (50, 'Pecahan, perpuluhan dan peratus', 'Jalur pecahan, petak seratus dan kad nombor'),
    (67, 'Wang', 'Kad harga, label wang dan jadual transaksi'),
    (80, 'Masa dan waktu', 'Jam model, kalendar, jadual waktu dan kad situasi'),
    (99, 'Ukuran dan sukatan', 'Alat ukur, bekas penyukat dan model bergambar'),
    (107, 'Bentuk', 'Kad bentuk, model kertas dan pembaris'),
    (112, 'Kedudukan', 'Grid paksi, kad objek dan penanda'),
    (117, 'Data', 'Rekod gundalan, piktograf berpetunjuk, carta palang dan carta pai'),
)
STANDARDS = {
    '1.1': 'Nilai nombor', '1.2': 'Menganggar', '1.3': 'Membundarkan nombor', '1.4': 'Pola nombor',
    '2.1': 'Tambah dan tolak dalam lingkungan 10 000', '2.2': 'Darab dan bahagi dalam lingkungan 10 000',
    '3.1': 'Pecahan', '3.2': 'Perpuluhan', '3.3': 'Peratus',
    '3.4': 'Perkaitan antara pecahan, perpuluhan dan peratus',
    '4.1': 'Tambah dan tolak wang', '4.2': 'Darab dan bahagi wang', '4.3': 'Mata wang asing',
    '4.4': 'Simpanan dan perbelanjaan', '5.1': 'Masa dan waktu',
    '5.2': 'Tambah dan tolak masa', '5.3': 'Darab dan bahagi masa',
    '6.1': 'Panjang', '6.2': 'Jisim', '6.3': 'Isi padu cecair', '7.1': 'Prisma dan bukan prisma', '7.2': 'Poligon sekata', '7.3': 'Paksi simetri',
    '8.1': 'Kedudukan pada paksi', '9.1': 'Mengumpul, mengelas dan menyusun data', '9.2': 'Carta pai',
}
DPK_PAGES = {
    '1.1.1(i)': '39', '1.1.1(ii)': '40', '1.1.2': '40–41', '1.2.1': '42', '1.3.1': '42', '1.4.1': '42', '1.4.2': '42',
    '2.1.1': '43', '2.1.2': '44', '2.2.1': '44',
    '3.1.1': '45', '3.1.2': '46', '3.1.3': '46', '3.1.4': '47', '3.1.5': '47', '3.2.1': '47', '3.2.2': '47', '3.3.1': '48', '3.3.2': '48', '3.4.1': '48',
    '4.1.1': '49', '4.1.2': '49', '4.2.1': '49', '4.3.1': '50', '4.4.1': '50',
    '5.1.1': '51', '5.1.2': '52', '5.2.1': '52', '5.2.2': '52', '5.3.1': '53',
    '6.1.1': '54', '6.1.2': '54', '6.1.3': '55', '6.2.1': '56', '6.2.2': '56', '6.2.3': '57',
    '6.3.1': '57', '6.3.2': '57', '6.3.3': '57', '7.1.1': '58', '7.1.2': '58', '7.1.3': '58',
    '7.2.1': '59', '7.2.2': '59', '7.3.1': '59',
    '8.1.1': '60', '8.1.2': '60', '8.1.3': '60', '9.1.1': '61', '9.2.1': '61', '9.2.2': '61',
}


def load():
    draft = read_agihan()
    weeks = {str(row['minggu']): row for row in draft['takwim']}
    schedule = {number: (weeks[week], minutes) for week, slots in draft['tahun']['3']['minggu'].items()
                for number, minutes in slots}
    plans = []
    for slot in (30, 60):
        found = []
        lines = (SOURCE / f'slot_{slot}_minit.tsv').read_text(encoding='utf-8').splitlines()
        for line in lines:
            number, sp, volume, pages, title, model, task, evidence = line.split('|')
            if sp not in DPK_PAGES or not all((pages, title, model, task, evidence)):
                raise ValueError(f'Semak SP, bahan atau evidens bagi Lesson {number}.')
            found.append(int(number))
            plans.append((int(number), sp, int(volume), pages, title, model, task, evidence))
        if found != sorted(n for n, (_, minutes) in schedule.items() if minutes == slot):
            raise ValueError(f'Semak slot {slot} minit Tahun 3 terhadap agihan RPT.')
    plans.sort()
    if {row[1] for row in plans} != DPK_PAGES.keys():
        raise ValueError('Set Tahun 3 mesti meliputi semua SP dalam DPK.')
    return plans, schedule


def unit_for(number):
    return next((unit, row) for unit, row in enumerate(UNITS, 1) if number <= row[0])


def document(plan, slot):
    number, sp, volume, pages, title, model, task, evidence = plan
    unit, (_, name, materials) = unit_for(number)
    week, minutes = slot
    opening, modelling, assessment, closing = PHASE_MINUTES[minutes]
    sk = sp.rsplit('.', 1)[0]
    details = [
        ('Unit', f'Unit {unit} {name}'),
        ('Lesson / tempoh', f'Lesson {number:03d} · {minutes} minit'),
        ('Tarikh RPT', f"M{week['minggu']:02d} · A {display_dates(week['A'])} · B {display_dates(week['B'])}"),
        ('Maklumat kelas', 'Kelas ______ · Tarikh ______ · Masa ______ · Murid ______'),
        ('SK / SP', f'SK {sk} {STANDARDS[sk]} · SP {sp}'),
        ('Rujukan', f'DPK Edisi 3, hlm. {DPK_PAGES[sp]} · Buku Teks Jilid {volume}, hlm. {pages}'),
        ('Objektif', f'Murid dapat {title[0].lower() + title[1:]} dan memberi respons yang sepadan dalam tugasan PBD.'),
        ('Bahan', materials),
    ]
    activities = [
        ('Fasa', 'Tindakan guru', 'Tindakan murid'),
        (f'Set induksi · {opening} minit', f'Paparkan bahan bagi topik {name.lower()}. Tanyakan maklumat yang sudah diketahui.',
         'Nyatakan satu maklumat daripada model atau situasi.'),
        (f'Aktiviti 1 · {modelling} minit', model, 'Ikuti model. Tunjukkan satu langkah, bacaan atau padanan kepada rakan.'),
        (f'Aktiviti 2 / PBD · {assessment} minit', task, 'Selesaikan tugasan secara individu. Catat jawapan atau tunjukkan model kepada guru.'),
        (f'Penutup · {closing} minit', 'Pilih satu respons untuk disemak dengan model asal.',
         'Terangkan cara menyemak respons menggunakan maklumat dalam soalan.'),
    ]
    reflection = [('Evidens PBD', evidence), ('Refleksi', '___ / ___ murid mencapai objektif. Semak item yang belum dikuasai.')]
    heading = ('Rancangan Pengajaran Harian', 'Matematik SK Tahun 3 · 2027', title)
    return heading, details, activities, reflection


def export(plans, schedule, output):
    output.mkdir(parents=True, exist_ok=True)
    for plan in plans:
        number = plan[0]
        parts = document(plan, schedule[number])
        for extension, renderer in (('docx', _word), ('pdf', _pdf)):
            with (output / f'CikguLaju_Matematik_T3_Lesson_{number:03d}.{extension}').open('wb') as stream:
                renderer(stream, *parts, mathematics=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plans, schedule = load()
    export(plans, schedule, args.output)
    print('117 RPH Tahun 3 disahkan dan dieksport, termasuk 42 sesi 30 minit.')


if __name__ == '__main__':
    main()
