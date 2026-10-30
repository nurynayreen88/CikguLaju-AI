"""Generate staging-only DOCX and PDF smoke outputs for all Year 4 lessons.

Run: python scripts/batch_smoke_english_year4_exports.py --output-dir /tmp/year4-batch
These files are for QA only; they are not approved bot outputs.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from smoke_english_year4_exports import source_lines, classroom_lines, make_docx, make_pdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for lesson in range(1, 161):
        lines = classroom_lines(source_lines(lesson))
        make_docx(lines, args.output_dir / f"year4_{lesson:03d}_SMOKE.docx")
        make_pdf(lines, args.output_dir / f"year4_{lesson:03d}_SMOKE.pdf")
    docx_files = list(args.output_dir.glob("year4_*_SMOKE.docx"))
    pdf_files = list(args.output_dir.glob("year4_*_SMOKE.pdf"))
    if len(docx_files) != 160 or len(pdf_files) != 160:
        raise RuntimeError(f"Unexpected output count: {len(docx_files)} DOCX, {len(pdf_files)} PDF")
    print("GENERATED: 160 draft DOCX and 160 draft PDF smoke files")
    print("NOT VERIFIED: page layout, audio, pedagogical QA, Telegram integration")


if __name__ == "__main__":
    main()
