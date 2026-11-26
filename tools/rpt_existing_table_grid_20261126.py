"""Polish existing native teaching tables only; preserve all text and multilingual runs."""
from io import BytesIO
import re
from docx import Document
from docx.shared import Twips,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Cell
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH

def normalized(s):return re.sub(r"\s+"," ",s).strip()
def teaching(table):
    h=[normalized(c.text) for c in table.rows[0].cells]
    if len(h)<4:return False
    return (h[0]=="MINGGU / KUMPULAN" and "STANDARD KANDUNGAN & PEMBELAJARAN" in h) or (
        (h[0]=="PdP" or h[0].startswith("PdP ") or h[0]=="Mg.") and
        any(re.search(r"\bSK\b|\bSP\b",v) for v in h))

def apply(table,limit,fill):
    def prop(parent,name,attrs):
        e=parent.find(qn("w:"+name))
        if e is None:e=OxmlElement("w:"+name);parent.append(e)
        for k,v in attrs.items():e.set(qn("w:"+k),str(v))
        return e
    widths=[c.width.twips for c in table.columns]
    assert all(w>0 for w in widths)
    total=min(sum(widths),limit)
    adjusted=[round(w*total/sum(widths)) for w in widths]
    adjusted[-1]+=total-sum(adjusted)
    for c,w in zip(table.columns,adjusted):c.width=Twips(w)
    table.autofit=False;table.alignment=WD_TABLE_ALIGNMENT.CENTER
    pr=table._tbl.tblPr
    prop(pr,"tblW",{"type":"dxa","w":total})
    prop(pr,"tblInd",{"type":"dxa","w":0})
    borders=prop(pr,"tblBorders",{})
    for side in ("top","left","bottom","right","insideH","insideV"):
        prop(borders,side,{"val":"single","sz":4 if side.startswith("inside") else 5,"color":"899A9E"})
    margins=prop(pr,"tblCellMar",{})
    for side,w in (("top",55),("bottom",55),("left",85),("right",85)):
        prop(margins,side,{"type":"dxa","w":w})
    for i,row in enumerate(table.rows):
        offset=0
        prop(row._tr.get_or_add_trPr(),"cantSplit",{"val":"1"})
        for tc in row._tr.tc_lst:
            span=tc.grid_span
            c=_Cell(tc,table);c.width=Twips(sum(adjusted[offset:offset+span]))
            if i==0:
                prop(tc.get_or_add_tcPr(),"shd",{"fill":fill,"val":"clear"})
                c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in c.paragraphs:
                p.paragraph_format.space_before=Pt(0)
                p.paragraph_format.space_after=Pt(1)
                p.paragraph_format.line_spacing=1.03
                if i==0:
                    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    for run in p.runs:run.bold=True
            offset+=span
        assert offset==len(adjusted)
    prop(table.rows[0]._tr.get_or_add_trPr(),"tblHeader",{"val":"1"})

def polish(blob,subject):
    d=Document(BytesIO(blob))
    limit=min(s.page_width.twips-s.left_margin.twips-s.right_margin.twips for s in d.sections)
    colors={"matematik":"D5E5EF","sains":"D5E6DF","alam_dan_manusia":"D5E6DF","bahasa-melayu":"D9E9F3","bahasa_melayu":"D9E9F3","bahasa-cina":"E9E3D5"}
    targets=[i for i,t in enumerate(d.tables) if t.rows and teaching(t)]
    if not targets:raise ValueError("No verified teaching header")
    before=[[[c.text for c in row.cells] for row in t.rows] for t in d.tables]
    non_targets={i:t._tbl.xml for i,t in enumerate(d.tables) if i not in targets}
    for i in targets:apply(d.tables[i],limit,colors.get(subject,"DCECDC"))
    assert all(d.tables[i]._tbl.xml==xml for i,xml in non_targets.items())
    out=BytesIO();d.save(out);data=out.getvalue()
    check=Document(BytesIO(data))
    assert before==[[[c.text for c in row.cells] for row in t.rows] for t in check.tables]
    for i in targets:
        t=check.tables[i];pr=t._tbl.tblPr
        assert pr.find(qn("w:tblW")).get(qn("w:type"))=="dxa"
        assert t.rows[0]._tr.trPr.find(qn("w:tblHeader")) is not None
    return data,targets
