"""Render one draft English RPH per lesson on A4 for human QA.

Uses ReportLab. Draft watermark and source/proposal labels are mandatory.
Run after merge_english_standalone_activity_proposals.py.
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output" / "english_standalone_supplemented_drafts.json"
OUT = ROOT / "output" / "english_rph_a4_review"
STYLES = {
    "title": ParagraphStyle("TitleRPH", fontName="Helvetica-Bold", fontSize=11, leading=13, alignment=TA_CENTER),
    "meta": ParagraphStyle("MetaRPH", fontName="Helvetica", fontSize=8, leading=10),
    "body": ParagraphStyle("BodyRPH", fontName="Helvetica", fontSize=8, leading=10, spaceAfter=2),
    "small": ParagraphStyle("SmallRPH", fontName="Helvetica-Oblique", fontSize=7, leading=9),
}

def para(value, style="body"):
    return Paragraph(escape(str(value or "Not recorded")), STYLES[style])

def make_pdf(record):
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"English_Y{record['year'].split()[-1]}_Lesson_{record['lesson_no']:03d}_DRAFT.pdf"
    doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=14*mm, rightMargin=14*mm,
                            topMargin=13*mm, bottomMargin=13*mm)
    story = [para("DRAFT RPH - NOT APPROVED FOR BOT RELEASE", "title"), Spacer(1, 5*mm)]
    fields = [
        ("Year / Lesson", f"{record['year']} / {record['lesson_no']} - {record['lesson_name']}"),
        ("Unit", record["unit"]),
        ("Main SK / SP", f"{record['main_sk']} / {record['main_sp']}"),
        ("Complementary SK / SP", f"{record['complementary_sk']} / {record['complementary_sp']}"),
        ("Learning aim (source)", record.get("objective_source", "")),
        ("Evidence of learning", record.get("success_evidence", "")),
    ]
    table = Table([[para(k, "meta"), para(v, "meta")] for k,v in fields], colWidths=[42*mm, 140*mm], hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                               ("BOTTOMPADDING",(0,0),(-1,-1),5),
                               ("LINEBELOW",(0,0),(-1,-1),0.3,colors.lightgrey)]))
    story.extend([table, Spacer(1,4*mm)])
    for activity in record["activities"]:
        proposed = activity.get("provenance") == "TEACHER_DEVELOPED_PROPOSAL_NOT_TB"
        label = activity["phase"] + (" [TEACHER PROPOSAL - UNVERIFIED]" if proposed else " [SOURCE GUIDANCE]")
        story.extend([para(label, "meta"), para(activity["procedure"]), Spacer(1,2*mm)])
    story.append(para(f"Source classification: {record['source']}. All content pending pedagogical and A4 review.", "small"))
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(14*mm, 9*mm, "CIKGULAJU AI - INTERNAL QA DRAFT")
        canvas.drawRightString(196*mm, 9*mm, f"Page {document.page}")
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return target

def main():
    records = json.loads(SOURCE.read_text(encoding="utf-8"))
    outputs = [make_pdf(record) for record in records]
    print(f"Generated {len(outputs)} draft PDFs. Check for overflow/multipage separately.")

if __name__ == "__main__":
    main()
