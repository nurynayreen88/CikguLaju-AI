"""Sejarah-only Word compacting after the existing Telegram-native table renderer.

Uses the same three-table document, preserves all actual words, page size and
metadata, and gives the main activity column more width. Never applied to other
subjects; it does not approve content or alter the source curriculum.
"""
from io import BytesIO
from zipfile import ZipFile

from docx import Document
from docx.shared import Cm, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _xml_text(data):
    """Exact document text nodes, so no words may disappear during compaction."""
    from lxml import etree
    with ZipFile(BytesIO(data)) as archive:
        root=etree.fromstring(archive.read("word/document.xml"))
    return tuple(node.text or "" for node in root.iter(qn("w:t")))


def compact_sejarah_native_word(data):
    if not isinstance(data,bytes) or not data.startswith(b"PK\x03\x04"):
        raise ValueError("Invalid Word document")
    before=_xml_text(data)
    doc=Document(BytesIO(data))
    if len(doc.tables)!=3 or len(doc.tables[1].columns)!=3:
        raise ValueError("Unexpected Telegram RPH table layout")
    for section in doc.sections:
        section.page_width=Cm(21)
        section.page_height=Cm(29.7)
        section.top_margin=Cm(0.48)
        section.bottom_margin=Cm(0.48)
        section.left_margin=Cm(0.70)
        section.right_margin=Cm(0.70)
        section.header_distance=Cm(0.20)
        section.footer_distance=Cm(0.20)
    normal=doc.styles["Normal"]
    normal.font.size=Pt(7.9)
    normal.paragraph_format.space_before=Pt(0)
    normal.paragraph_format.space_after=Pt(0)
    normal.paragraph_format.line_spacing=0.92
    for para in doc.paragraphs:
        para.paragraph_format.space_before=Pt(0)
        para.paragraph_format.space_after=Pt(0)
        para.paragraph_format.line_spacing=0.92
        for run in para.runs:
            run.font.size=Pt(7.9)
    if doc.paragraphs and doc.paragraphs[0].runs:
        doc.paragraphs[0].runs[0].font.size=Pt(10.5)
    for index,table in enumerate(doc.tables):
        table.autofit=False
        widths=(Cm(4.45),Cm(14.75)) if index!=1 else (Cm(2.05),Cm(15.40),Cm(1.75))
        for col,width in zip(table.columns,widths):
            col.width=width
        for cell,width in zip(table.rows[0].cells,widths):
            cell.width=width
        for row in table.rows:
            for cell,width in zip(row.cells,widths):
                cell.width=width
                props=cell._tc.get_or_add_tcPr()
                margin=props.find(qn("w:tcMar"))
                if margin is None:
                    margin=OxmlElement("w:tcMar")
                    props.append(margin)
                for side in ("top","bottom","left","right"):
                    side_node=margin.find(qn("w:"+side))
                    if side_node is None:
                        side_node=OxmlElement("w:"+side)
                        margin.append(side_node)
                    side_node.set(qn("w:w"),"5" if side in ("top","bottom") else "25")
                    side_node.set(qn("w:type"),"dxa")
                for para in cell.paragraphs:
                    para.paragraph_format.space_before=Pt(0)
                    para.paragraph_format.space_after=Pt(0)
                    para.paragraph_format.line_spacing=0.92
                    for run in para.runs:
                        run.font.size=Pt(7.9)
    output=BytesIO()
    doc.save(output)
    done=output.getvalue()
    if _xml_text(done)!=before:
        raise ValueError("Sejarah layout compactor changed document text")
    return done
