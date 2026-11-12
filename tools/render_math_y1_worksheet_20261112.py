"""Generate a reproducible, pupil-facing Maths Y1 PDF and Word review sample.

STAGING ONLY. Does not add a Web/Telegram route, approve a worksheet, assign a
Lesson/PdP, touch the legacy database, or change RPH credits. The source is a
single hard-coded, internally reviewed candidate; no arbitrary path input.
"""
import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from docx import Document
from docx.shared import Mm, Pt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "supplementary_materials/math/year1/repair_demo_sk1_1_sp1_1_1_20261112.json"
HEADING = "CIKGULAJU AI  |  MATEMATIK TAHUN 1"
FOOTER = "CONTOH PEMULIHAN DALAMAN - BUKAN UNTUK EDARAN"
PREFIX = "CIKGULAJU_MATEMATIK_T1_SK1_1_SP1_1_1_CONTOH"


def source():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    curriculum = data["curriculum"]
    assert data["visibility"] == "STAGING_INTERNAL"
    assert data["approval"] == "NOT_APPROVED_FOR_PRODUCTION"
    assert data["publish"] is False
    assert (curriculum["year"], curriculum["subject"]) == (1, "Matematik")
    assert (curriculum["sk"], curriculum["sp"]) == ("1.1", "1.1.1")
    assert curriculum["lesson_token"] is None
    assert curriculum["textbook_page"] is None
    questions = data["student_copy"]["questions"]
    assert len(questions) == 6
    assert [q["no"] for q in questions] == list(range(1, 7))
    for q in questions:
        assert 1 <= q["group_a"] <= 8 and 1 <= q["group_b"] <= 8
        assert q["shape"] == "bulatan"
        assert q["task"].strip() and len(q["task"]) < 150
        assert isinstance(q["choices"], list) and len(q["choices"]) <= 2
        assert all(isinstance(x, str) and x.strip() for x in q["choices"])
    assert questions[-1]["choices"] == []
    return data


def _pdf_text(value):
    return str(value).translate(str.maketrans({
        "–": "-", "—": "-", "’": "'", "‘": "'", "•": "-",
        "“": '"', "”": '"', "…": "...", "\u00a0": " "
    }))


def make_pdf(data, path):
    page_width, page_height = A4
    pdf = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    pdf.setTitle("CikguLaju Matematik Tahun 1 - Banding Kuantiti - STAGING")
    pdf.setAuthor("CikguLaju AI")
    margin = 43
    right = page_width - margin
    usable = page_width - 2 * margin
    top = page_height - 39

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margin, top, HEADING)
    pdf.setStrokeColor(colors.Color(.65, .67, .69))
    pdf.line(margin, top - 9, right, top - 9)
    pupil = data["student_copy"]
    pdf.setFont("Helvetica-Bold", 17)
    pdf.drawString(margin, top - 37, _pdf_text(pupil["title"]).upper())
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, top - 54, _pdf_text(pupil["subtitle"]))
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(margin, top - 77, "NAMA: __________________________  KELAS: __________  TARIKH: __________")

    y = top - 95
    pdf.setFont("Helvetica", 9)
    for line in simpleSplit("ARAHAN: " + _pdf_text(pupil["instruction"]),
                            "Helvetica", 9, usable):
        pdf.drawString(margin, y, line)
        y -= 13
    y -= 15

    for item in pupil["questions"]:
        if y < 140:
            raise ValueError("Maths worksheet would exceed one A4 page")
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(margin, y, str(item["no"]) + ".")
        pdf.setFont("Helvetica", 10.5)
        lines = simpleSplit(_pdf_text(item["task"]), "Helvetica", 10.5, usable - 23)
        for line in lines:
            pdf.drawString(margin + 22, y, line)
            y -= 15
        y -= 12

        # Filled circles show the quantities without printing an answer.
        for label, qty, x in (
            ("Kumpulan A", item["group_a"], margin + 22),
            ("Kumpulan B", item["group_b"], margin + 265),
        ):
            pdf.setFillColor(colors.black)
            pdf.setFont("Helvetica", 9)
            pdf.drawString(x, y, label)
            cy = y - 19
            for index in range(qty):
                pdf.circle(x + 10 + index * 20, cy, 5.6, stroke=1, fill=1)
            if item["no"] == 6 and label == "Kumpulan B":
                # Empty drawing box is deliberately not a seventh pre-filled dot.
                start = x + 10 + qty * 20
                pdf.rect(start - 7, cy - 9, 24, 19, stroke=1, fill=0)

        y -= 37
        pdf.setFont("Helvetica", 9)
        if item["choices"]:
            x = margin + 22
            for choice in item["choices"]:
                pdf.rect(x, y - 2, 9, 9, stroke=1, fill=0)
                pdf.drawString(x + 14, y - 1, _pdf_text(choice))
                x += 245
        else:
            pdf.drawString(margin + 22, y, "Lukis bulatan dalam kotak kosong kumpulan B.")
        y -= 29
        pdf.setStrokeColor(colors.Color(.87, .87, .87))
        pdf.line(margin + 20, y + 12, right, y + 12)

    if y < 48:
        raise ValueError("Worksheet overlaps the footer")
    pdf.setStrokeColor(colors.Color(.65, .67, .69))
    pdf.line(margin, 49, right, 49)
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 7.5)
    pdf.drawString(margin, 36, FOOTER)
    pdf.drawRightString(right, 36, "1 / 1")
    pdf.showPage()
    pdf.save()


def make_docx(data, path):
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.top_margin, section.bottom_margin = Mm(14), Mm(13)
    section.left_margin, section.right_margin = Mm(16), Mm(16)
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.line_spacing = 1.05

    header = section.header.paragraphs[0]
    r = header.add_run(HEADING)
    r.bold = True
    r.font.size = Pt(9)
    pupil = data["student_copy"]
    title = doc.add_paragraph()
    title.paragraph_format.space_after = Pt(1)
    r = title.add_run(pupil["title"].upper())
    r.bold = True
    r.font.size = Pt(16)
    doc.add_paragraph(pupil["subtitle"])
    doc.add_paragraph("NAMA: __________________________  KELAS: __________  TARIKH: __________")
    doc.add_paragraph("ARAHAN: " + pupil["instruction"])

    for item in pupil["questions"]:
        prompt = doc.add_paragraph()
        prompt.paragraph_format.space_before = Pt(7)
        prompt.paragraph_format.space_after = Pt(4)
        prompt.paragraph_format.keep_with_next = True
        num = prompt.add_run(str(item["no"]) + ". ")
        num.bold = True
        prompt.add_run(item["task"])

        # Explicit quantities, printed as circles, not as numeric clues.
        groups = doc.add_paragraph()
        groups.paragraph_format.space_after = Pt(2)
        for label, qty in (("Kumpulan A", item["group_a"]),
                           ("Kumpulan B", item["group_b"])):
            run = groups.add_run(label + ":  ")
            run.bold = True
            dots = groups.add_run("  ".join("●" for _ in range(qty)))
            dots.font.size = Pt(12)
            if label == "Kumpulan A":
                groups.add_run("       ")
        if item["no"] == 6:
            groups.add_run("    [          ]")

        if item["choices"]:
            answer = doc.add_paragraph("    ".join("(   ) " + x for x in item["choices"]))
        else:
            answer = doc.add_paragraph("Lukis satu bulatan dalam kotak kosong kumpulan B.")
        answer.paragraph_format.space_after = Pt(4)

    footer = section.footer.paragraphs[0]
    run = footer.add_run(FOOTER)
    run.font.size = Pt(7.5)
    doc.core_properties.title = "CikguLaju - Matematik Tahun 1 - Banding Kuantiti - STAGING"
    doc.core_properties.author = "CikguLaju AI"
    doc.save(str(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    folder = Path(args.out)
    folder.mkdir(parents=True, exist_ok=True)
    data = source()
    make_pdf(data, folder / (PREFIX + ".pdf"))
    make_docx(data, folder / (PREFIX + ".docx"))
    print("Generated STAGING-only PDF and Word, pending manual review: " + PREFIX)


if __name__ == "__main__":
    main()
