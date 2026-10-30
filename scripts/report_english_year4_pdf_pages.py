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
    parser.add_argument("--fail-on-multipage", action="store_true", help="Optional strict one-page gate")
    args = parser.parse_args()
    rows = []
    missing_text = []
    for lesson in range(1, 161):
        path = args.input_dir / f"year4_{lesson:03d}_SMOKE.pdf"
        if not path.is_file():
            raise FileNotFoundError(path)
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        if pages < 1:
            raise ValueError(f"Empty PDF: {path}")
        extracted = "\\n".join(page.extract_text() or "" for page in reader.pages)
        if "English Year 4" not in extracted:
            missing_text.append(lesson)
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
    if missing_text:
        raise SystemExit(f"FAILED PDF text extraction for lessons: {missing_text}")
    if args.fail_on_multipage and multi:
        raise SystemExit(f"FAILED one-page target: {len(multi)} lessons require layout review")


if __name__ == "__main__":
    main()
