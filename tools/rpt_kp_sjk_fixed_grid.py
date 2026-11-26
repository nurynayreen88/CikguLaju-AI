"""Format only verified teaching tables in existing editable KP2027/SJK RPTs."""
from io import BytesIO
import re
from docx import Document
from docx.shared import Twips,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Cell
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH

def prop(parent,name,attrs):
    node=parent.find(qn("w:"+name))
    if node is None:
        node=OxmlElement("w:"+name);parent.append(node)
    for k,v in attrs.items():node.set(qn("w:"+k),str(v))
    return node

def heading(t):
    return " ".join(c.text.replace("\n"," ") for c in t.rows[0].cells)
def teaching(t):
    h=heading(t)
    return len(t.columns)>=4 and bool(re.search(r"\bPdP\b|节次|MINGGU / KUMPULAN",h,re.I)) and bool(re.search(r"\bSK\b|STANDARD KANDUNGAN|内容与学习标准",h,re.I))
def fix(raw,subject):
    doc=Document(BytesIO(raw))
    width=min(s.page_width.twips-s.left_margin.twips-s.right_margin.twips for s in doc.sections)
    count=0
    palette={"matematik":"D9E9F3","sains":"DCECDC","alam_dan_manusia":"E2EAD9","bahasa_melayu":"F1E7DA","bahasa-melayu":"F1E7DA","bahasa-cina":"F2E4E6"}
    fill=palette.get(subject,"DCE8EC")
    for t in doc.tables:
        if not t.rows or not teaching(t):continue
        before=[[c.text for c in row.cells] for row in t.rows]
        raw_width=[c.width.twips for c in t.columns]
        assert all(w>0 for w in raw_width)
        widths=[round(w*width/sum(raw_width)) for w in raw_width]
        widths[-1]+=width-sum(widths)
        for c,w in zip(t.columns,widths):c.width=Twips(w)
        t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
        pr=t._tbl.tblPr
        prop(pr,"tblW",{"type":"dxa","w":width})
        prop(pr,"tblInd",{"type":"dxa","w":0})
        b=prop(pr,"tblBorders",{})
        for side in ("top","left","bottom","right","insideH","insideV"):
            prop(b,side,{"val":"single","sz":4 if side.startswith("inside") else 5,"color":"899A9E"})
        margins=prop(pr,"tblCellMar",{})
        for side,w in (("top",55),("bottom",55),("left",85),("right",85)):
            prop(margins,side,{"type":"dxa","w":w})
        prop(t.rows[0]._tr.get_or_add_trPr(),"tblHeader",{"val":"1"})
        for i,row in enumerate(t.rows):
            prop(row._tr.get_or_add_trPr(),"cantSplit",{"val":"1"})
            offset=0
            for tc in row._tr.tc_lst:
                span=tc.grid_span;c=_Cell(tc,t)
                c.width=Twips(sum(widths[offset:offset+span]))
                centered=i==0 or offset==0
                c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if centered else WD_CELL_VERTICAL_ALIGNMENT.TOP
                if i==0:prop(tc.get_or_add_tcPr(),"shd",{"fill":fill,"val":"clear"})
                for p in c.paragraphs:
                    if centered:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_before=Pt(0)
                    p.paragraph_format.space_after=Pt(1)
                    p.paragraph_format.line_spacing=1.03
                    # Keep original East Asian/Tamil font families and text direction.
                    if i==0:
                        for run in p.runs:run.bold=True
                offset+=span
            assert offset==len(widths)
        assert before==[[c.text for c in row.cells] for row in t.rows]
        count+=1
    assert count,"No confirmed teaching table"
    out=BytesIO();doc.save(out)
    return out.getvalue(),count
