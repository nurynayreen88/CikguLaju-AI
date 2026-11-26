"""Physical native Word page tables; do not rely on repeat-header support."""
from copy import deepcopy
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.shared import Pt,Cm
from docx.text.paragraph import Paragraph
import fitz
def lines(text,width):
    n=1;used=0
    for token in text.split():
        w=fitz.get_text_length(token,fontname="hebo",fontsize=9)
        gap=2.8 if used else 0
        if used and used+gap+w>width:n+=1;used=0;gap=0
        if w>width:
            whole=int(w//width);n+=whole;w-=whole*width
        used+=gap+w
    return n
def height(cell,width):
    return 8+sum(12.3*lines(p.text,width-12)+3 for p in cell.paragraphs)
def split_week_tables(doc,t,groups,*,budget=465,breaks=None):
    widths=[c.width.pt for c in t.columns]
    header=max(height(c,w) for c,w in zip(t.rows[0].cells,widths))
    chunks=[];first=None;last=None;total=header
    for week,(_,a,b) in enumerate(groups,1):
        h=sum(max(height(c,w) for c,w in zip(t.rows[i].cells[1:],widths[1:])) for i in range(a,b+1))
        h=max(h,height(t.cell(a,0),widths[0]))
        if first is not None and ((breaks is not None and week in breaks) or (breaks is None and total+h>budget)):
            chunks.append((first,last));first=None;total=header
        if first is None:first=a
        last=b;total+=h
    if first is not None:chunks.append((first,last))
    assert chunks and chunks[0][0]==1 and chunks[-1][1]==len(t.rows)-1
    anchor=t._tbl
    for i,(a,b) in enumerate(chunks):
        if i:
            el=OxmlElement("w:p");anchor.addprevious(el)
            p=Paragraph(el,doc);f=p.paragraph_format
            f.page_break_before=False;f.keep_with_next=False;f.keep_together=False;f.space_before=Pt(0);f.space_after=Pt(0);f.line_spacing=Pt(1)
            run=p.add_run();run.font.size=Pt(1);run.add_break(WD_BREAK.PAGE)
        clone=deepcopy(anchor)
        for j,tr in enumerate(list(clone.tr_lst)):
            if j!=0 and not a<=j<=b:clone.remove(tr)
        # Keep the complete physical page table together where Word can fit it.
        # Each new table begins after a literal page break, not a blank paragraph flag.
        for idx,tr in enumerate(clone.tr_lst):
            for node in tr.xpath(".//w:p"):
                fmt=Paragraph(node,doc).paragraph_format
                fmt.keep_with_next=idx<len(clone.tr_lst)-1
                fmt.keep_together=True
                fmt.widow_control=False
        anchor.addprevious(clone)
    anchor.getparent().remove(anchor)
    for sec in doc.sections:sec.top_margin=sec.bottom_margin=Cm(1.5)
    return chunks
