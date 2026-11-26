"""Physical page tables with repeated headings and explicit safe page breaks."""
from copy import deepcopy
from io import BytesIO
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm,Pt
from docx.table import _Cell
from docx.text.paragraph import Paragraph
import fitz,re

def height(c,width):
    width=max(20,width-13)
    total=8
    for p in c.paragraphs:
        count=1;used=0
        for token in p.text.split():
            size=fitz.get_text_length(token,fontname="hebo",fontsize=9.2)
            gap=3 if used else 0
            if used and used+gap+size>width:count+=1;used=0;gap=0
            if size>width:
                count+=int(size//width);size%=width
            used+=gap+size
        total+=13*count+3
    return total
def physical_height(t,row,widths):
    vals=[];offset=0
    for tc in row._tr.tc_lst:
        span=tc.grid_span
        if offset:
            vals.append(height(_Cell(tc,t),sum(widths[offset:offset+span])))
        offset+=span
    return max(vals+[20])
def snapshot(t):
    return [tuple(c.text for c in row.cells) for row in t.rows[1:]]
def paginate(blob,*,budget=440,first_budget=None):
    doc=Document(BytesIO(blob))
    t=doc.tables[0];before=snapshot(t)
    widths=[c.width.pt for c in t.columns]
    header=max(height(c,w) for c,w in zip(t.rows[0].cells,widths))
    groups=[]
    for i in range(1,len(t.rows)):
        if groups and t.cell(i,0)._tc is t.cell(groups[-1][0],0)._tc:groups[-1].append(i)
        else:groups.append([i])
    # Oversize weeks can span two pages with the identical week label.
    blocks=[]
    for g in groups:
        start=g[0];current=[];total=0
        for i in g:
            h=physical_height(t,t.rows[i],widths)
            assert header+h<budget,("row too tall",i,h)
            if current and header+max(total+h,height(t.cell(start,0),widths[0]))>budget:
                blocks.append((start,current,max(total,height(t.cell(start,0),widths[0]))))
                current=[];total=0
            current.append(i);total+=h
        if current:blocks.append((start,current,max(total,height(t.cell(start,0),widths[0]))))
    pages=[];current=[];total=header
    for start,rows,h in blocks:
        limit=first_budget if not pages and first_budget else budget
        if current and total+h>limit:pages.append(current);current=[];total=header
        current.append((start,rows));total+=h
    if current:pages.append(current)
    anchor=t._tbl
    for n,blocks in enumerate(pages):
        if n:
            el=OxmlElement("w:p");anchor.addprevious(el)
            p=Paragraph(el,doc);pf=p.paragraph_format
            pf.page_break_before=True;pf.space_before=Pt(0);pf.space_after=Pt(0);pf.line_spacing=Pt(1)
            p.add_run(" ").font.size=Pt(1)
        clone=deepcopy(anchor)
        for tr in list(clone.tr_lst)[1:]:clone.remove(tr)
        for start,rows in blocks:
            for k,i in enumerate(rows):
                row=deepcopy(t.rows[i]._tr)
                if k==0 and i!=start:
                    new=deepcopy(t.rows[start]._tr.tc_lst[0])
                    row.replace(row.tc_lst[0],new)
                # Avoid inheriting keep-next across the new physical page boundary.
                for e in row.xpath(".//w:keepNext"):e.getparent().remove(e)
                clone.append(row)
        anchor.addprevious(clone)
    anchor.getparent().remove(anchor)
    for sec in doc.sections:sec.top_margin=sec.bottom_margin=Cm(1.5)
    out=BytesIO();doc.save(out);result=out.getvalue()
    check=Document(BytesIO(result))
    assert [v for table in check.tables for v in snapshot(table)]==before,"source rows changed"
    assert len(check.tables)==len(pages)
    return result

def verify_pages(blob,pdf):
    doc=Document(BytesIO(blob))
    def norm(s):return re.sub(r"\s+"," ",s).strip().casefold()
    assert len(pdf)==len(doc.tables)+1,("unexpected spill pages",len(pdf),len(doc.tables))
    for page,t in zip(list(pdf)[1:],doc.tables):
        txt=norm(page.get_text())
        assert all(norm(c.text) in txt for c in t.rows[0].cells),("missing heading",page.number+1)
        assert all(d["rect"].y1<=page.rect.height-39 for d in page.get_drawings()),("bottom margin",page.number+1)
