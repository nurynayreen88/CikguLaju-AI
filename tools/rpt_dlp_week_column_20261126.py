"""Avoid cross-renderer vertical-merge overhang in the Week/Date column.
Keep every real lesson row, weekly shading and external borders. Suppress
only the internal horizontal edges of each week; use real independent cells.
"""
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

def fix_week_column(table):
    rows=list(table._tbl.tr_lst)
    assert all(len(r.tc_lst)==6 for r in rows)
    cells=[r.tc_lst[0] for r in rows]
    types=[tc.vMerge for tc in cells]
    assert types[0] is None and types[1]!="continue"
    before=[tuple("".join(tc.xpath(".//w:t/text()")) for tc in r.tc_lst) for r in rows]
    for i,tc in enumerate(cells):
        if i==0:continue
        pr=tc.get_or_add_tcPr()
        vm=pr.find(qn("w:vMerge"))
        if vm is not None:pr.remove(vm)
        border=pr.find(qn("w:tcBorders"))
        if border is None:
            border=OxmlElement("w:tcBorders")
            pr.insert_element_before(border,"w:shd","w:noWrap","w:tcMar","w:textDirection","w:tcFitText","w:vAlign")
        for edge,hidden in (("top",types[i]=="continue"),("bottom",i+1<len(cells) and types[i+1]=="continue")):
            el=border.find(qn("w:"+edge))
            if el is not None:border.remove(el)
            el=OxmlElement("w:"+edge)
            el.set(qn("w:val"),"nil" if hidden else "single")
            if not hidden:
                el.set(qn("w:sz"),"5" if i==len(cells)-1 and edge=="bottom" else "4")
                el.set(qn("w:color"),"849991")
            border.append(el)
        if types[i]=="continue":
            assert not "".join(tc.xpath(".//w:t/text()")).strip()
            p=tc.xpath("./w:p")[0]
            spacing=p.get_or_add_pPr().get_or_add_spacing()
            spacing.line=Pt(1);spacing.set(qn("w:lineRule"),"exact");spacing.after=Pt(0)
    assert all(tc.vMerge is None for tc in cells)
    assert before==[tuple("".join(tc.xpath(".//w:t/text()")) for tc in r.tc_lst) for r in rows]
