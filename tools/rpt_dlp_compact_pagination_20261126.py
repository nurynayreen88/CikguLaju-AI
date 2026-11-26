"""Compact DLP page packing with measured group heights and repeated native headings."""
from copy import deepcopy
from docx.shared import Pt,Cm
from docx.text.paragraph import Paragraph
from tools.rpt_physical_page_tables import next_page_section
from functools import lru_cache
import fitz,re

def compact_table(doc,t,groups,sizes=None):
    # Preserve the original font sizes, vertical merges and academic text.
    for i,r in enumerate(t.rows):
        same_next=i>0 and i+1<len(t.rows) and r.cells[0].text==t.rows[i+1].cells[0].text
        for el in r._tr.xpath(".//w:p"):
            fmt=Paragraph(el,doc).paragraph_format
            fmt.keep_with_next=same_next;fmt.keep_together=True
            fmt.space_after=Pt(.5);fmt.space_before=Pt(0);fmt.line_spacing=1.0
    for section in doc.sections:section.top_margin=section.bottom_margin=Cm(1.5)
    if sizes is None:
        return [(1,len(t.rows)-1)]
    assert sum(sizes)==len(groups) and all(n>0 for n in sizes)
    anchor=t._tbl;chunks=[];i=0
    for n in sizes:
        a,b=groups[i][1],groups[i+n-1][2]
        if i:next_page_section(doc,anchor)
        clone=deepcopy(anchor)
        for j,tr in enumerate(list(clone.tr_lst)):
            if j!=0 and not a<=j<=b:clone.remove(tr)
        anchor.addprevious(clone);chunks.append((a,b));i+=n
    anchor.getparent().remove(anchor)
    return chunks

def measure_weeks(pdf):
    """Use actual filled date-cell geometry from a native Word rendering."""
    heights=[]
    for p in list(pdf)[1:-1]:
        labels=re.findall(r"(?m)^Week\s+\d{2}\s*$",p.get_text())
        assert labels,(p.number,"no weekly labels")
        fills=[d["rect"] for d in p.get_drawings() if d["type"]=="f" and d["fill"] is not None and d["rect"].height>10]
        left=min(r.x0 for r in fills)
        date_cells=[r for r in fills if abs(r.x0-left)<.4]
        # One shaded date cell per group, plus repeated header. The header
        # can have multiple nested drawings; select unique physical bounds.
        unique=sorted(set((round(r.y0,2),round(r.y1,2)) for r in date_cells))
        assert len(unique)==len(labels)+1,(p.number,len(unique),len(labels))
        heights.extend(b-a for a,b in unique[1:])
    return heights

def choose_sizes(heights,budget=477):
    """Prefer four to five complete weeks; allow fewer for dense standards."""
    n=len(heights)
    @lru_cache(None)
    def best(i):
        if i==n:return (0,())
        options=[]
        for count in range(1,min(5,n-i)+1):
            h=sum(heights[i:i+count])
            if h>budget:break
            tail,sizes=best(i+count)
            # Page count dominates, then balance remaining whitespace.
            penalty=150000+(budget-h)**2+8000*max(0,4-count)**2
            options.append((penalty+tail,(count,*sizes)))
        return min(options,default=(float("inf"),()))
    _,sizes=best(0)
    assert sum(sizes)==n,("weekly group does not fit safely",heights)
    return list(sizes)
