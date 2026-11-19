"""Typography and unfilled boxes for the shared RPH renderers."""

from functools import lru_cache
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

BODY_FONT = "Source Sans 3"
TITLE_FONT = "Source Serif 4 Semibold"
FONT_DIR = Path(__file__).resolve().parents[1] / "fonts" / "rph"
FONT_FILES = (
    (BODY_FONT, "embedRegular", "SourceSans3-Regular.ttf"),
    (BODY_FONT, "embedBold", "SourceSans3-Bold.ttf"),
    (TITLE_FONT, "embedRegular", "SourceSerif4-Semibold.ttf"),
)


@lru_cache(maxsize=1)
def pdf_fonts():
    from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
    from reportlab.pdfbase.ttfonts import TTFont

    regular, bold, title = "SourceSans3-Regular", "SourceSans3-Bold", "SourceSerif4-Semibold"
    for name, (_, _, filename) in zip((regular, bold, title), FONT_FILES, strict=True):
        registerFont(TTFont(name, str(FONT_DIR / filename)))
    registerFontFamily(regular, normal=regular, bold=bold, italic=regular, boldItalic=bold)
    registerFontFamily(bold, normal=bold, bold=bold, italic=bold, boldItalic=bold)
    return regular, bold, title


@lru_cache(maxsize=3)
def _word_font_data(filename):
    key = uuid5(NAMESPACE_URL, "cikgulaju-rph:" + filename)
    data = bytearray((FONT_DIR / filename).read_bytes())
    mask = key.bytes[::-1]
    for offset in range(32):
        data[offset] ^= mask[offset % 16]
    return "{" + str(key).upper() + "}", bytes(data)


def word_typography(doc, body_size, *, embed_fonts=True):
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    from docx.opc.packuri import PackURI
    from docx.opc.part import Part
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor
    from lxml import etree

    normal = doc.styles["Normal"]
    normal.font.size = Pt(body_size)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.05
    title = doc.styles["Title"]
    title.font.size = Pt(20 if embed_fonts else 16)
    title.font.bold = not embed_fonts
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(7)
    title.paragraph_format.line_spacing = 1.0
    properties = title.element.get_or_add_pPr()
    border = properties.find(qn("w:pBdr"))
    if border is not None:
        properties.remove(border)
    if not embed_fonts:
        return

    normal.font.name = BODY_FONT
    title.font.name = TITLE_FONT
    for style in (normal, title):
        fonts = style.element.rPr.rFonts
        for attribute in ("asciiTheme", "hAnsiTheme"):
            fonts.attrib.pop(qn(f"w:{attribute}"), None)
    font_table = doc.part.part_related_by(RT.FONT_TABLE)
    fonts = parse_xml(font_table.blob)
    for family, variant, filename in FONT_FILES:
        font = next((item for item in fonts if item.get(qn("w:name")) == family), None)
        if font is None:
            font = OxmlElement("w:font")
            font.set(qn("w:name"), family)
            fonts.append(font)
        key, data = _word_font_data(filename)
        uri = PackURI("/word/fonts/" + Path(filename).with_suffix(".odttf").name)
        part = Part(uri, "application/vnd.openxmlformats-officedocument.obfuscatedFont", data)
        embedded = OxmlElement(f"w:{variant}")
        embedded.set(qn("r:id"), font_table.relate_to(part, RT.FONT))
        embedded.set(qn("w:fontKey"), key)
        font.append(embedded)
    font_table._blob = etree.tostring(fonts, encoding="utf-8")
    settings = doc.settings.element
    settings.insert_element_before(OxmlElement("w:embedTrueTypeFonts"),
                                   "w:embedSystemFonts", "w:saveSubsetFonts", "w:saveFormsData",
                                   "w:mirrorMargins", "w:proofState", "w:defaultTabStop")


def word_gap(doc, points=6):
    from docx.shared import Pt

    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = Pt(points)
    paragraph.paragraph_format.keep_with_next = True


def style_word_table(table, widths, *, header=False, padding=45):
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm

    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for column, width in zip(table.columns, widths, strict=True):
        column.width = Mm(width)
    for index, row in enumerate(table.rows):
        is_header = header and index == 0
        if is_header:
            row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        for col, (cell, width) in enumerate(zip(row.cells, widths, strict=True)):
            cell.width = Mm(width)
            props = cell._tc.get_or_add_tcPr()
            margins = OxmlElement("w:tcMar")
            borders = OxmlElement("w:tcBorders")
            for edge in ("top", "left", "bottom", "right"):
                line = OxmlElement(f"w:{edge}")
                line.set(qn("w:val"), "single")
                line.set(qn("w:sz"), "4")
                line.set(qn("w:color"), "000000")
                borders.append(line)
                margin = OxmlElement(f"w:{edge}")
                margin.set(qn("w:w"), str(padding if edge in ("top", "bottom") else 115))
                margin.set(qn("w:type"), "dxa")
                margins.append(margin)
            props.append(borders)
            props.append(margins)
            if is_header or col == 0:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True


def pdf_box_style(vertical_padding=3):
    from reportlab.lib.colors import black

    return [
        ("GRID", (0, 0), (-1, -1), 0.5, black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5.75),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5.75),
        ("TOPPADDING", (0, 0), (-1, -1), vertical_padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), vertical_padding),
    ]
