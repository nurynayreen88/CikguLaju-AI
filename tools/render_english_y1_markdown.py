"""Export an existing English Year 1 standalone Markdown RPH to a review PDF.

This utility does not modify Telegram handlers or legacy databases.
Usage: python tools/render_english_y1_markdown.py 16
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from english_standalone_adapter import load_english_y1_rph

OUT = ROOT / "output" / "english_y1_standalone_preview"
STYLE = ParagraphStyle("rph-body", fontName="Helvetica", fontSize=8, leading=10, spaceAfter=3)
HEAD = ParagraphStyle("rph-head", parent=STYLE, fontName="Helvetica-Bold", fontSize=10, leading=12, spaceBefore=5)


def render(lesson_no):
    source = load_english_y1_rph(lesson_no)
    if source is None:
        raise ValueError(f"Standalone lesson unavailable: {lesson_no}")
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"english_y1_lesson_{int(lesson_no):03d}_preview.pdf"
    story = []
    for line in source.splitlines():
        line = line.strip()
        if not line:
            continue
        heading = line.startswith("#")
        line = line.lstrip("# ").replace("**", "")
        story.append(Paragraph(escape(line), HEAD if heading else STYLE))
        if heading:
            story.append(Spacer(1, 2 * mm))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(13 * mm, 8 * mm, "CIKGULAJU AI - STANDALONE REVIEW ONLY")
        canvas.restoreState()
    doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=13*mm,
                            rightMargin=13*mm, topMargin=12*mm, bottomMargin=12*mm)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return target


if __name__ == "__main__":
    number = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    print(render(number))
