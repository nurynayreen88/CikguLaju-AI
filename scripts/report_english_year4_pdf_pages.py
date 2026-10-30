"""Report PDF page counts for 160 draft Year 4 export smoke files.

Run after batch_smoke_english_year4_exports.py.
This is a diagnostic, not a release approval.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for lesson in range(1, 161):
        path = args.input_dir / f"year4_{lesson:03d}_SMOKE.pdf"
        if not path.is_file():
            raise FileNotFoundError(path)
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        if pages < 1:
            raise ValueError(f"Empty PDF: {path}")
        rows.append((lesson, pages, "REVIEW" if pages != 1 else "ONE_PAGE"))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lesson", "pdf_pages", "layout_status"))
        writer.writerows(rows)
    multi = [n for n, pages, _ in rows if pages > 1]
    print(f"Generated {len(rows)} PDF page-count records")
    print(f"One-page PDF: {160 - len(multi)}; multi-page PDF: {len(multi)}")
    if multi:
        print("Needs A4 layout review:", ", ".join(map(str, multi)))
    print("NOTE: one PDF page does not prove visual quality or DOCX page count")


if __name__ == "__main__":
    main()
