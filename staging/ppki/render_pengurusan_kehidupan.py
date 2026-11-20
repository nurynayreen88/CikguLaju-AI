"""Render the reviewed-source PPKI Year 2 pilot lesson plans for local QA."""

import argparse
import csv
from datetime import date
from io import BytesIO
import json
from pathlib import Path

from dlp_year2_rph import _pdf, _word


SOURCE = Path(__file__).with_name("pengurusan_kehidupan_tahun2.json")
RENDERERS = {"docx": _word, "pdf": _pdf}
PPKI_LABEL_FILL = "EEE6F7"


def load_catalog():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def render_lesson(catalog, lesson, extension, teacher):
    lesson_date = teacher.get("date")
    display_date = date.fromisoformat(lesson_date).strftime("%d/%m/%Y") if lesson_date else ""
    sk = lesson["sp"].rsplit(".", 1)[0]
    content = catalog["content_standards"][sk]
    learning = catalog["learning_standards"][lesson["sp"]]
    heading = ("Rancangan Pengajaran Harian", "PPKI · Pengurusan Kehidupan · Tahun 2", lesson["title"])
    details = [
        ("Unit", catalog["unit"]),
        ("PdP", lesson["pdp"]),
        ("Tarikh", display_date),
        ("Masa", teacher.get("time", "")),
        ("Kelas", teacher.get("class", "")),
        ("Bilangan Murid", teacher.get("students", "")),
        ("Standard Kandungan", f"{sk} {content}"),
        ("Standard Pembelajaran", f"{lesson['sp']} {learning}\nFokus: {lesson['focus']}"),
        ("Objektif Pembelajaran", lesson["objective"]),
        ("Bahan Bantu Mengajar", lesson["materials"]),
        ("Rujukan", lesson["book"]),
    ]
    activities = [
        ("Fasa", "Guru", "Murid"),
        ("Set Induksi", *lesson["induction"]),
        ("Aktiviti 1 · Latihan berpandu", *lesson["guided"]),
        ("Aktiviti 2 · Aplikasi", *lesson["practice"]),
        ("Penutup", *lesson["closure"]),
    ]
    assessment = [
        ("Sokongan", lesson["support"]),
        ("Pentaksiran Bilik Darjah", lesson["assessment"]),
        ("Refleksi", f"____ / ____ murid mencapai objektif.\nSusulan: {lesson['follow_up']}"),
    ]
    output = BytesIO()
    RENDERERS[extension](output, heading, details, activities, assessment,
                        compact=True, label_fill=PPKI_LABEL_FILL)
    return output.getvalue()


def export(output, teacher):
    catalog = load_catalog()
    output.mkdir(parents=True, exist_ok=True)
    index_path = output / "RPT_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_SEMAKAN.csv"
    with index_path.open("w", encoding="utf-8-sig", newline="") as stream:
        index = csv.writer(stream)
        index.writerow(("Unit", "PdP", "Tajuk", "SK", "Deskripsi SK", "SP", "Deskripsi SP",
                        "Fokus", "Halaman Buku Teks"))
        for lesson in catalog["lessons"]:
            stem = f"RPH_PPKI_PENGURUSAN_KEHIDUPAN_TAHUN_2_{lesson['pdp']}"
            for extension in RENDERERS:
                path = output / f"{stem}.{extension}"
                path.write_bytes(render_lesson(catalog, lesson, extension, teacher))
            sk = lesson["sp"].rsplit(".", 1)[0]
            index.writerow((catalog["unit"], lesson["pdp"], lesson["title"], sk,
                            catalog["content_standards"][sk], lesson["sp"],
                            catalog["learning_standards"][lesson["sp"]], lesson["focus"],
                            lesson["book"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--date", default="", help="ISO date, YYYY-MM-DD")
    parser.add_argument("--time", default="")
    parser.add_argument("--class", dest="class_name", default="")
    parser.add_argument("--students", type=int)
    args = parser.parse_args()
    export(args.output, {"date": args.date, "time": args.time, "class": args.class_name,
                         "students": str(args.students) if args.students is not None else ""})


if __name__ == "__main__":
    main()
