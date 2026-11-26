"""Physical per-page RPT tables; preserve merged weeks and all source cells."""
from copy import deepcopy
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

def paginate(doc,table,max_rows=10,budget=580):
    rows=table.rows
    groups=[]
    for row in rows[1:]:
        if row._tr.tc_lst[0].vMerge!='continue':groups.append([])
        groups[-1].append(row)
    widths=[c.width.pt for c in table.columns]
    def height(row):
        values=[]
        for j,c in enumerate(row.cells):
            if j==0:continue
            usable=widths[j]-13
            h=8
            for p in c.paragraphs:
                count=1;used=0
                for word in p.text.split():
                    w=len(word)*4.7+3
                    if used and used+w>usable:count+=1;used=0
                    used+=w
                h+=count*12+2
            values.append(h)
        return max(values+[38])
    pages=[];current=[];used=0
    for group in groups:
        gh=sum(height(row) for row in group)
        if current and (len(current)+len(group)>max_rows or used+gh>budget):
            pages.append(current);current=[];used=0
        current.extend(group);used+=gh
    if current:pages.append(current)
    old=table._tbl;parent=old.getparent();idx=parent.index(old)
    header=deepcopy(rows[0]._tr)
    original=[[c.text for c in row.cells] for row in rows[1:]]
    for i,page in enumerate(pages):
        if i:
            p=OxmlElement("w:p");pp=Paragraph(p,doc._body)
            pp.paragraph_format.space_before=Pt(0)
            pp.paragraph_format.space_after=Pt(0)
            pp.paragraph_format.line_spacing=Pt(1)
            pp.paragraph_format.page_break_before=True
            pp.add_run(" ").font.size=Pt(1)
            parent.insert(idx,p);idx+=1
        t=deepcopy(old)
        for tr in t.tr_lst:t.remove(tr)
        t.append(deepcopy(header))
        for row in page:t.append(deepcopy(row._tr))
        parent.insert(idx,t);idx+=1
    parent.remove(old)
    check=[row for t in doc.tables[:len(pages)] for row in t.rows[1:]]
    assert [[c.text for c in row.cells] for row in check]==original
    return len(pages)
