"""Print-friendly PDF and editable Word for a single Sains Tahun 1 repair sample.

Staging-only CLI: NO Flask route, Telegram delivery, Supabase interaction or
credit mutation. Only the exact hardcoded source sample is accepted.
Teacher-only metadata is intentionally excluded from student artifacts.
"""
import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from docx import Document
from docx.shared import Mm, Pt, RGBColor

SOURCE = (Path(__file__).resolve().parents[1] /
          "supplementary_materials/science/year1/"
          "repair_demo_sk1_1_sp1_1_1_20261112.json")
TITLE = "CIKGULAJU AI  |  SAINS TAHUN 1"
MIME_PDF = "application/pdf"


def source():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert data["visibility"] == "STAGING_INTERNAL"
    assert data["approval"] == "NOT_APPROVED_FOR_PRODUCTION"
    assert data["publish"] is False
    assert data["curriculum"]["year"] == 1
    assert data["curriculum"]["subject"] == "Sains"
    assert (data["curriculum"]["sk"], data["curriculum"]["sp"]) == ("1.1", "1.1.1")
    assert data["curriculum"]["lesson_token"] is None
    assert data["curriculum"]["textbook_page"] is None
    q = data["student_copy"]["questions"]
    assert len(q) == 6
    assert [x["no"] for x in q] == [1, 2, 3, 4, 5, 6]
    for x in q:
        assert x["response_type"] in ("short_text", "checkboxes", "long_text")
        assert x["task"] and len(x["task"]) < 200
        assert x["response_type"] != "checkboxes" or len(x["options"]) in (2, 3, 4)
        assert x["response_type"] == "checkboxes" or 1 <= x["response_lines"] <= 3
    return data


def _pdf_clean(s):
    return str(s).translate(str.maketrans({
        "—": "-", "–": "-", "’": "'", "‘": "'", "•": "-",
        "“": '"', "”": '"', "…": "...", "\u00a0": " "
    }))


def make_pdf(data, target):
    page_w, page_h = A4
    pdf = canvas.Canvas(str(target), pagesize=A4, pageCompression=1)
    pdf.setTitle("CikguLaju Sains Tahun 1 - Saya Memerhati - DUMMY STAGING")
    pdf.setAuthor("CikguLaju AI")
    left, right = 42, 42
    usable = page_w - left - right
    top = page_h - 39
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(left, top, TITLE)
    pdf.setStrokeColor(colors.Color(.65, .68, .67))
    pdf.line(left, top-8, page_w-right, top-8)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(left, top-34, _pdf_clean(data["student_copy"]["title"]).upper())
    pdf.setFont("Helvetica", 9)
    pdf.drawString(left, top-50, _pdf_clean(data["student_copy"]["subtitle"]))
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(left, top-70, "NAMA: __________________________  KELAS: __________  TARIKH: __________")
    materials = "BAHAN: " + ", ".join(data["student_copy"]["materials"])
    for i, part in enumerate(simpleSplit(_pdf_clean(materials), "Helvetica", 8.4, usable)):
        pdf.drawString(left, top - 88 - 12*i, part)
    pdf.setFont("Helvetica", 8.5)
    p = _pdf_clean(data["student_copy"]["instruction"])
    safety = _pdf_clean(data["student_copy"]["safety"])
    y = top - 122
    for text in ("ARAHAN: " + p, "INGAT: " + safety):
        for line in simpleSplit(text, "Helvetica", 8.4, usable):
            pdf.drawString(left, y, line)
            y -= 13
    y -= 8
    for item in data["student_copy"]["questions"]:
        if y < 114:
            raise ValueError("Six questions cannot fit on one A4 page")
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(left, y, str(item["no"]) + ".")
        indent = left+21
        lines = simpleSplit(_pdf_clean(item["task"]), "Helvetica", 10.5, usable-21)
        pdf.setFont("Helvetica", 10.5)
        for line in lines:
            pdf.drawString(indent, y, line)
            y -= 17
        y -= 10
        if item["response_type"] == "checkboxes":
            x=indent+3
            pdf.setFont("Helvetica", 10)
            for opt in item["options"]:
                label = _pdf_clean(opt)
                size = 19 + pdf.stringWidth(label, "Helvetica", 10) + 15
                if x+size > page_w-right:
                    x=indent+3
                    y -= 18
                pdf.setStrokeColor(colors.black)
                pdf.rect(x, y-2, 8.5, 8.5)
                pdf.drawString(x+13, y-1, label)
                x += size
            y -= 32
        else:
            label = _pdf_clean(item.get("response_label", "Jawapan:"))
            pdf.setFont("Helvetica", 10)
            pdf.drawString(indent+2, y, label)
            y -= 16
            for _ in range(item["response_lines"]):
                pdf.setStrokeColor(colors.Color(.45,.45,.45))
                pdf.line(indent+2, y, page_w-right, y)
                y -= 25
            y -= 10
        if y < 85:
            raise ValueError("Worksheet content overflow")
    pdf.setStrokeColor(colors.Color(.65, .68, .67))
    pdf.line(left, 48, page_w-right, 48)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(left, 35, "CONTOH PEMULIHAN DALAMAN - BUKAN UNTUK EDARAN")
    pdf.drawRightString(page_w-right, 35, "1 / 1")
    pdf.showPage()
    pdf.save()


def make_docx(data, target):
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.top_margin, section.bottom_margin = Mm(14), Mm(13)
    section.left_margin, section.right_margin = Mm(16), Mm(16)
    section.header_distance, section.footer_distance = Mm(7), Mm(7)
    norm = doc.styles["Normal"]
    norm.font.name = "Arial"
    norm.font.size = Pt(9)
    norm.paragraph_format.space_after = Pt(2)
    norm.paragraph_format.line_spacing = 1.02
    h=section.header.paragraphs[0]
    h.add_run(TITLE).bold=True
    h.runs[0].font.size=Pt(9)
    t=doc.add_paragraph()
    t.paragraph_format.space_after=Pt(0)
    r=t.add_run(data["student_copy"]["title"].upper())
    r.bold=True
    r.font.size=Pt(16)
    sub=doc.add_paragraph(data["student_copy"]["subtitle"])
    sub.paragraph_format.space_after=Pt(5)
    doc.add_paragraph("NAMA: __________________________  KELAS: __________  TARIKH: __________")
    doc.add_paragraph("BAHAN: " + ", ".join(data["student_copy"]["materials"]))
    doc.add_paragraph("ARAHAN: " + data["student_copy"]["instruction"])
    warn=doc.add_paragraph("INGAT: " + data["student_copy"]["safety"])
    warn.paragraph_format.space_after=Pt(7)
    for item in data["student_copy"]["questions"]:
        para=doc.add_paragraph()
        para.paragraph_format.keep_with_next=True
        para.paragraph_format.space_before=Pt(6)
        para.paragraph_format.space_after=Pt(2)
        num=para.add_run(str(item["no"]) + ". ")
        num.bold=True
        para.add_run(item["task"])
        if item["response_type"] == "checkboxes":
            response=doc.add_paragraph("     " + "      ".join("(  ) "+x for x in item["options"]))
            response.paragraph_format.space_after=Pt(7)
        else:
            doc.add_paragraph("     " + item.get("response_label", "Jawapan:"))
            for _ in range(item["response_lines"]):
                line=doc.add_paragraph("     _________________________________________________________________")
                line.paragraph_format.space_after=Pt(3)
    footer=section.footer.paragraphs[0]
    run=footer.add_run("CONTOH PEMULIHAN DALAMAN - BUKAN UNTUK EDARAN")
    run.font.size=Pt(7.5)
    doc.core_properties.title="CikguLaju - Sains Tahun 1 - Saya Memerhati (staging)"
    doc.core_properties.author="CikguLaju AI"
    doc.save(str(target))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    args=p.parse_args()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    data=source()
    prefix="CIKGULAJU_SAINS_T1_SK1_1_SP1_1_1_CONTOH"
    make_pdf(data,out/(prefix+".pdf"))
    make_docx(data,out/(prefix+".docx"))
    print("Generated two STAGING_ONLY files for human review: "+prefix)


if __name__ == "__main__":
    main()
