"""Offline staging-only DOCX/PDF smoke test for Year 4 standalone RPH.

Usage: python scripts/smoke_english_year4_exports.py --lesson 1 --output-dir /tmp/year4-smoke
Requires python-docx and reportlab. Does not import app.py, access DB or Telegram,
or change any repository files. This is NOT a live-bot integration test.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rph_standalone" / "english" / "year4"


def plain_markdown(line: str) -> str:
    return re.sub(r"\\*\\*|\\*|\\`", "", line).strip()


def source_lines(lesson: int) -> list[str]:
    if not 1 <= lesson <= 160:
        raise ValueError("lesson must be 1..160")
    source = BASE / f"lesson_{lesson:03d}.md"
    if not source.is_file():
        raise FileNotFoundError(source)
    return source.read_text(encoding="utf-8").splitlines()


def make_docx(lines: list[str], destination: Path) -> None:
    from docx import Document
    from docx.shared import Cm, Pt

    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(1.6)
    section.bottom_margin = Cm(1.6)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)
    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9)
    normal.paragraph_format.space_after = Pt(2)
    for raw in lines:
        if not raw.strip():
            continue
        if raw.startswith("# "):
            document.add_heading(plain_markdown(raw[2:]), level=1)
        elif raw.startswith("## "):
            document.add_heading(plain_markdown(raw[3:]), level=2)
        else:
            document.add_paragraph(plain_markdown(raw.lstrip("- ")))
    document.save(destination)


def make_pdf(lines: list[str], destination: Path) -> None:
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Year4Body", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, spaceAfter=3, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="Year4Title", parent=styles["Heading1"], fontSize=13, leading=15, spaceAfter=6))
    styles.add(ParagraphStyle(name="Year4Stage", parent=styles["Heading2"], fontSize=9.5, leading=12, spaceBefore=5, spaceAfter=3, textColor=colors.black))
    story = []
    for raw in lines:
        if not raw.strip():
            continue
        if raw.startswith("# "):
            style, value = styles["Year4Title"], raw[2:]
        elif raw.startswith("## "):
            style, value = styles["Year4Stage"], raw[3:]
        else:
            style, value = styles["Year4Body"], raw.lstrip("- ")
        story.append(Paragraph(escape(plain_markdown(value)), style))
    doc = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=38, leftMargin=38, topMargin=35, bottomMargin=35)
    doc.build(story)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lesson", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    lines = source_lines(args.lesson)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    docx = args.output_dir / f"year4_lesson_{args.lesson:03d}_SMOKE.docx"
    pdf = args.output_dir / f"year4_lesson_{args.lesson:03d}_SMOKE.pdf"
    make_docx(lines, docx)
    make_pdf(lines, pdf)
    if docx.stat().st_size < 1000 or pdf.stat().st_size < 1000:
        raise RuntimeError("Unexpectedly small output")
    print(f"SMOKE OUTPUT CREATED: {docx} ({docx.stat().st_size} bytes)")
    print(f"SMOKE OUTPUT CREATED: {pdf} ({pdf.stat().st_size} bytes)")
    print("STAGING-ONLY: visual QA, 1-page layout, audio and bot integration NOT verified")


if __name__ == "__main__":
    main()
