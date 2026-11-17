"""Eksport RPT dan RPH Sains SK Tahun 5 untuk semakan guru."""

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
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import checked_book_pages
from tools.sains_y5_kssr2017_official_sp_statements_20261107 import checked_statements
from web.sains_y5_83_activity_bank_draf_20261107 import BANK


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("agihan_2027.json")
SPECIFIC = Path(__file__).with_name("aktiviti_khusus.json")
CALENDAR = ROOT / "rpt_2027/takwim_pdp_2027_ab_draf.json"
RPT_STEM = "CikguLaju_RPT_Sains_SK_Tahun5_2027_Semakan_Guru"
DURATIONS = {30: (3, 7, 8, 9, 3), 60: (5, 16, 19, 15, 5)}
PHASES = ("Set induksi", "Aktiviti 1", "Aktiviti 2", "Pentaksiran PBD", "Penutup")
FIELDS = {
    "materials", "induction_teacher", "induction_pupils", "guide_teacher", "guide_pupils",
    "pbd_teacher", "pbd",
}

# Pembetulan atau penyesuaian amali bagi sumber bank 83 SP.
ACTIVITY_UPDATES = {
    "2.2.1": {
        "teacher1": "memodelkan jantung sebagai pam, salur darah sebagai laluan dan peparu sebagai tempat pertukaran gas",
        "pupil1": "menandakan lokasi jantung, peparu dan salur darah pada rajah",
        "teacher2": "membimbing padanan fungsi jantung, salur darah, peparu dan darah",
        "pupil2": "menulis satu fungsi bagi setiap bahagian dan menyemak padanan menggunakan rajah",
        "pbd": "Empat padanan fungsi jantung, salur darah, peparu dan darah pada rajah individu",
    },
    "2.2.2": {
        "teacher1": "menjejak laluan jantung–peparu–jantung dan jantung–badan–jantung dengan kad anak panah",
        "pupil1": "memasang anak panah bagi kedua-dua gelung pada model",
        "teacher2": "menunjukkan darah lebih oksigen yang kembali dari peparu dan darah lebih karbon dioksida yang kembali dari badan",
        "pupil2": "melakar kedua-dua gelung dan melabelkan darah yang kembali ke jantung",
        "pbd": "Dua gelung lengkap dengan arah yang tepat serta label darah lebih oksigen dan lebih karbon dioksida",
    },
    "3.1.3": {
        "hook": "Gambar kerbau berkubang dan haiwan yang berhibernasi",
        "teacher1": "membandingkan cabaran hidup dalam cuaca panas dan musim sejuk",
        "pupil1": "memadankan kerbau berkubang dengan cuaca panas dan hibernasi dengan musim sejuk",
        "teacher2": "membimbing penerangan tentang cara tingkah laku membantu haiwan menghadapi cuaca melampau",
        "pupil2": "melengkapkan jadual cuaca, tingkah laku dan faedah untuk dua contoh",
        "pbd": "Dua contoh tingkah laku dan penerangan tentang cara ia membantu haiwan menghadapi panas atau sejuk",
        "materials": "Kad kerbau, imej haiwan berhibernasi dan jadual perbandingan",
    },
    "3.3.5": {
        "teacher1": "mengedarkan dua set kad hubungan makanan yang dipadankan dengan sawah dan kolam",
        "pupil1": "menggabungkan dua rantai bagi setiap habitat pada kertas carta",
        "teacher2": "meminta kumpulan menyemak arah anak panah dan hidupan yang terdapat dalam lebih satu rantai",
        "pupil2": "menerangkan satu perkaitan dalam setiap siratan dan menyiapkan satu lakaran sendiri",
        "pbd": "Dua siratan ringkas daripada habitat berbeza, dengan pengeluar, pengguna dan anak panah dari makanan kepada pemakan",
    },
    "5.2.5": {
        "teacher1": "menunjukkan susunan sel kering sejenis pada kit litar bersiri dan selari yang serasi dengan kadaran mentol",
        "pupil1": "meramal perubahan kecerahan apabila bilangan sel ditambah pada bekalan",
        "teacher2": "menyelia perbandingan dengan bilangan dan jenis mentol yang sama bagi setiap susunan litar",
        "pupil2": "merekod kecerahan bagi setiap bilangan sel dan membandingkan dapatan kedua-dua jenis litar",
        "pbd": "Jadual kecerahan dua bilangan sel kering bagi litar bersiri dan litar selari serta rumusan bersandarkan bacaan",
    },
    "6.1.4": {
        "teacher1": "menyediakan air suam dan termometer digital serta menunjukkan cara merekod suhu bilik",
        "pupil1": "mencatat suhu air pada sela masa tetap dan membandingkannya dengan suhu bilik",
        "teacher2": "membekalkan rekod bersiri tambahan untuk menunjukkan perubahan apabila air hampir pada suhu bilik",
        "pupil2": "memplot bacaan, melabel suhu bilik dan menerangkan arah pemindahan haba",
        "pbd": "Graf suhu melawan masa, suhu bilik yang dilabel dan rumusan bahawa air yang lebih panas menyejuk ke arah suhu bilik",
        "materials": "Air suam disediakan guru, dua termometer digital, jam randik dan kertas graf",
        "safety": "Gunakan air suam yang disediakan guru dan letakkan bekas di permukaan stabil.",
    },
    "6.1.5": {
        "teacher1": "menunjukkan susunan yang sudah siap dengan belon dan botol dalam air suam",
        "pupil1": "membandingkan saiz belon sebelum dan selepas udara dalam botol dipanaskan",
        "teacher2": "memindahkan botol ke air sejuk dan meminta murid melakar perubahan kedua",
        "pupil2": "membandingkan dapatan pemanasan dengan penyejukan dan melabel pengembangan serta pengecutan",
        "pbd": "Dua lakaran yang mengaitkan haba diterima dengan pengembangan udara dan haba dilepaskan dengan pengecutan",
    },
    "7.1.3": {
        "teacher1": "menyelia pelabelan tiga set paku besi yang membezakan pendedahan kepada air dan udara",
        "pupil1": "mencatat keadaan awal, tiga jenis pemboleh ubah dan hipotesis pada jadual",
        "teacher2": "menunjukkan set yang sudah disediakan beberapa hari lebih awal dan menerangkan cara menjadualkan pemerhatian susulan",
        "pupil2": "merekod tanda karat daripada set rujukan dan merancang perbandingan ulangan bagi set sendiri",
        "pbd": "Rekod keadaan awal, kawalan yang sepadan serta rumusan berpandukan hasil perbandingan set rujukan",
    },
    "8.2.1": {
        "teacher1": "menyelaras pemerhatian ais mencair dan titisan terbentuk pada bekas sejuk",
        "pupil1": "merekod dua perubahan yang diperhatikan pada stesen",
        "teacher2": "memberi kad gambar bersiri atau rakaman pembekuan, penyejatan dan pendidihan",
        "pupil2": "menyusun kad, menamakan lima proses dan membezakan pemerhatian langsung daripada yang ditunjukkan melalui rakaman",
        "pbd": "Dua pemerhatian dan rajah dengan label peleburan, pembekuan, penyejatan, pendidihan dan kondensasi",
        "materials": "Ais, bekas sejuk, kad keadaan air dan rakaman demonstrasi guru",
    },
    "8.2.2": {
        "teacher1": "membandingkan ais yang mencair dengan wap air yang terkondensasi pada permukaan sejuk",
        "pupil1": "merekod dua perubahan dan menggunakan anak panah untuk menunjukkan arah pemindahan haba",
        "teacher2": "memberi rekod pembekuan, penyejatan dan pendidihan untuk dilengkapkan pada rajah",
        "pupil2": "mengelaskan kelima-lima proses kepada menerima atau kehilangan haba serta menerangkan satu contoh",
        "pbd": "Peleburan, penyejatan dan pendidihan menerima haba. Pembekuan dan kondensasi kehilangan haba. Murid memberi satu sebab berdasarkan pemerhatian.",
        "materials": "Ais, bekas sejuk, kad proses dan rekod demonstrasi guru",
    },
}


def sentence(text):
    return text[0].upper() + text[1:].rstrip(".") + "."


def specific_plan(item):
    if set(item) != FIELDS or not all(value.strip() for value in item.values()):
        raise ValueError("Incomplete KPS or consolidation activity")
    actions = (
        (item["induction_teacher"], item["induction_pupils"]),
        (item["guide_teacher"], item["guide_pupils"]),
        ("Beri lembaran individu. Minta murid menggunakan contoh daripada aktiviti.", item["pbd"]),
        (item["pbd_teacher"], "Serahkan evidens individu dan terangkan satu dapatan."),
        ("Minta murid menyatakan satu langkah yang boleh diulang.", "Nyatakan satu perkara yang penting dalam tugas ini."),
    )
    return item["pbd"], item["materials"], "", actions


def bank_plan(sp):
    lesson = {**BANK[sp], **ACTIVITY_UPDATES.get(sp, {})}
    hook = lesson["hook"]
    actions = (
        (f"Tunjukkan {hook[0].lower() + hook[1:]}.", "Nyatakan satu pemerhatian atau ramalan."),
        (sentence(lesson["teacher1"]), sentence(lesson["pupil1"])),
        (sentence(lesson["teacher2"]), sentence(lesson["pupil2"])),
        ("Semak hasil individu mengikut kriteria PBD.", f"Serahkan evidens individu. {lesson['pbd']}."),
        ("Minta murid mengaitkan bukti dengan tajuk.", "Jelaskan satu dapatan dengan bukti daripada aktiviti."),
    )
    return lesson["pbd"], lesson["materials"], lesson["safety"], actions


def expand_pages(reference):
    if not re.fullmatch(r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*", reference):
        raise ValueError(f"Invalid printed-page reference: {reference}")
    pages = set()
    for span in reference.split(","):
        limits = list(map(int, span.split("-")))
        if not 1 <= limits[0] <= limits[-1] <= 230:
            raise ValueError(f"Out-of-range printed pages: {reference}")
        pages.update(range(limits[0], limits[-1] + 1))
    return pages


def build_source():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    custom = {int(i): value for i, value in json.loads(SPECIFIC.read_text(encoding="utf-8")).items()}
    calendar = json.loads(CALENDAR.read_text(encoding="utf-8"))["minggu"]
    content_standards = checked_statements()
    book_pages = checked_book_pages()
    rows = {row["id"]: row for row in data["pdp"]}
    if list(rows) != list(range(1, 117)) or len(rows) != len(data["pdp"]):
        raise ValueError("Expected 116 unique source PdP in order")

    sequence, custom_ids, core_codes, reviews = [], set(), set(), 0
    weeks = data["minggu"]
    for week, original in zip(weeks, calendar, strict=True):
        number = week["minggu"]
        expected_a = ["2027-03-15", "2027-03-18"] if number == 10 else original["A"]
        if number != original["minggu"] or week["A"] != expected_a or week["B"] != original["B"]:
            raise ValueError(f"Unexpected calendar window M{number:02d}")
        ids = week["pdp"]
        if bool(ids) != (number <= 38 and number not in (6, 18, 19)) or len(ids) > 4:
            raise ValueError(f"Invalid teaching slots M{number:02d}")
        if sum(rows[i]["minutes"] for i in ids) > (90 if number in data["minggu_pendek"] else 120):
            raise ValueError(f"Excess minutes M{number:02d}")
        for i in ids:
            row = rows[i]
            sp = row["sp"]
            is_kps = sp.startswith("1.1.")
            if not row["unit"].startswith(f"Unit {sp.split('.')[0]}:"):
                raise ValueError(f"Unexpected unit for PdP {i:03d}")
            if row["review"] != (sp in core_codes):
                raise ValueError(f"Unexpected core or review identity for PdP {i:03d}")
            core_codes.add(sp)
            reviews += row["review"]
            pages = expand_pages(row["pages"])
            if row["review"] or is_kps:
                custom_ids.add(i)
                pbd, materials, safety, actions = specific_plan(custom[i])
            else:
                pbd, materials, safety, actions = bank_plan(sp)
                if not pages & set(book_pages[sp]["printed_pages"]):
                    raise ValueError(f"Missing audited textbook context for PdP {i:03d}")
            row.update(
                sk=sp.rsplit(".", 1)[0], week=number,
                dates=f"A {date_range(week['A'])} · B {date_range(week['B'])}",
                objective=pbd, pbd=pbd, materials=materials, safety=safety,
            )
            row["phases"] = [
                (f"{phase} · {minutes} minit", teacher, pupils)
                for phase, minutes, (teacher, pupils) in zip(PHASES, DURATIONS[row["minutes"]], actions, strict=True)
            ]
            sequence.append(i)
    if sequence != list(rows) or custom_ids != set(custom) or len(custom) != 33 or reviews != 21:
        raise ValueError("RPT, core, KPS and consolidation sequence must match")
    if core_codes != set(content_standards) | {f"1.1.{i}" for i in range(1, 13)} or len(core_codes) != 95:
        raise ValueError("Source standards differ from DSKP inventory")
    if sorted(row["minutes"] for row in rows.values()) != [30] * 104 + [60] * 12:
        raise ValueError("RPT must maintain the 64-hour allocation")
    return weeks, rows


def date_range(values):
    return "–".join(date.fromisoformat(value).strftime("%d/%m") for value in values)

def export_rpt(path, weeks, rows):
    doc = Document()
    doc.core_properties.title = "Rancangan Pengajaran Tahunan Sains Tahun 5 Sekolah Kebangsaan 2027"
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
    footer.text = "Sains Tahun 5 SK 2027    •    Halaman "
    page_field = OxmlElement("w:fldSimple")
    page_field.set(qn("w:instr"), "PAGE")
    footer._p.append(page_field)
    doc.add_paragraph("Rancangan Pengajaran Tahunan Sains Tahun 5 2027", "Title")
    doc.add_paragraph("Sekolah Kebangsaan · KSSR Semakan 2017 · Kumpulan A dan B")
    profile = doc.add_table(rows=3, cols=2)
    profile.style = "Table Grid"
    for line, label in zip(profile.rows, ("Nama sekolah", "Nama guru", "Logo sekolah"), strict=True):
        line.cells[0].text = label
        if label == "Logo sekolah":
            line.height = Mm(24)
            line.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
        else:
            line.cells[1].text = "__________________________________"
    doc.add_heading("Peruntukan PdP", 1)
    doc.add_paragraph("116 PdP dalam 10 unit, dengan 104 sesi 30 minit dan 12 sesi 60 minit. Jumlah 64 jam.")
    doc.add_paragraph("Gunakan julat Kumpulan A atau B mengikut sekolah. Pilih slot PdP sebenar mengikut jadual waktu, cuti negeri dan tarikh UASA sekolah.")
    doc.add_paragraph("Kumpulan A meliputi Kedah, Kelantan dan Terengganu. Kumpulan B meliputi negeri lain dan Wilayah Persekutuan.")
    doc.add_paragraph("Sumber: Kalendar Akademik KPM 2027, DSKP Sains Tahun 5 dan Buku Teks Sains Tahun 5 SK, DBP 2020.")
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
                    f"SK {row['sk']}\nSP {row['sp']}",
                    row["pbd"], f"m/s {row['pages']}\n{row['minutes']} minit",
                )
            line = table.add_row()
            line._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell, width, value in zip(line.cells, widths, values, strict=True):
                cell.width = Mm(width)
                cell.text = value
    doc.save(path)


def export_rph(output, row):
    heading = ("Rancangan Pengajaran Harian", "Sains · Tahun 5 SK · 2027", row["title"])
    details = [
        ("Unit", row["unit"]),
        ("Nombor dan tempoh", f"PdP {row['id']:03d} · {row['minutes']} minit"),
        ("Julat RPT", row["dates"]),
        ("Kelas, tarikh dan masa", "Kelas: ______  Tarikh: ______  Masa: ______  Bil. murid: ______"),
        ("Standard", f"SK {row['sk']} · SP {row['sp']}"),
        ("Buku teks", f"Buku Teks Sains Tahun 5 SK, m/s {row['pages']}"),
        ("Objektif", row["objective"]),
        ("Bahan", row["materials"]),
    ]
    if row["safety"]:
        details.append(("Panduan aktiviti", row["safety"]))
    activities = [("Fasa", "Guru", "Murid"), *row["phases"]]
    evidence = [
        ("Evidens PBD", row["pbd"]),
        ("Refleksi", "___ daripada ___ murid mencapai objektif. Tindakan susulan: ____________________"),
    ]
    stem = f"CikguLaju_RPH_Sains_SK_T5_PdP_{row['id']:03d}"
    for suffix, renderer in (("docx", _word), ("pdf", _pdf)):
        with (output / f"{stem}.{suffix}").open("wb") as stream:
            renderer(stream, heading, details, activities, evidence)


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
    print(f"{len(rows)} PdP Sains Tahun 5, 95 SP dan 64 jam disahkan pada sumber semakan.")


if __name__ == "__main__":
    main()
