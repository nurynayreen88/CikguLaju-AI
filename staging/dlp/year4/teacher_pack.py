"""Build editable and printable Year 4 Science RPT and RPH books for a school."""

import argparse
from copy import deepcopy
from pathlib import Path
from shutil import copyfile
from subprocess import run
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pypdf import PdfReader, PdfWriter

from .annual_plan import make_annual_plan
from .render_science import export, load_plans


RPT = "RPT_Sains_DLP_Tahun_4_SK_2027"
RPH = "RPH_Sains_DLP_Tahun_4_SK_2027"
PACK = "RPT_dan_RPH_Sains_DLP_Tahun_4_SK_2027"


def lesson_book(plans, singles, destination):
    book = None
    previous_unit = None
    for plan in plans:
        doc = Document(singles / (plan["id"] + ".docx"))
        if plan["unit"] != previous_unit:
            subject = doc.paragraphs[1]
            subject.runs[0].text += "   •   " + plan["unit"]
            outline = OxmlElement("w:outlineLvl")
            outline.set(qn("w:val"), "0")
            subject._p.get_or_add_pPr().append(outline)
        topic = doc.paragraphs[2]
        topic.runs[0].text = plan["label"] + "   " + plan["title"]
        outline = OxmlElement("w:outlineLvl")
        outline.set(qn("w:val"), "1")
        topic._p.get_or_add_pPr().append(outline)
        if book is None:
            book = doc
        else:
            doc.paragraphs[0].paragraph_format.page_break_before = True
            body = book._element.body
            for element in doc._element.body.iterchildren():
                if element.tag != qn("w:sectPr"):
                    body.insert_element_before(deepcopy(element), "w:sectPr")
        previous_unit = plan["unit"]
    book.core_properties.title = "Daily Lesson Plans 2027 • Science DLP Year 4 SK"
    book.core_properties.author = "CikguLaju AI"
    book.save(destination)


def add_bookmarks(plans, source, destination):
    reader = PdfReader(source)
    if len(reader.pages) != len(plans):
        raise ValueError("The Word lesson book must contain exactly one page per RPH.")
    writer = PdfWriter()
    writer.append(reader, import_outline=False)
    previous_unit = None
    for page, plan in enumerate(plans):
        if plan["unit"] != previous_unit:
            parent = writer.add_outline_item(plan["unit"], page)
        writer.add_outline_item(plan["label"] + " · " + plan["title"], page, parent=parent)
        previous_unit = plan["unit"]
    writer.add_metadata({"/Title": "Daily Lesson Plans 2027 • Science DLP Year 4 SK",
                         "/Author": "CikguLaju AI"})
    writer.write(destination)


def build(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    plans = load_plans()
    with TemporaryDirectory(prefix="science_y4_pack_") as folder:
        temp = Path(folder)
        singles = temp / "singles"
        export(plans, singles)
        annual = destination / f"{RPT}.docx"
        combined = destination / f"{RPH}.docx"
        make_annual_plan(annual)
        lesson_book(plans, singles, combined)
        run(["soffice", f"-env:UserInstallation={(temp / 'lo').as_uri()}", "--headless",
             "--convert-to", "pdf", "--outdir", str(temp), str(annual), str(combined)],
            check=True, capture_output=True, timeout=180)
        copyfile(temp / f"{RPT}.pdf", destination / f"{RPT}.pdf")
        add_bookmarks(plans, temp / f"{RPH}.pdf", destination / f"{RPH}.pdf")
        with ZipFile(destination / f"{PACK}.zip", "w", ZIP_DEFLATED) as archive:
            for book in (RPT, RPH):
                for fmt in ("docx", "pdf"):
                    file = destination / f"{book}.{fmt}"
                    archive.write(file, file.name)
            for position, plan in enumerate(plans, start=1):
                _, number, name = plan["unit"].split(" ", 2)
                unit_dir = f"RPH_Ikut_Unit/{int(number):02d}_{name.replace(' ', '_')}"
                for fmt in ("docx", "pdf"):
                    filename = f"{position:02d}_{plan['label'].replace(' ', '_')}.{fmt}"
                    archive.write(singles / (plan["id"] + "." + fmt), f"{unit_dir}/{filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    build(parser.parse_args().destination)
