"""Conservative formatting for source-extracted RPT body cells, not academic edits."""
import re
from docx.shared import Pt

BOUNDARY=re.compile(r"^(?:\d+\.\d+(?:\.\d+)*(?:\s|$|\()|(?:SK|SP|CS|LS|PdP|Lesson|Unit|Tema|Tajuk|Topik|MAIN|COMPLEMENTARY|Main Skill|Complementary Skill|Learning Standard|Content Standard|Textbook|Student.?s Book|Workbook|Activity Book|TB|SB|WB|AB|BBM|Bahan|Catatan|Rujukan|EMK|KBAT|PBD|Pentaksiran|Evidens|Nilai)\b)",re.I)
IDENTIFIER=re.compile(r"^(?:\d+\.\d+(?:\.\d+)*(?:\([ivx]+\))?|(?:SK|SP|CS|LS)\s+\d+\.\d+(?:\.\d+)*|(?:PdP|Lesson)\s*[:]?\s*\d+)",re.I)
def norm(v):return re.sub(r"\s+"," ",v).strip()
def reflow(lines):
    out=[]
    for line in lines:
        v=line.strip()
        if not v:continue
        if not out or BOUNDARY.match(v):out.append(v)
        else:out[-1]+=" "+v
    assert norm(" ".join(out))==norm(" ".join(lines))
    return out
def format_source_cell(cell,lines,fill,*,size=8.5,preserve=False):
    fill(cell,lines if preserve else reflow(lines))
    for p in cell.paragraphs:
        p.paragraph_format.keep_together=True
        m=IDENTIFIER.match(p.text)
        if not m:continue
        val=p.text;p.clear()
        for text,bold in ((m.group(),True),(val[m.end():],False)):
            if text:
                run=p.add_run(text);run.bold=bold;run.font.name="Arial";run.font.size=Pt(size)

def fixed_grid(table,header_fill,*,body_size=8.5):
    """Lock total width and every physical cell, including horizontal spans."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.table import _Cell
    from docx.shared import Twips,RGBColor
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    def prop(parent,name,attrs):
        e=parent.find(qn("w:"+name))
        if e is None:
            e=OxmlElement("w:"+name);parent.append(e)
        for k,v in attrs.items():e.set(qn("w:"+k),str(v))
        return e
    widths=[c.width.twips for c in table.columns]
    table.autofit=False
    pr=table._tbl.tblPr
    prop(pr,"tblW",{"type":"dxa","w":sum(widths)})
    prop(pr,"tblInd",{"type":"dxa","w":0})
    borders=prop(pr,"tblBorders",{})
    for side in ("top","left","bottom","right","insideH","insideV"):
        prop(borders,side,{"val":"single","sz":4 if side.startswith("inside") else 5,"color":"899A9E"})
    margins=prop(pr,"tblCellMar",{})
    for side,w in (("top",55),("bottom",55),("left",85),("right",85)):
        prop(margins,side,{"type":"dxa","w":w})
    for i,row in enumerate(table.rows):
        offset=0
        for tc in row._tr.tc_lst:
            span=tc.grid_span
            c=_Cell(tc,table);c.width=Twips(sum(widths[offset:offset+span]))
            centered=i==0 or offset==0
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if centered else WD_CELL_VERTICAL_ALIGNMENT.TOP
            if i==0:prop(tc.get_or_add_tcPr(),"shd",{"fill":header_fill,"val":"clear"})
            for j,p in enumerate(c.paragraphs):
                if centered:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before=Pt(0)
                p.paragraph_format.space_after=Pt(2 if i and j<len(c.paragraphs)-1 else 0)
                p.paragraph_format.line_spacing=1.03
                for run in p.runs:
                    run.font.name="Arial";run.font.size=Pt(9 if i==0 else body_size)
                    if i==0:run.bold=True;run.font.color.rgb=RGBColor.from_string("24373E")
            offset+=span
        assert offset==len(widths)
    prop(table.rows[0]._tr.get_or_add_trPr(),"tblHeader",{"val":"1"})
