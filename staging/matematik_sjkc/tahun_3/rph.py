"""Resolve and export an individual Matematik SJKC Tahun 3 PdP from the reviewed set."""

from functools import lru_cache
from io import BytesIO
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
STEM = "RPH_2027_Matematik_SJKC_Tahun_3"
PDP_COUNT = 96
YEAR = 3
SUBJECT = "Matematik SJKC"
RELEASE_FLAG = "CIKGULAJU_MATEMATIK_SJKC_T3_RPH_ENABLED"
_PHASE_DURATION = re.compile(r"[0-9]{1,2} 分钟")


def enabled():
    return os.environ.get(RELEASE_FLAG) == "1"


@lru_cache(maxsize=1)
def lessons():
    source = json.loads((ROOT / "year_3_2027.json").read_text(encoding="utf-8"))
    records = source["lessons"]
    if (source["year"], source["school_type"], source["subject"]) != (3, "SJKC", "Matematik"):
        raise ValueError("Unexpected Matematik SJKC source")
    if [record["pdp"] for record in records] != list(range(1, PDP_COUNT + 1)):
        raise ValueError("Invalid Matematik SJKC PdP sequence")
    return tuple(records)


def resolve(unit, pdp):
    if type(unit) is not int or type(pdp) is not int or not 1 <= pdp <= PDP_COUNT:
        return None
    lesson = lessons()[pdp - 1]
    return lesson if lesson["unit_number"] == unit else None


def units():
    return tuple(dict.fromkeys((lesson["unit_number"], lesson["unit"]) for lesson in lessons()))


def teacher_lines(teacher):
    teacher = teacher or {}
    date = teacher.get("date") or ""
    time = teacher.get("time") or ""
    name = teacher.get("class") or ""
    pupils = teacher.get("students") or ""
    return (
        f"日期 Tarikh {date}   |   时间 Masa {time}",
        f"班级 Kelas {name}   |   学生人数 Bilangan murid {pupils}",
    )


def render(lesson, fmt, teacher=None):
    pdp = lesson["pdp"]
    output = BytesIO()
    lines = teacher_lines(teacher)
    reflection = (teacher or {}).get("reflection", "")
    if fmt == "word":
        _word(lesson, output, lines, reflection)
    elif fmt == "pdf":
        _pdf(lesson, output, lines, reflection)
    else:
        raise ValueError("Unsupported RPH format")
    ext = "docx" if fmt == "word" else "pdf"
    return f"{STEM}_PdP_{pdp:03}.{ext}", output.getvalue()


def _word(lesson, output, lines, reflection, *, path=None):
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    doc = Document(path if path is not None else ROOT / f"{STEM}.docx")
    body = doc.element.body
    groups = [[]]
    section = body.sectPr
    for element in body:
        if element is section:
            continue
        if (element.tag == qn("w:p") and
                any(br.get(qn("w:type")) == "page" for br in element.iter(qn("w:br")))):
            groups.append([])
        else:
            groups[-1].append(element)

    def paragraph_text(element):
        return "".join(part.text or "" for part in element.iter(qn("w:t")))

    marker = f"PdP {lesson['pdp']:03}"
    if len(groups) != PDP_COUNT:
        raise ValueError("Word sequence count does not match the data")
    selected = groups[lesson["pdp"] - 1]
    if (not any(re.match(rf"^{marker}\b", paragraph_text(element)) for element in selected)
            or not any(paragraph_text(element) == lesson["topic"] for element in selected)):
        raise ValueError("Word page does not match requested PdP")
    selected = set(selected)
    for element in list(body):
        if element is not section and element not in selected:
            body.remove(element)
    context, = [p for p in doc.paragraphs if p.text.startswith("日期 Tarikh ")]
    context.runs[0].text = "\n".join(lines)
    for table in doc.tables:
        if table.cell(0, 1).text == "分钟":
            for row in table.rows:
                row.cells[1].paragraphs[0].runs[0].text = ""
        else:
            for row in table.rows:
                phase = row.cells[0].paragraphs[0]
                for run in phase.runs:
                    title, sep, planned_time = run.text.rpartition("\n")
                    if sep and _PHASE_DURATION.fullmatch(planned_time):
                        run.text = title
    if reflection:
        notes, = [p for p in doc.paragraphs if p.text.startswith("教学反思")]
        paragraph = doc.add_paragraph()
        notes._p.addnext(paragraph._p)
        paragraph.paragraph_format.space_before = Pt(2)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = Pt(11)
        run = paragraph.add_run(reflection.expandtabs(2))
        run.font.size = Pt(9)
        # On CJK runs Word uses szCs independently of the Latin font size.
        size = OxmlElement("w:szCs")
        size.set(qn("w:val"), "18")
        run._r.get_or_add_rPr().append(size)
    doc.save(output)


def _pdf(lesson, output, lines, reflection, *, path=None):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(path if path is not None else ROOT / f"{STEM}.pdf")
    if len(reader.pages) != PDP_COUNT:
        raise ValueError("PDF sequence count does not match the data")
    page = reader.pages[lesson["pdp"] - 1]
    source_text = page.extract_text()
    marker = f"PdP {lesson['pdp']:03}"
    if (not re.search(rf"\b{marker}\b", source_text)
            or "".join(lesson["topic"].split()) not in "".join(source_text.split())):
        raise ValueError("PDF page does not match requested PdP")
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(output)
    personalized = _personalize_pdf(output.getvalue(), lines, reflection)
    output.seek(0)
    output.truncate()
    output.write(personalized)


def _personalize_pdf(source, lines, reflection):
    import pymupdf as fitz

    with fitz.open(stream=source, filetype="pdf") as document:
        page = document[0]
        text_lines = [
            ("".join(span["text"] for span in line["spans"]), fitz.Rect(line["bbox"]))
            for block in page.get_text("dict")["blocks"] if "lines" in block
            for line in block["lines"]
        ]
        (_, context), = [(text, rect) for text, rect in text_lines
                                    if text.startswith("日期 Tarikh ")]
        notes, = [rect for text, rect in text_lines if text.startswith("教学反思")]
        minute_headers = [rect for text, rect in text_lines if text == "分钟"]
        if minute_headers:
            # SJKC Year 3 has a standalone, aligned column for phase minutes.
            header, = minute_headers
            durations = [rect for text, rect in text_lines
                         if re.fullmatch(r"[0-9]{1,2}", text)
                         and abs(rect.x0 - header.x0) < 1 and header.y1 < rect.y0 < notes.y0]
            duration_cells = [header, *durations]
        else:
            # SJKC Year 2 puts durations on separate lines in the phase cells.
            duration_cells = [rect for text, rect in text_lines
                              if _PHASE_DURATION.fullmatch(text)
                              and context.x0 <= rect.x0 < context.x0 + 15]
        for rect in [context, *duration_cells]:
            page.add_redact_annot(rect, fill=False)
        page.apply_redactions(images=0, graphics=0)
        font = fitz.Font("china-s")
        right = page.rect.width - context.x0
        writer = fitz.TextWriter(page.rect)
        box = fitz.Rect(context.x0, context.y0 - 4, right, context.y1 + 13)
        widest = max(font.text_length(line, fontsize=9) for line in lines)
        size = min(9, 9 * (box.width - 2) / widest)
        for index, line in enumerate(lines):
            writer.append((box.x0, context.y0 + 4 + 10 * index), line, font=font, fontsize=size)
        if reflection:
            box = fitz.Rect(notes.x0, notes.y1 + 8, right, page.rect.height - 70)
            if writer.fill_textbox(box, reflection.expandtabs(2), font=font, fontsize=9, lineheight=1.15):
                raise ValueError("Teacher reflection exceeds available PDF space")
        writer.write_text(page)
        document.subset_fonts()
        return document.tobytes(garbage=4, deflate=True)
