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
    return line.replace("**", "").replace("*", "").replace("`", "").strip()


def source_lines(lesson: int) -> list[str]:
    if not 1 <= lesson <= 160:
        raise ValueError("lesson must be 1..160")
    source = BASE / f"lesson_{lesson:03d}.md"
    if not source.is_file():
        raise FileNotFoundError(source)
    return source.read_text(encoding="utf-8").splitlines()



# QA-only metadata must never be mistaken for classroom content.
QA_SECTION_MARKERS = (
    "source mapping", "source audio", "direct textbook verification",
    "verified mapping", "verified source", "sow direct verification",
    "verification notes", "audit", "source verification",
)
QA_FIELD_MARKERS = ("**status:**", "**qa status:**", "**verification:**", "**source:**", "**sow:**", "**references:**")


def classroom_lines(lines: list[str]) -> list[str]:
    """Keep teaching instructions; omit audit appendices and release flags."""
    result: list[str] = []
    in_qa_section = False
    for line in lines:
        if line.startswith("## "):
            heading = line[3:].lower()
            in_qa_section = any(marker in heading for marker in QA_SECTION_MARKERS)
        if in_qa_section:
            continue
        if line.strip().lower().startswith(QA_FIELD_MARKERS):
            continue
        # Preserve track numbers while omitting internal audio-verification notes.
        line = re.sub(r"; CD1 designation in draft remains pending independent TB/audio verification", "", line, flags=re.IGNORECASE)
        result.append(line)
    return result


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
    normal.paragraph_format.line_spacing = 1.0
    for style_name, size, before, after in (("Heading 1", 12, 0, 4), ("Heading 2", 9.5, 4, 2)):
        style = document.styles[style_name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
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
    from reportlab.platypus import SimpleDocTemplate, Paragraph

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_candidates = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    )
    font_path = next((p for p in font_candidates if p.is_file()), None)
    if font_path is None:
        raise RuntimeError("Unicode PDF font unavailable; refusing potentially broken preview")
    pdfmetrics.registerFont(TTFont("Year4Unicode", str(font_path)))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Year4Body", parent=styles["Normal"], fontName="Year4Unicode", fontSize=8.5, leading=11, spaceAfter=3, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="Year4Title", parent=styles["Heading1"], fontName="Year4Unicode", fontSize=12, leading=14, spaceAfter=4))
    styles.add(ParagraphStyle(name="Year4Stage", parent=styles["Heading2"], fontName="Year4Unicode", fontSize=9.5, leading=11, spaceBefore=3, spaceAfter=2, textColor=colors.black))
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
    lines = classroom_lines(source_lines(args.lesson))
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
