"""Private layout QA only. Reformat exact approved DOCX bodies without changing text, cover or script."""
from io import BytesIO
from copy import deepcopy
from math import ceil
from docx.text.paragraph import Paragraph
from pathlib import Path
import json,re,subprocess,tempfile
from hashlib import sha256
from docx import Document
from docx.shared import Twips,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Cell
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
import fitz
from web import kp2027_year1_rpt_combined as kp
from web.rpt_2027_all_http import SCHOOL_RPTS
def prop(parent,name,attrs):
    e=parent.find(qn("w:"+name))
    if e is None:e=OxmlElement("w:"+name);parent.append(e)
    for k,v in attrs.items():e.set(qn("w:"+k),str(v))
    return e
def heading(table):
    vals=[c.text.strip() for c in table.rows[0].cells]
    return len(vals)>=4 and bool(vals[0]) and (vals[0].splitlines()[0] in ("PdP","Mg.","MINGGU / KUMPULAN"))
def signature(doc):
    # Include all paragraphs and all physical cells, not merged aliases.
    return [p.text for p in doc.paragraphs],[[[ _Cell(tc,t).text for tc in row._tr.tc_lst] for row in t.rows] for t in doc.tables]
def fixed(table,available,fill):
    widths=[c.width.twips for c in table.columns]
    assert all(w>0 for w in widths)
    # Normalize to printable width even if original grid exceeds page margin.
    widths=[round(w*available/sum(widths)) for w in widths]
    widths[-1]+=available-sum(widths)
    table.autofit=False;table.alignment=WD_TABLE_ALIGNMENT.CENTER
    for c,w in zip(table.columns,widths):c.width=Twips(w)
    pr=table._tbl.tblPr
    prop(pr,"tblW",{"type":"dxa","w":available})
    prop(pr,"tblInd",{"type":"dxa","w":0})
    b=prop(pr,"tblBorders",{})
    for side in ("top","bottom","left","right","insideH","insideV"):
        prop(b,side,{"val":"single","sz":4 if side.startswith("inside") else 5,"color":"899A9E"})
    m=prop(pr,"tblCellMar",{})
    for side,w in (("top",55),("bottom",55),("left",85),("right",85)):
        prop(m,side,{"type":"dxa","w":w})
    for i,row in enumerate(table.rows):
        trpr=row._tr.get_or_add_trPr()
        prop(trpr,"cantSplit",{"val":"1"})
        if i==0:prop(trpr,"tblHeader",{"val":"1"})
        offset=0
        for tc in row._tr.tc_lst:
            span=tc.grid_span;c=_Cell(tc,table)
            c.width=Twips(sum(widths[offset:offset+span]))
            if i==0:
                prop(tc.get_or_add_tcPr(),"shd",{"val":"clear","fill":fill})
                c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for p in c.paragraphs:
                    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    for run in p.runs:run.bold=True
            offset+=span
        assert offset==len(widths)
def polish(raw,fill):
    d=Document(BytesIO(raw));before=signature(d)
    sec=d.sections[0]
    available=min(s.page_width.twips-s.left_margin.twips-s.right_margin.twips for s in d.sections)
    changed=[]
    for i,t in enumerate(d.tables):
        if heading(t):
            fixed(t,available,fill);changed.append(i)
    assert changed,"No recognized teaching table"
    # Do not touch cover tables, blank change-log template or original text.
    out=BytesIO();d.save(out);result=out.getvalue()
    check=Document(BytesIO(result));assert signature(check)==before
    for i in changed:
        t=check.tables[i];pr=t._tbl.tblPr
        assert pr.find(qn("w:tblW")).get(qn("w:type"))=="dxa"
        assert t.rows[0]._tr.trPr.find(qn("w:tblHeader")) is not None
    return result,changed
def split_native_tables(raw):
    # Keep existing headings, notes, covers, links and source cells.
    # Additional repeated headers are layout-only, not additional lessons.
    d=Document(BytesIO(raw))
    original_paragraphs=[p.text for p in d.paragraphs if p.text]
    def cell_rows(t):
        return [[_Cell(tc,t).text for tc in r._tr.tc_lst] for r in t.rows]
    original=[(heading(t),cell_rows(t)) for t in d.tables]
    expected=[]
    for t in list(d.tables):
        rows=cell_rows(t)
        if not heading(t):
            expected.append(rows);continue
        widths=[c.width.pt for c in t.columns]
        def estimate(i):
            offset=0;heights=[]
            for tc in t.rows[i]._tr.tc_lst:
                w=max(18,sum(widths[offset:offset+tc.grid_span])-12)
                offset+=tc.grid_span
                c=_Cell(tc,t)
                heights.append(8+sum(13*sum(max(1,ceil(sum(10 if ord(ch)>255 else 5 for ch in line)/w)) for line in p.text.splitlines() or [""]) for p in c.paragraphs))
            return max(heights+[20])
        # Never break a vertical merge or detach a full-width week label.
        groups=[];current=[]
        for j in range(1,len(t.rows)):
            cells=t.rows[j]._tr.tc_lst
            continuation=any(tc.tcPr is not None and tc.tcPr.vMerge is not None and tc.tcPr.vMerge.val=="continue" for tc in cells)
            prior_label=bool(current and len(t.rows[current[-1]]._tr.tc_lst)==1)
            if current and not continuation and not prior_label:
                groups.append(current);current=[]
            current.append(j)
        if current:groups.append(current)
        chunks=[];current=[];h=estimate(0)
        budget=min(390,min(sec.page_height.pt-sec.top_margin.pt-sec.bottom_margin.pt for sec in d.sections)*.75)
        for g in groups:
            gh=sum(estimate(j) for j in g)
            if current and (h+gh>budget or len(current)+len(g)>7):
                chunks.append(current);current=[];h=estimate(0)
            current.extend(g);h+=gh
        if current:chunks.append(current)
        assert chunks
        anchor=t._tbl
        # These reviewed sources have a single uniform page setup.
        assert len(d.sections)==1 or all((sec.page_width,sec.page_height,sec.left_margin,sec.right_margin)==(d.sections[0].page_width,d.sections[0].page_height,d.sections[0].left_margin,d.sections[0].right_margin) for sec in d.sections)
        for n,chunk in enumerate(chunks):
            if n:
                el=OxmlElement("w:p");anchor.addprevious(el)
                pf=Paragraph(el,d).paragraph_format
                pf.keep_with_next=False;pf.keep_together=False
                pf.space_before=Pt(0);pf.space_after=Pt(0);pf.line_spacing=Pt(1)
                sec=deepcopy(d.element.body.sectPr)
                for child in list(sec):
                    if child.tag in (qn("w:headerReference"),qn("w:footerReference"),qn("w:pgNumType")):sec.remove(child)
                typ=sec.find(qn("w:type"))
                if typ is None:
                    typ=OxmlElement("w:type");sec.insert_element_before(typ,"w:pgSz","w:pgMar","w:cols","w:docGrid")
                typ.set(qn("w:val"),"nextPage")
                el.get_or_add_pPr().append(sec)
            clone=deepcopy(anchor)
            for j,tr in enumerate(list(clone.tr_lst)):
                if j!=0 and j not in chunk:clone.remove(tr)
            for j,tr in enumerate(clone.tr_lst):
                for el in tr.xpath(".//w:p"):
                    pf=Paragraph(el,d).paragraph_format
                    pf.keep_with_next=j<len(clone.tr_lst)-1
                    pf.keep_together=True;pf.widow_control=False
            anchor.addprevious(clone)
            expected.append([rows[0]]+[rows[j] for j in chunk])
        anchor.getparent().remove(anchor)
    out=BytesIO();d.save(out);blob=out.getvalue()
    check=Document(BytesIO(blob))
    assert [p.text for p in check.paragraphs if p.text]==original_paragraphs
    assert [cell_rows(t) for t in check.tables]==expected
    assert len([r for t in check.tables if heading(t) for r in t.rows[1:]])==sum(len(rows)-1 for is_teaching,rows in original if is_teaching)
    return blob

def render_doc(folder,name,raw):
    p=folder/(name+".docx");p.write_bytes(raw)
    subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"profile").as_uri(),"--headless","--convert-to","pdf","--outdir",str(folder),str(p)],check=True,timeout=240)
    return folder/(name+".pdf")
def normalized(text):
    return re.sub(r"\s+","",text).casefold()
def color_matches(actual,hexcolor):
    if actual is None or len(actual)!=3:return False
    expected=tuple(int(hexcolor[i:i+2],16)/255 for i in (0,2,4))
    return max(abs(a-b) for a,b in zip(actual,expected))<0.035
def geometry_report(doc,fill,minimum_bottom):
    # Inspect the actual colored table grid, not only the DOCX repeat-header flag.
    report={"grid_pages":[],"missing_header":[],"bottom_overflow":[]}
    for page in list(doc)[1:]:
        drawings=page.get_drawings()
        borders=[d["rect"] for d in drawings if color_matches(d.get("color"),"899A9E")]
        headers=[d["rect"] for d in drawings if color_matches(d.get("fill"),fill)]
        if not borders and not headers:continue
        n=page.number+1;report["grid_pages"].append(n)
        all_rects=borders+headers
        top=min(r.y0 for r in all_rects)
        if not headers or min(r.y0 for r in headers)>top+4:
            report["missing_header"].append(n)
        if page.rect.height-max(r.y1 for r in all_rects)<minimum_bottom-2:
            report["bottom_overflow"].append(n)
    return report
def render(key,word,pdf,fill):
    result,changed=polish(word,fill)
    result=split_native_tables(result)
    source_doc=Document(BytesIO(word))
    minimum_bottom=min(s.bottom_margin.pt for s in source_doc.sections)
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td)
        before=render_doc(folder,"original",word)
        after=render_doc(folder,"sample",result)
        with fitz.open(stream=pdf,filetype="pdf") as old,fitz.open(before) as original,fitz.open(after) as new:
            assert len(new)>1 and all(p.get_text().strip() for p in list(new)[1:])
            equal=old[0].rect==new[0].rect and old[0].get_pixmap().samples==new[0].get_pixmap().samples
            word_cover_equal=original[0].rect==new[0].rect and original[0].get_pixmap().samples==new[0].get_pixmap().samples
            cover_text_equal=normalized(old[0].get_text())==normalized(new[0].get_text())
            first_page=normalized(new[0].get_text())
            first_has_teaching=False
            for i in changed:
                cells=source_doc.tables[i].rows[0].cells
                terms=[normalized(c.text) for c in cells if normalized(c.text)]
                if len(terms)>=4 and all(t in first_page for t in terms):
                    first_has_teaching=True
            grid=geometry_report(new,fill,minimum_bottom)
            preserved=False
            # Only replace the PDF cover if both independently rendered Word covers
            # match, cover text agrees with the approved PDF, and there is no teaching
            # table on page one. Keep all body pages; never publish a candidate here.
            if word_cover_equal and cover_text_equal and not first_has_teaching and old[0].rect==new[0].rect:
                with fitz.open() as candidate:
                    candidate.insert_pdf(old,from_page=0,to_page=0)
                    candidate.insert_pdf(new,from_page=1)
                    assert len(candidate)==len(new)
                    assert candidate[0].get_pixmap().samples==old[0].get_pixmap().samples
                    assert all(candidate[i].get_text()==new[i].get_text() for i in range(1,len(new)))
                    preserved=True
            blockers=[]
            if not word_cover_equal:blockers.append("Word cover changed")
            if not (equal or preserved):print("PDF_UNCHANGED",key,"existing PDF remains the download source",flush=True)
            if first_has_teaching:blockers.append("Teaching header on cover")
            if not grid["grid_pages"]:blockers.append("No physical grid detected")
            if grid["missing_header"]:blockers.append("Physical header missing")
            if grid["bottom_overflow"]:blockers.append("Bottom clearance")
            print("GRID_QA",json.dumps({"key":key,"tables_fixed":len(changed),"source_pages":len(old),"render_pages":len(new),"exact_cover_pixel_match":equal,"original_word_cover_match":word_cover_equal,"source_cover_text_match":cover_text_equal,"original_pdf_cover_preserved_candidate":preserved,"geometry":grid,"blockers":blockers,"word_only_candidate":True,"word_source_sha256":sha256(word).hexdigest(),"pdf_source_sha256":sha256(pdf).hexdigest()}),flush=True)
            assert not blockers,(key,blockers)
def main(scope):
    if scope=="kp":
        for subject in kp.SUBJECTS:
            render("KP2027:"+subject,kp.document(subject,"docx")[0],kp.document(subject,"pdf")[0],"DCECDC" if subject=="alam_dan_manusia" else "D9E9F3")
    else:
        school,slug=scope.split(":");m=SCHOOL_RPTS[school][slug]
        for year in m.YEARS:
            w=m.document_path(year,"docx");p=m.document_path(year,"pdf")
            assert w and p,(scope,year)
            render(f"{scope}:{year}",w.read_bytes(),p.read_bytes(),"DCECDC" if slug=="sains" else "D9E9F3")
if __name__=="__main__":
    import sys
    main(sys.argv[1])
