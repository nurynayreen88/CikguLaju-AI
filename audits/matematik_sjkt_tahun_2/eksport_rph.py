"""Export and verify an individual Matematik SJKT Tahun 2 RPH for review."""

import argparse
from functools import lru_cache
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parent
STEM = "RPH_2027_Matematik_SJKT_Tahun_2"
COUNT = 96
CONTEXT_FIELDS = (("class", "Kelas", 40), ("date", "Tarikh", 10),
                  ("time", "Masa", 13), ("students", "Bilangan murid", 3))


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


def teacher_context(teacher):
    if teacher is None:
        return "", ""

    from web.rph_teacher_reflection import clean_reflection, valid_teacher_fields

    if not valid_teacher_fields(teacher):
        raise ValueError("Butiran guru tidak sah.")
    fields = []
    for key, label, limit in CONTEXT_FIELDS:
        value = teacher[key]
        if not isinstance(value, str) or len(value) > limit or (value and not value.isprintable()):
            raise ValueError("Butiran guru tidak sah.")
        value = value.strip()
        if key == "students" and value and not re.fullmatch(r"[0-9]{1,3}", value):
            raise ValueError("Bilangan murid tidak sah.")
        fields.append((label, value))
    context = "   ·   ".join(f"{label} {value or '________'}" for label, value in fields)
    reflection = clean_reflection(teacher.get("reflection", "")).expandtabs(2)
    return (context if any(value for _, value in fields) else ""), reflection


def render(unit, pdp, extension, teacher=None):
    row = resolve(unit, pdp)
    if row is None:
        raise ValueError("PdP tiada dalam unit yang dipilih.")
    context, reflection = teacher_context(teacher)
    if extension == "docx":
        content = _word(row, context, reflection)
    elif extension == "pdf":
        content = _pdf(row, context, reflection)
    else:
        raise ValueError("Format perlu docx atau pdf.")
    return f"{STEM}_PdP_{pdp:03}.{extension}", content


def _word(row, context, reflection):
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
    if context:
        header, = (p for p in document.paragraphs if p.text.startswith("Kelas ___"))
        header.runs[0].text = context
    if reflection:
        lines = [p for p in document.paragraphs if re.fullmatch(r"_{60,}", p.text)]
        if len(lines) != 4:
            raise ValueError("Ruang refleksi Word tidak sepadan.")
        lines[0].runs[0].text = reflection
        for paragraph in lines[1:]:
            body.remove(paragraph._p)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _pdf(row, context, reflection):
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
        if context or reflection:
            _personalize_pdf(output[0], context, reflection)
        return output.tobytes(garbage=1, deflate=True, use_objstms=1)


def _personalize_pdf(page, context, reflection):
    import pymupdf as fitz

    lines = [
        ("".join(span["text"] for span in line["spans"]), fitz.Rect(line["bbox"]))
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
    ]
    blocks = []
    if context:
        start, = (rect for text, rect in lines if text.strip() == "Kelas")
        right = page.rect.width - start.x0
        erase = fitz.Rect(start.x0 - .2, start.y0 - .3, right, start.y1 + 1.2)
        page.add_redact_annot(erase, fill=False, cross_out=False)
        blocks.append((fitz.Rect(start.x0, start.y0 - 1, right, start.y1 + 9), context))
    if reflection:
        blanks = [rect for text, rect in lines if re.fullmatch(r"_{60,}", text)]
        if len(blanks) != 4:
            raise ValueError("Ruang refleksi PDF tidak sepadan.")
        for rect in blanks:
            page.add_redact_annot(rect, fill=False, cross_out=False)
        start = blanks[0]
        blocks.append((fitz.Rect(start.x0, start.y0 - 1, page.rect.width - start.x0,
                                page.rect.height - 60), _reflection_soft_breaks(reflection)))
    page.apply_redactions(images=0, graphics=0)
    for box, text in blocks:
        html = "<div>" + escape(text).replace("\n", "<br>") + "</div>"
        spare, _ = page.insert_htmlbox(
            box, html, css="div { font-size: 9.5pt; font-family: sans-serif; margin: 0; }",
            scale_low=.8,
        )
        if spare < 0:
            raise ValueError("Butiran guru melebihi ruang yang tersedia dalam PDF.")


def _reflection_soft_breaks(reflection):
    # MuPDF wraps at soft breaks even when a long string has no spaces.
    # Keep Tamil vowel marks and virama joins attached to their letters.
    def break_word(match):
        word = match.group()
        pieces = []
        start = 0
        for i, character in enumerate(word):
            if (i - start >= 40
                    and unicodedata.category(character)[0] != "M"
                    and character not in "\u200c\u200d"
                    and word[i - 1] not in "\u0bcd\u200d"):
                pieces.append(word[start:i])
                start = i
        pieces.append(word[start:])
        return "\u200b".join(pieces)

    return re.sub(r"\S{41,}", break_word, reflection)


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
