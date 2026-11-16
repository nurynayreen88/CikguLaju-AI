"""Assemble the October English SK RPT and integrated RPH review copies."""

import argparse
from collections import Counter
from pathlib import Path
from shutil import copyfile
from subprocess import run
from tempfile import TemporaryDirectory

import fitz

from tools.build_english_paired_rph_2027 import paired_plan_index
from tools.build_english_rpt_2027_review import SOURCE, schedule
from web.english_integrated_rph_2027 import filename, render


def assert_a4_page(pdf, lesson_label):
    if len(pdf) != 1:
        raise ValueError(f"{lesson_label} uses {len(pdf)} pages")
    page = pdf[0]
    if abs(page.rect.width - 595.28) > 1 or abs(page.rect.height - 841.89) > 1:
        raise ValueError(f"{lesson_label} is not A4")
    if lesson_label not in page.get_text():
        raise ValueError(f"{lesson_label} is missing from {page.parent.name}")


def build_bundle(output):
    output.mkdir(parents=True, exist_ok=False)
    counts = Counter()
    rph_folders = {}
    for year in range(2, 7):
        folder = output / f"Year_{year}"
        folder.mkdir()
        rph_folder = folder / "RPH"
        rph_folder.mkdir()
        rph_folders[year] = rph_folder
        rpt = SOURCE / f"RPT_English_SK_2027_Year_{year}_A_B.pdf"
        with fitz.open(rpt) as pdf:
            calendar = pdf[1].get_text() + pdf[2].get_text()
            sessions = [pair for _, _, _, week in schedule(year) for pair in week]
            if len(sessions) != 142 or [n for pair in sessions for n in pair] != list(range(1, 161)):
                raise ValueError(f"Incomplete RPT for Year {year}")
            for pair in sessions:
                if len(pair) == 2 and f"{pair[0]:03d}+{pair[1]:03d}" not in calendar:
                    raise ValueError(f"RPT lacks Year {year} pair {pair}")
        copyfile(rpt, folder / rpt.name)

    for (year, number), plan in paired_plan_index().items():
        pair = tuple(lesson[0] for lesson in plan[-1])
        if number != pair[0]:
            continue
        folder = rph_folders[year]
        label = f"Lesson {pair[0]:03d} + {pair[1]:03d}"
        word = folder / filename(year, pair, "word")
        pdf = folder / filename(year, pair, "pdf")
        word.write_bytes(render(year, number, "word", {}))
        pdf.write_bytes(render(year, number, "pdf", {}))
        with fitz.open(pdf) as document:
            assert_a4_page(document, label)
        counts[year] += 1

    if counts != {year: 18 for year in range(2, 7)}:
        raise ValueError(f"Incomplete RPH review package: {counts}")
    with TemporaryDirectory() as temp:
        rendered = Path(temp)
        for folder in rph_folders.values():
            word_files = sorted(folder.glob("*.docx"))
            run(
                ["libreoffice", f"-env:UserInstallation={(rendered / 'profile').as_uri()}",
                 "--headless", "--convert-to", "pdf", "--outdir", str(rendered),
                 *map(str, word_files)],
                check=True,
                capture_output=True,
                text=True,
            )
            for word in word_files:
                first, last = word.stem.rsplit("_L", 1)[1].split("-")
                with fitz.open(rendered / f"{word.stem}.pdf") as pdf:
                    assert_a4_page(pdf, f"Lesson {first} + {last}")

    (output / "BACA_DULU.txt").write_text(
        "RPT dan RPH English SK 2027 Year 2–6 untuk semakan guru\n\n"
        "Setiap folder mengandungi satu RPT Kumpulan A dan B serta 18 RPH bersepadu. "
        "Satu pasangan Lesson menggunakan satu RPH 60 minit. Fail Word boleh disunting.\n"
        "Untuk sesi satu Lesson, rujuk RPH asal nombor Lesson dalam CikguLaju.\n"
        "Year 5 mengandungi 18 RPH dan 36 rujukan SOW untuk semakan sebelum pengesahan.\n",
        encoding="utf-8",
    )
    print("5 RPT PDFs, 90 Word RPH and 90 native PDF RPH. Both RPH formats verified as one A4 page.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    build_bundle(parser.parse_args().output)
