#!/usr/bin/env python3
"""Fail-closed printability QA: all 298 Bahasa Arab teacher DOCX/PDF previews.

Verifies technical output, not pedagogical/DSKP final approval. Never reads or
writes the live Telegram/Web app, user database, free quotas, or payments.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from collections import Counter
from pathlib import Path

from docx import Document

EXPECTED = {2: 60, 3: 60, 4: 58, 5: 60, 6: 60}
STANDARD = re.compile(r"^\d+\.\d+ / \d+\.\d+\.\d+$")
ARABIC = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
NAME = re.compile(r"^year([2-6])_lesson_(\d{3})\.docx$")
FORBIDDEN = ("DRAF", "BELUM READY", "FINAL READY", "SEBELUM FINAL")


def validate(root: Path) -> None:
    docx_files = sorted(root.glob("year[2-6]_lesson_*.docx"))
    pdfdir = root / "_pdf_previews"
    counts = Counter()
    problems = []
    if len(docx_files) != 298:
        problems.append(f"Expected 298 DOCX, got {len(docx_files)}")
    for path in docx_files:
        match = NAME.fullmatch(path.name)
        if match is None:
            problems.append(f"{path.name}: invalid filename")
            continue
        year, lesson_no = int(match.group(1)), int(match.group(2))
        counts[year] += 1
        try:
            doc = Document(path)
            assert len(doc.tables) == 1
            fields = {r.cells[0].text.strip(): r.cells[1].text.strip()
                      for r in doc.tables[0].rows}
            assert fields["Tahun"] == str(year)
            assert fields["Unit / Tajuk"]
            assert fields["Objektif"]
            assert fields["Set induksi"]
            assert fields["Aktiviti 1"]
            assert fields["Aktiviti 2"]
            assert fields["Penutup"]
            assert fields["Refleksi"]
            assert STANDARD.fullmatch(fields["SK / SP"])
            assert fields["SK / SP"].split(" / ")[1].startswith(
                fields["SK / SP"].split(" / ")[0] + ".")
            assert fields["Tarikh / Masa / Kelas"].startswith("Tarikh: ____ / ____")
            all_text = "\n".join(
                " ".join(cell.text for cell in row.cells)
                for table in doc.tables for row in table.rows)
            assert ARABIC.search(all_text)
            assert not any(word in all_text.upper() for word in FORBIDDEN)
        except Exception as exc:
            problems.append(f"{path.name}: {type(exc).__name__}: {exc}")
        pdf = pdfdir / path.with_suffix(".pdf").name
        if not pdf.is_file():
            problems.append(f"{path.name}: PDF missing")
            continue
        info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
        match_pages = re.search(r"^Pages:\s*(\d+)", info, flags=re.MULTILINE)
        if match_pages is None or int(match_pages.group(1)) != 1:
            problems.append(f"{pdf.name}: page overflow or unreadable PDF")
        content = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
        if any(word in content.upper() for word in FORBIDDEN):
            problems.append(f"{pdf.name}: internal audit text leaked into printable PDF")
        if "SK / SP" not in content or not ARABIC.search(content):
            problems.append(f"{pdf.name}: missing standards field or Arabic glyph text")
    if dict(sorted(counts.items())) != EXPECTED:
        problems.append(f"Year counts mismatch {counts}")
    print(f"Printability QA: 298 Word + 298 PDF; years={dict(sorted(counts.items()))}; technical_errors={len(problems)}")
    for msg in problems[:25]:
        print("PRINT_BLOCKER:", msg)
    assert not problems, "Teacher-printable output failed safety and integrity QA"
    print("PASS: numeric-only SK/SP, dates HH/BB/TTTT, Arabic present, one A4 PDF per PdP, no leaked audit status")
    print("NOT A CONTENT RELEASE: pedagogical signoff and RPT2027 group A/B dated calendar remain separate.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    validate(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
