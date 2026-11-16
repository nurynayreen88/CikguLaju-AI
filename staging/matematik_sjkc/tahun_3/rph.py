"""Resolve and export an individual Matematik SJKC Tahun 3 PdP from the reviewed set."""

from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
STEM = "RPH_2027_Matematik_SJKC_Tahun_3"
PDP_COUNT = 96


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


def render(lesson, fmt):
    pdp = lesson["pdp"]
    output = BytesIO()
    if fmt == "word":
        _word(lesson, output)
    elif fmt == "pdf":
        _pdf(lesson, output)
    else:
        raise ValueError("Unsupported RPH format")
    ext = "docx" if fmt == "word" else "pdf"
    return f"{STEM}_PdP_{pdp:03}.{ext}", output.getvalue()


def _word(lesson, output):
    from docx import Document
    from docx.oxml.ns import qn

    doc = Document(ROOT / f"{STEM}.docx")
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
    doc.save(output)


def _pdf(lesson, output):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(ROOT / f"{STEM}.pdf")
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
