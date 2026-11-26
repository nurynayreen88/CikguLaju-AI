"""Physical page tables for Latin-script KSSR RPT, retaining the original rows."""
from copy import deepcopy
from io import BytesIO
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm,Pt
from docx.table import _Cell
from docx.text.paragraph import Paragraph
import fitz

def text_lines(text,width,size):
    count=0
    for line in text.split("\n"):
        n=1;used=0
        for word in line.split():
            w=fitz.get_text_length(word,fontname="hebo",fontsize=size)
            gap=size*.35 if used else 0
            if used and used+gap+w>width:n+=1;used=0;gap=0
            if w>width:
                whole=int(w//width);n+=whole;w-=whole*width
            used+=gap+w
        count+=n
    return count

def cell_height(cell):
    width=max(20,cell.width.pt-13)
    return 8+sum(text_lines(p.text,width,9.4)*13.2+3 for p in cell.paragraphs)

def paginate(blob,ranges,*,first_budget=420,budget=455):
    doc=Document(BytesIO(blob));assert len(doc.tables)==1
    t=doc.tables[0];anchor=t._tbl
    header=max(cell_height(c) for c in t.rows[0].cells)
    chunks=[];start=None;end=None;used=header
    def limit():return first_budget if not chunks else budget
    for a,b in ranges:
        heights=[max(cell_height(c) for c in t.rows[i].cells[1:]) for i in range(a,b+1)]
        weekheight=cell_height(t.cell(a,0))
        # Whole weeks when they fit; a long week may span pages with its original
        # date label repeated at the start of each continuation.
        if start is not None and used+max(sum(heights),weekheight)>limit():
            chunks.append((start,end));start=None;used=header
        for i,h in zip(range(a,b+1),heights):
            h=max(h,weekheight) if start is None else h
            if start is not None and used+h>limit():
                chunks.append((start,end));start=None;used=header;h=max(h,weekheight)
            if start is None:start=i
            end=i;used+=h
    if start is not None:chunks.append((start,end))
    assert chunks and chunks[0][0]==1 and chunks[-1][1]==len(t.rows)-1
    rows=list(anchor.tr_lst)
    for n,(a,b) in enumerate(chunks):
        if n:
            el=OxmlElement("w:p");anchor.addprevious(el)
            p=Paragraph(el,doc);f=p.paragraph_format
            f.page_break_before=True;f.space_before=f.space_after=Pt(0);f.line_spacing=Pt(1)
            p.add_run(" ").font.size=Pt(1)
        clone=deepcopy(anchor)
        for j,tr in enumerate(list(clone.tr_lst)):
            if j!=0 and not a<=j<=b:clone.remove(tr)
        group=next((x for x in ranges if x[0]<=a<=x[1]),None)
        if group and group[0]!=a:
            first=clone.tr_lst[1];first.replace(first.tc_lst[0],deepcopy(rows[group[0]].tc_lst[0]))
        anchor.addprevious(clone)
    anchor.getparent().remove(anchor)
    for sec in doc.sections:sec.top_margin=sec.bottom_margin=Cm(1.5)
    # Compare every source cell, including repeated week labels, in logical order.
    source=Document(BytesIO(blob)).tables[0]
    flattened=[r for table in doc.tables for r in table.rows[1:]]
    assert len(flattened)==len(source.rows)-1
    for i,row in enumerate(flattened,1):
        assert [c.text for c in row.cells]==[c.text for c in source.rows[i].cells],i
    out=BytesIO();doc.save(out);return out.getvalue()

def verify_pages(docx_path,pdf_path,headings,normalize):
    d=Document(docx_path)
    with fitz.open(pdf_path) as pdf:
        assert len(pdf)==len(d.tables)+1,("unexpected spill page",len(pdf),len(d.tables))
        for page in list(pdf)[1:]:
            text=normalize(page.get_text()).casefold()
            assert all(normalize(h).casefold() in text for h in headings),(page.number,"missing heading")
            assert all(x["rect"].y1<=page.rect.height-39 for x in page.get_drawings()),(page.number,"bottom margin")
