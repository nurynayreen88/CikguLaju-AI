"""Export and verify an individual Matematik SJKT Tahun 2 RPH for review."""

import argparse
from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
STEM = "RPH_2027_Matematik_SJKT_Tahun_2"
COUNT = 96


@lru_cache(maxsize=1)
def lessons():
    source = json.loads((ROOT / "rpt_2027.json").read_text(encoding="utf-8"))
    if (source["sekolah"], source["subjek"], source["tahun"], source["tahun_ajaran"]) != (
        "SJKT", "Matematik", 2, 2027
    ):
        raise ValueError("Sumber Matematik SJKT Tahun 2 tidak sepadan.")
    rows = source["pdp"]
    if [row["pdp"] for row in rows] != list(range(1, COUNT + 1)):
        raise ValueError("Urutan PdP tidak sepadan.")
    return tuple(rows)


def resolve(unit, pdp):
    if type(unit) is not int or type(pdp) is not int or not 1 <= pdp <= COUNT:
        return None
    row = lessons()[pdp - 1]
    return row if row["unit"] == unit else None


def render(unit, pdp, extension):
    row = resolve(unit, pdp)
    if row is None:
        raise ValueError("PdP tiada dalam unit yang dipilih.")
    if extension == "docx":
        content = _word(row)
    elif extension == "pdf":
        content = _pdf(row)
    else:
        raise ValueError("Format perlu docx atau pdf.")
    return f"{STEM}_PdP_{pdp:03}.{extension}", content


def _word(row):
    from docx import Document
    from docx.oxml.ns import qn

    document = Document(ROOT / (STEM + ".docx"))
    body = document.element.body
    section = body.sectPr
    groups = [[]]
    for element in body:
        if element is section:
            continue
        if any(item.get(qn("w:type")) == "page" for item in element.iter(qn("w:br"))):
            groups.append([])
        else:
            groups[-1].append(element)
    if len(groups) != COUNT:
        raise ValueError("Jumlah halaman Word tidak sepadan.")
    selected = groups[row["pdp"] - 1]
    paragraphs = ["".join(e.text or "" for e in item.iter(qn("w:t"))) for item in selected]
    marker = f"PdP {row['pdp']:03}  |  Unit {row['unit']}  |"
    if not any(p.startswith(marker) for p in paragraphs) or row["tajuk_tamil"] not in paragraphs:
        raise ValueError("Halaman Word tidak sepadan dengan PdP.")
    for element in list(body):
        if element is not section and element not in selected:
            body.remove(element)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _pdf(row):
    import pymupdf as fitz

    with fitz.open(ROOT / (STEM + ".pdf")) as document, fitz.open() as output:
        if len(document) != COUNT:
            raise ValueError("Jumlah halaman PDF tidak sepadan.")
        index = row["pdp"] - 1
        text = document[index].get_text(sort=True)
        marker = re.compile(rf"\bPdP\s+{row['pdp']:03}\b")
        if not marker.search(text) or row["sp"] not in text:
            raise ValueError("Halaman PDF tidak sepadan dengan PdP.")
        output.insert_pdf(document, from_page=index, to_page=index)
        return output.tobytes(garbage=1, deflate=True, use_objstms=1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("unit", type=int)
    parser.add_argument("pdp", type=int)
    parser.add_argument("format", choices=("docx", "pdf"))
    parser.add_argument("direktori", type=Path)
    args = parser.parse_args()
    filename, content = render(args.unit, args.pdp, args.format)
    args.direktori.mkdir(parents=True, exist_ok=True)
    target = args.direktori / filename
    # The review exporter never replaces a previously downloaded file.
    with target.open("xb") as f:
        f.write(content)
    print(target)
