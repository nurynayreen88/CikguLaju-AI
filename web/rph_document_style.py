"""Colours and Word formatting for the shared CikguLaju RPH layout."""

INK = "172C3A"
NAVY = "163449"
TEAL = "14665E"
MIST = "E8F1F3"
STRIPE = "F5F8F9"
GRID = "D9DFE5"
WHITE = "FFFFFF"


def style_word_table(table, widths, *, header=False):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, RGBColor

    table.autofit = False
    for column, width in zip(table.columns, widths, strict=True):
        column.width = Mm(width)
    for index, row in enumerate(table.rows):
        is_header = header and index == 0
        if is_header:
            row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        for col, (cell, width) in enumerate(zip(row.cells, widths, strict=True)):
            cell.width = Mm(width)
            props = cell._tc.get_or_add_tcPr()
            shade = props.find(qn("w:shd"))
            if shade is None:
                shade = OxmlElement("w:shd")
                props.append(shade)
            shade.set(qn("w:fill"), NAVY if is_header else MIST if col == 0 else STRIPE if index % 2 else WHITE)
            borders = props.find(qn("w:tcBorders"))
            if borders is None:
                borders = OxmlElement("w:tcBorders")
                props.append(borders)
            for edge in ("top", "left", "bottom", "right"):
                line = borders.find(qn(f"w:{edge}"))
                if line is None:
                    line = OxmlElement(f"w:{edge}")
                    borders.append(line)
                accent = index == 0 and edge == "top" and not header
                line.set(qn("w:val"), "single")
                line.set(qn("w:sz"), "10" if accent else "4")
                line.set(qn("w:color"), TEAL if accent else GRID)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    if is_header or col == 0:
                        run.bold = True
                        run.font.color.rgb = RGBColor.from_string(WHITE if is_header else INK)
