"""Eksport RPT dan RPH Sains SK Tahun 6 untuk semakan guru."""

import argparse
from datetime import date
import json
from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from dlp_year2_rph import _pdf, _word
from web.sains_unit_awal import LESSONS
from web.sains_y6_84_activity_bank_draf_20261107 import BANK


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("agihan_2027.json")
CALENDAR = ROOT / "rpt_2027/takwim_pdp_2027_ab_draf.json"
INVENTORY = ROOT / "audits/sains_dskp_t6_sp_token_inventory_20261106.json"
RPT_STEM = "CikguLaju_RPT_Sains_SK_Tahun6_2027_Semakan_Guru"
DURATIONS = {30: (3, 7, 8, 9, 3), 60: (5, 16, 19, 15, 5)}
PHASES = ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Pentaksiran PBD", "Penutup")

OPENING_ACTIONS = {
    85: (
        ("Tunjuk dua kereta model.", "Sebut satu ciri bagi setiap model."),
        ("Model cara mengelas kad dan menanda titik mula.", "Asingkan kad mengikut satu ciri sepunya."),
        ("Selia ukuran dari titik mula yang sama.", "Ukur satu jarak dan catat unit cm."),
        ("Semak ciri, pengelasan dan unit ukuran.", "Catat dua ciri, satu pengelasan dan satu bacaan."),
        ("Minta murid memberi sebab memilih titik mula yang sama.", "Terangkan cara memastikan ukuran setara."),
    ),
    86: (
        ("Paparkan dua bacaan jarak.", "Kenal pasti model yang bergerak lebih jauh."),
        ("Model cara melabel jadual dan beza inferens dengan ramalan.", "Susun bacaan dalam jadual berlabel."),
        ("Minta murid menguji andaian menggunakan bacaan yang diberi.", "Tulis sebab yang mungkin dan jangkaan bagi ujian baharu."),
        ("Semak bukti yang menyokong inferens dan ramalan.", "Beri satu inferens dan satu ramalan bersama bacaan yang dirujuk."),
        ("Tanya cara menguji inferens.", "Nyatakan satu data tambahan yang diperlukan."),
    ),
    87: (
        ("Tunjuk kedudukan model pada dua masa.", "Banding kedudukan yang ditunjukkan."),
        ("Model cara mencatat kedudukan pada sela masa tetap.", "Susun kad kedudukan mengikut masa."),
        ("Bimbing tafsiran pola dan semak titik awal serta akhir ukuran.", "Terangkan pola dan tetapkan cara mengukur jarak pada satu masa."),
        ("Semak dua nilai dan takrif jarak.", "Serah urutan, penerangan pola dan takrif ukuran yang boleh diulang."),
        ("Tanya beza jarak dengan kelajuan.", "Berikan satu contoh ukuran dalam cm."),
    ),
    88: (
        ("Tunjuk model dengan dua jisim.", "Ramalkan kesan perubahan jisim."),
        ("Tetapkan jisim sebagai faktor yang diubah.", "Tentukan jarak sebagai ukuran dan pilih dua kawalan."),
        ("Semak supaya belon, model dan laluan sama.", "Tulis hipotesis dan semak rancangan rakan."),
        ("Semak pemboleh ubah dan kaitan antara jisim dengan jarak.", "Hantar tiga jenis pemboleh ubah dan satu hipotesis boleh uji."),
        ("Tanya kesan mengubah dua faktor serentak.", "Terangkan mengapa faktor lain perlu dikekalkan."),
    ),
    89: (
        ("Semak pemboleh ubah dan laluan ujian.", "Tetapkan tugas pelepas, pengukur dan pencatat."),
        ("Selia dua ulangan untuk setiap jisim.", "Ukur dari garisan mula hingga model berhenti. Catat empat bacaan."),
        ("Bimbing perbandingan bacaan dan penerangan perbezaan ulangan.", "Bandingkan hasil dan tulis rumusan terhadap hipotesis."),
        ("Semak empat bacaan, dua kawalan dan bukti dalam rumusan.", "Serah laporan dengan keputusan serta dua bacaan yang dirujuk."),
        ("Minta satu penambahbaikan jika bacaan tidak seragam.", "Cadangkan cara meningkatkan ketekalan ujian."),
    ),
}

# Penyesuaian aktiviti amali dan penggunaan rekod pemerhatian.
ACTIVITY_UPDATES = {
    "3.1.3": {
        "hook": "Belon pada botol dan imej protozoa",
        "teacher1": "menyelia ujian yis pembakar makanan mengikut Aktiviti 1 buku teks dan menanda masa mula",
        "pupil1": "memasang belon pada botol dan mengukur lilitannya pada minit 0 dan 10",
        "teacher2": "menyediakan rakaman protozoa dan foto kulapuk bertarikh untuk pemerhatian semasa menunggu bacaan",
        "pupil2": "melakar perubahan kedudukan dan membandingkan keluasan tompok pada foto. Lengkapkan ukuran belon pada minit 20 dan 30",
        "pbd": "Huraikan pernafasan, pergerakan dan pertumbuhan dengan satu bukti pemerhatian bagi setiap proses",
        "materials": "Kit yis pembakar makanan, jadual masa, rakaman protozoa dan foto kulapuk",
        "safety": "Guru menyelia penggunaan air suam dan yis pembakar makanan.",
    },
    "3.1.4": {
        "hook": "Dua sampel yis pembakar dan kad ramalan",
        "teacher1": "membimbing ujian dua sampel yis, satu dengan gula dan satu tanpa gula. Jisim yis awal, suhu, isipadu dan tempoh dipadankan",
        "pupil1": "menulis hipotesis, melabel kedua-dua sampel dan memulakan eksperimen di bawah seliaan guru",
        "teacher2": "memaparkan imej mikroskop kedua-dua sampel pada masa mula dan menetapkan masa bacaan susulan",
        "pupil2": "merekod kiraan awal sel yis pada grid yang sama saiz. Ulang kiraan pada masa susulan dan bandingkan perubahan",
        "pbd": "Catat hipotesis dan tiga pemboleh ubah, kemudian rumuskan perubahan kiraan sel yis bagi kedua-dua sampel",
        "materials": "Yis pembakar makanan, dua sampel berlabel, imej mikroskop bergrid dan jadual kiraan",
        "safety": "Guru menyediakan slaid dan mengendalikan sampel yis pembakar makanan.",
    },
    "3.1.6": {
        "hook": "Jadual penyiasatan PdP 013 dan eksperimen PdP 014",
        "teacher1": "memaparkan imej mikroskop susulan bagi kedua-dua sampel yis dengan grid yang sama saiz",
        "pupil1": "melengkapkan kiraan susulan dan mengira perubahan bersama kumpulan",
        "teacher2": "membimbing murid menghubungkan satu dapatan proses hidup dan satu dapatan faktor pertumbuhan dengan bukti",
        "pupil2": "menyediakan lakaran berlabel atau laporan ringkas dan berkongsi dapatan dengan rakan",
        "pbd": "Satu lakaran atau laporan individu dengan satu pemerhatian proses hidup dan satu perbandingan kiraan sel yis",
        "materials": "Log PdP 013 dan 014, imej mikroskop susulan bergrid dan kertas laporan",
        "safety": "Pemerhatian menggunakan imej mikroskop yang disediakan guru.",
    },
    "4.2.1": {
        "teacher1": "menunjukkan dua set anak pokok sama spesies yang sudah disediakan pada kepadatan berbeza",
        "pupil1": "mengukur tinggi dari aras tanah dan merekod keadaan daun bagi dua sampel setiap set",
        "teacher2": "membimbing murid mengenal pasti kepadatan sebagai faktor ubah dan cahaya serta siraman sebagai kawalan",
        "pupil2": "membandingkan dua set dan mengaitkan dapatan dengan persaingan untuk ruang, air atau cahaya",
        "pbd": "Jadual dua set, satu pemboleh ubah dimalarkan dan satu inferens berasaskan ukuran",
        "materials": "Dua set anak pokok pratanam, pembaris dan jadual",
    },
    "6.2.3": {
        "teacher1": "menunjukkan stesen tarik bongkah pada dua permukaan dengan jisim yang sama",
        "pupil1": "merekod bacaan neraca spring semasa bongkah bergerak sekata",
        "teacher2": "menunjukkan stesen kedua yang mengubah jisim dengan permukaan yang sama",
        "pupil2": "membandingkan bacaan dalam setiap stesen dan menyatakan faktor yang dikekalkan",
        "pbd": "Dua perbandingan daya dalam newton, pemboleh ubah dan rumusan berasaskan bacaan",
        "materials": "Bongkah ringan, pemberat, neraca spring, kain, papan dan rekod bacaan",
    },
    "8.2.3": {
        "teacher1": "menunjukkan dua bahagian buah yang sama yang disediakan untuk pengeringan dan penyejukbekuan",
        "pupil1": "melabel kedua-dua sampel, mencatat keadaan awal dan memulakan projek di bawah seliaan guru",
        "teacher2": "menunjukkan rekod susulan bertarikh bagi dua kaedah",
        "pupil2": "membandingkan satu ciri yang dapat dilihat dan merancang catatan susulan projek",
        "pbd": "Log dua kaedah bagi buah yang sama dengan keadaan awal dan satu dapatan daripada rekod susulan",
        "materials": "Buah dipotong guru, bekas berlabel, gambar bertarikh dan jadual",
        "safety": "Gunakan sampel untuk pemerhatian di bawah seliaan guru.",
    },
    "12.1.4": {
        "teacher1": "menunjukkan dua rasuk kertas sama jenis dengan bentuk rata dan berlipat",
        "pupil1": "menambah beban ringan pada tengah rasuk dan mencatat had sebelum bengkok",
        "teacher2": "memberi dua rasuk sama bentuk daripada bahan berbeza dan menyemak jarak sokongan",
        "pupil2": "mengulang ujian dengan jarak dan kedudukan beban dimalarkan",
        "pbd": "Dua perbandingan yang memisahkan kesan bentuk dan bahan serta satu rumusan berpandukan bilangan beban",
        "materials": "Rasuk siap dibentuk, dua penyokong, pemberat ringan dan jadual",
    },
    "12.1.6": {
        "teacher1": "menunjukkan cara menyambung bahagian kadbod bersih yang siap dipotong",
        "pupil1": "memasang model bertapak luas dan mengukuhkan penyokong",
        "teacher2": "menunjukkan cara merekod ujian tolakan ringan dan ujian beban pada model",
        "pupil2": "menguji model lalu mengenal pasti satu penambahbaikan",
        "pbd": "Model daripada bahan kitar semula dengan rekod ujian kestabilan dan beban",
        "materials": "Kadbod terpakai yang siap dipotong, pita pelekat, pemberat ringan dan jadual",
    },
}


def sentence(text):
    return text[0].upper() + text[1:].rstrip(".") + "."


def ordinary_plan(row):
    standard, = row["standards"]
    lesson = {**BANK[standard], **ACTIVITY_UPDATES.get(standard, {})}
    hook = lesson["hook"]
    assessment = f"Serahkan hasil individu. {lesson['pbd']}."
    if standard == "3.1.4":
        assessment = "Serahkan hipotesis, pemboleh ubah dan kiraan awal. Lengkapkan rumusan pada PdP 016."
    activities = (
        (f"Tunjukkan {hook[0].lower() + hook[1:]}.", "Nyatakan satu pemerhatian atau jangkaan."),
        (sentence(lesson["teacher1"]), sentence(lesson["pupil1"])),
        (sentence(lesson["teacher2"]), sentence(lesson["pupil2"])),
        ("Semak hasil individu mengikut kriteria PBD.", assessment),
        ("Minta murid mengaitkan bukti dengan tajuk.", "Jelaskan satu dapatan dengan bukti daripada aktiviti."),
    )
    return lesson["pbd"], lesson["materials"], lesson["safety"], activities


def build_source():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    calendar = json.loads(CALENDAR.read_text(encoding="utf-8"))["minggu"]
    standards = set(json.loads(INVENTORY.read_text(encoding="utf-8"))["sp_tokens"])
    rows = {row["id"]: row for row in data["pdp"]}
    opening = {lesson.number: lesson for lesson in LESSONS if lesson.year == 6}
    if len(rows) != len(data["pdp"]) or set(rows) != set(range(1, 90)):
        raise ValueError("Expected 89 unique source PdP")
    sequence = []
    weeks = data["minggu"]
    for week, original in zip(weeks, calendar, strict=True):
        number = week["minggu"]
        expected_a = ["2027-03-15", "2027-03-18"] if number == 10 else original["A"]
        if number != original["minggu"] or week["A"] != expected_a or week["B"] != original["B"]:
            raise ValueError(f"Unexpected calendar window M{number:02d}")
        ids = week["pdp"]
        has_teaching = number <= 38 and number not in (6, 18, 19)
        if bool(ids) != has_teaching or len(ids) > 3:
            raise ValueError(f"Invalid teaching slots M{number:02d}")
        slots = sum(rows[i]["minutes"] for i in ids)
        if slots > (90 if number in data["minggu_pendek"] else 150):
            raise ValueError(f"Excess minutes M{number:02d}")
        for i in ids:
            row = rows[i]
            if not re.fullmatch(r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*", row["pages"]):
                raise ValueError(f"Invalid textbook references PdP {i:03d}")
            sks = {code.rsplit(".", 1)[0] for code in row["standards"]}
            if len(sks) != 1 or not row["title"] or not row["unit"].startswith(f"Unit {next(iter(sks)).split('.')[0]}:"):
                raise ValueError(f"Invalid source unit or SK PdP {i:03d}")
            row["sk"] = sks.pop()
            row["week"] = number
            row["dates"] = f"A {date_range(week['A'])} · B {date_range(week['B'])}"
            if i in opening:
                lesson = opening[i]
                if (tuple(row["standards"]) != lesson.standards
                        or row["title"] != lesson.title or row["pages"].replace("-", "–") != lesson.pages):
                    raise ValueError(f"Opening lesson {i} differs from source")
                pbd, materials, safety, actions = (
                    lesson.assessment, lesson.materials, "", OPENING_ACTIONS[i],
                )
                row["objective"] = lesson.objective
            else:
                pbd, materials, safety, actions = ordinary_plan(row)
                row["objective"] = pbd
            row.update(pbd=pbd, materials=materials, safety=safety)
            row["phases"] = [
                (f"{phase} · {minutes} minit", teacher, pupils)
                for phase, minutes, (teacher, pupils) in zip(PHASES, DURATIONS[row["minutes"]], actions, strict=True)
            ]
            sequence.append(i)
    if sequence != [*range(85, 90), *range(1, 85)]:
        raise ValueError("Source teaching order changed")
    if {code for row in rows.values() for code in row["standards"]} != standards or len(standards) != 96:
        raise ValueError("Source standards differ from DSKP inventory")
    if sorted(row["minutes"] for row in rows.values()) != [30] * 50 + [60] * 39:
        raise ValueError("RPT must preserve the 64-hour source allocation")
    return weeks, rows


def date_range(values):
    return "–".join(date.fromisoformat(value).strftime("%d/%m") for value in values)


def export_rpt(path, weeks, rows):
    doc = Document()
    doc.core_properties.title = "Rancangan Pengajaran Tahunan Sains Tahun 6 Sekolah Kebangsaan 2027"
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Mm(297), Mm(210)
    section.left_margin = section.right_margin = Mm(13)
    section.top_margin = section.bottom_margin = Mm(12)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(9.5)
    normal.paragraph_format.space_after = Pt(2)
    title = doc.styles["Title"]
    title.font.color.rgb = RGBColor(0, 0, 0)
    title_properties = title.element.get_or_add_pPr()
    border = title_properties.find(qn("w:pBdr"))
    if border is not None:
        title_properties.remove(border)
    footer = section.footer.paragraphs[0]
    footer.text = "Sains Tahun 6 SK 2027    •    Halaman "
    page_field = OxmlElement("w:fldSimple")
    page_field.set(qn("w:instr"), "PAGE")
    footer._p.append(page_field)
    doc.add_paragraph("Rancangan Pengajaran Tahunan Sains Tahun 6 2027", "Title")
    doc.add_paragraph("Sekolah Kebangsaan · KSSR Semakan 2017 · Kumpulan A dan B")
    profile = doc.add_table(rows=3, cols=2)
    profile.style = "Table Grid"
    for line, label in zip(profile.rows, ("Nama sekolah", "Nama guru", "Logo sekolah"), strict=True):
        line.cells[0].text = label
        if label == "Logo sekolah":
            line.height = Mm(24)
        else:
            line.height = Mm(11)
            line.cells[1].text = "__________________________________"
        line.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    doc.add_heading("Peruntukan PdP", 1)
    doc.add_paragraph("89 PdP dalam 13 unit, dengan 50 sesi 30 minit dan 39 sesi 60 minit. Jumlah 64 jam.")
    doc.add_paragraph("Gunakan julat Kumpulan A atau B mengikut sekolah. Pilih slot PdP sebenar mengikut jadual waktu, cuti negeri dan tarikh UASA sekolah.")
    doc.add_paragraph("Kumpulan A meliputi Kedah, Kelantan dan Terengganu. Kumpulan B meliputi negeri lain dan Wilayah Persekutuan.")
    doc.add_paragraph("Sumber: Kalendar Akademik KPM 2027, DSKP Sains Tahun 6 dan Buku Teks Sains Tahun 6 SK, DBP 2021.")
    doc.add_page_break()

    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    table.autofit = False
    widths = (42, 60, 34, 105, 28)
    for column, value in zip(table.columns, widths, strict=True):
        column.width = Mm(value)
    header = table.rows[0]
    header._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for cell, width, label in zip(
        header.cells, widths, ("Minggu dan tarikh A/B", "PdP dan unit", "SK dan SP", "Evidens PBD", "Buku teks dan masa"), strict=True,
    ):
        cell.width = Mm(width)
        background = OxmlElement("w:shd")
        background.set(qn("w:fill"), "E8F0F2")
        cell._tc.get_or_add_tcPr().append(background)
        cell.paragraphs[0].add_run(label).bold = True
    for week in weeks:
        week_label = f"M{week['minggu']:02d}\nA {date_range(week['A'])}\nB {date_range(week['B'])}"
        for i in week["pdp"] or [None]:
            if i is None:
                values = (week_label, week["catatan"], "", "", "")
            else:
                row = rows[i]
                values = (
                    week_label, f"PdP {i:03d}\n{row['unit']}\n{row['title']}",
                    f"SK {row['sk']}\nSP {', '.join(row['standards'])}",
                    row["pbd"], f"m/s {row['pages']}\n{row['minutes']} minit",
                )
            line = table.add_row()
            line._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell, width, value in zip(line.cells, widths, values, strict=True):
                cell.width = Mm(width)
                cell.text = value
    doc.save(path)


def render_rph(stream, row, renderer, *, teacher=None):
    teacher = teacher or {}
    session = "  ".join(
        f"{label}: {teacher.get(key) or '______'}"
        for key, label in (("class", "Kelas"), ("date", "Tarikh"),
                           ("time", "Masa"), ("students", "Bil. murid"))
    )
    heading = ("Rancangan Pengajaran Harian", "Sains · Tahun 6 SK · 2027", row["title"])
    details = [
        ("Unit", row["unit"]),
        ("Nombor dan tempoh", f"PdP {row['id']:03d} · {row['minutes']} minit"),
        ("Julat RPT", row["dates"]),
        ("Kelas, tarikh dan masa", session),
        ("Standard", f"SK {row['sk']} · SP {', '.join(row['standards'])}"),
        ("Buku teks", f"Buku Teks Sains Tahun 6 SK, m/s {row['pages']}"),
        ("Objektif", row["objective"]),
        ("Bahan", row["materials"]),
    ]
    if row["safety"]:
        details.append(("Panduan aktiviti", row["safety"]))
    activities = [("Fasa", "Guru", "Murid"), *row["phases"]]
    evidence = [
        ("Evidens PBD", row["pbd"]),
        ("Refleksi", teacher.get("reflection") or
         "___ daripada ___ murid mencapai objektif. Tindakan susulan: ____________________"),
    ]
    renderer(stream, heading, details, activities, evidence)


def export_rph(output, row):
    stem = f"CikguLaju_RPH_Sains_SK_T6_PdP_{row['id']:03d}"
    for suffix, renderer in (("docx", _word), ("pdf", _pdf)):
        with (output / f"{stem}.{suffix}").open("wb") as stream:
            render_rph(stream, row, renderer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    weeks, rows = build_source()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        export_rpt(args.output / f"{RPT_STEM}.docx", weeks, rows)
        for row in rows.values():
            export_rph(args.output, row)
    print(f"{len(rows)} PdP Sains Tahun 6, 96 SP dan 64 jam disahkan pada sumber semakan.")


if __name__ == "__main__":
    main()
