"""Write the Year 4 Science DLP classroom RPT from the same lessons used by the RPH."""

import argparse
import json
from itertools import groupby
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from .render_science import LS_CODE, ROOT, SOURCE, load_plans


FLEX_WINDOWS = (
    ("9–13 May", "10–14 May", "Plants and scientific skills",
     "Compare the dated seedling drawings from Lessons 24 and 26. Pupils revise one conclusion using an observation from each setup."),
    ("24–27 Oct", "25–27 Oct", "Select work for follow-up",
     "Review the ten unit slips. Each pupil selects a diagram or investigation to improve and identifies the part that needs clearer evidence."),
    ("31 Oct–4 Nov", "1–5 Nov", "Record a fair comparison",
     "Revisit Lessons 08–10. Pupils repeat a short ramp comparison, keep one condition fixed and annotate the results table."),
    ("7–11 Nov", "8–12 Nov", "Explain a life-science process",
     "Revisit Lessons 11, 19 or 25. Pupils redraw an airway, label animal breathing organs or explain how a leaf makes and stores food."),
    ("14–18 Nov", "15–19 Nov", "Use observations to choose a material",
     "Revisit Review 08 with a different intended use. Pupils support a material choice with two observations and explain why a second material is less suitable."),
    ("21–25 Nov", "22–26 Nov", "Apply learning in a model",
     "Use Lesson 53 or 58. Pupils demonstrate a globe or a model for moving a load and answer a partner’s question with evidence from the model."),
    ("28 Nov–2 Dec", "29 Nov–3 Dec", "Complete pupil records",
     "Compare an early response with the revised work. Record the criterion now demonstrated and one next step for the pupil."),
)


def make_table(doc, widths, headings):
    table = doc.add_table(rows=0, cols=len(widths))
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for column, width in zip(table.columns, widths, strict=True):
        column.width = Mm(width)
    properties = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        line = OxmlElement(f"w:{edge}")
        for name, value in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
            line.set(qn(f"w:{name}"), value)
        borders.append(line)
    properties.append(borders)
    margins = OxmlElement("w:tblCellMar")
    for edge, size in (("top", 65), ("bottom", 65), ("left", 80), ("right", 80)):
        margin = OxmlElement(f"w:{edge}")
        margin.set(qn("w:w"), str(size))
        margin.set(qn("w:type"), "dxa")
        margins.append(margin)
    properties.append(margins)
    header = write_row(table, widths, [(heading,) for heading in headings], header=True)
    header._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    return table


def write_row(table, widths, values, *, header=False):
    row = table.add_row()
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    colour = "275361" if header else ("F0F5F6" if len(table.rows) % 2 else "FFFFFF")
    for cell, width, lines in zip(row.cells, widths, values, strict=True):
        cell.width = Mm(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade = OxmlElement("w:shd")
        shade.set(qn("w:fill"), colour)
        cell._tc.get_or_add_tcPr().append(shade)
        for index, line in enumerate(lines):
            paragraph = cell.add_paragraph() if index else cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.space_before = Pt(2 if index else 0)
            paragraph.paragraph_format.line_spacing = 1.06
            run = paragraph.add_run(line)
            run.font.name = "Calibri"
            run.font.size = Pt(10.5 if header else 10)
            run.bold = header
            run.font.color.rgb = RGBColor.from_string("FFFFFF" if header else "20282B")
    return row


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.page_break_before = True
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(4)
    for r in p.runs:
        r.font.name = "Calibri"
        r.font.color.rgb = RGBColor.from_string("000000")
        r.font.size = Pt(22)
    return p


def introductory_line(doc, value):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(9)
    r = p.add_run(value)
    r.font.name = "Calibri"
    r.font.size = Pt(11)


def standards_for(plan):
    if "review_lss" in plan:
        codes = plan["review_lss"]
        content = sorted({code.rsplit(".", 1)[0] for code in codes})
        return "CS " + ", ".join(content), "LS " + ", ".join(codes)
    return tuple(plan["standards"])


def make_annual_plan(destination):
    plans = load_plans()
    metadata = json.loads(SOURCE.read_text(encoding="utf-8"))
    doc = Document(ROOT / "rpt_2027" / "dlp" / metadata["rpt_file"])
    for item in (doc.paragraphs[-1]._p, doc.tables[-1]._tbl):
        item.getparent().remove(item)
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("Choose the date range"):
            paragraph.runs[0].text = (
                "Choose your group’s dates and enter the actual lesson time in the matching RPH. "
                "Each entry gives the objective and the evidence to collect from each pupil. "
                "Use flexible weeks for school priorities and adapt dates for state and local holidays."
            )
            for run in paragraph.runs[1:]:
                run.text = ""
        elif paragraph.text == "Science Year 4 Textbook (BT074003).":
            paragraph.runs[0].text = "Science Year 4 Textbook (BT074003). References use printed page numbers."
    doc.core_properties.title = "Yearly Teaching Plan 2027 • Science DLP Year 4 SK"
    widths = (33, 48, 31, 67, 70, 22)
    headings = ("Teaching dates", "RPH session", "Standards", "Learning objective",
                "Individual PBD evidence", "Textbook and time")
    for unit, members in groupby(plans, key=lambda p: p["unit"]):
        records = list(members)
        midpoint = (len(records) + 1) // 2
        chunks = [records] if len(records) <= 7 else [records[:midpoint], records[midpoint:]]
        for group_index, chunk in enumerate(chunks):
            heading(doc, unit)
            first, last = chunk[0], chunk[-1]
            unit_number = int(unit.split()[1])
            subtitle = f"{first['label']} to {last['label']}  •  {sum(p['minutes'] for p in chunk)} minutes"
            if len(chunks) > 1:
                subtitle += f"  •  Unit {unit_number}, part {group_index + 1} of {len(chunks)}"
            introductory_line(doc, subtitle)
            table = make_table(doc, widths, headings)
            for p in chunk:
                label = p["label"]
                dates = tuple(s.replace("-", "–") for s in p["rpt_dates"])
                reference = p["references"][0].removeprefix("TB ")
                row = write_row(table, widths, (dates, (label, p["title"]), standards_for(p),
                                (p["objective"],), (p["success_criteria"],),
                                (reference, f"{p['minutes']} min")))
                row.cells[1].paragraphs[0].runs[0].bold = True
    heading(doc, "Flexible teaching weeks")
    introductory_line(doc, "Use these weeks for catch-up, individual assessment or enrichment when the school timetable allows. The 64 hours above cover the 59 lessons and 10 reviews.")
    widths = (37, 37, 65, 132)
    flex = make_table(doc, widths, ("Group A", "Group B", "Focus", "Suggested teaching and evidence"))
    for date_a, date_b, focus, task in FLEX_WINDOWS:
        write_row(flex, widths, ((date_a,), (date_b,), (focus,), (task,)))
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7)
    p.add_run("Calendar note. ").bold = True
    p.add_run("The October window uses days before the Deepavali break. In Sarawak, follow the state school calendar. Check other state and public holidays when assigning a specific day.")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc.save(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    make_annual_plan(parser.parse_args().destination)
