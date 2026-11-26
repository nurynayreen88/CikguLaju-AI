"""Private layout QA only. Reformat exact approved DOCX bodies without changing text, cover or script."""
from io import BytesIO
from pathlib import Path
import json,re,subprocess,tempfile
from hashlib import sha256
from docx import Document
from docx.shared import Twips
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
            if not (equal or preserved):blockers.append("PDF cover parity unverified")
            if first_has_teaching:blockers.append("Teaching header on cover")
            if not grid["grid_pages"]:blockers.append("No physical grid detected")
            if grid["missing_header"]:blockers.append("Physical header missing")
            if grid["bottom_overflow"]:blockers.append("Bottom clearance")
            print("GRID_QA",json.dumps({"key":key,"tables_fixed":len(changed),"source_pages":len(old),"render_pages":len(new),"exact_cover_pixel_match":equal,"original_word_cover_match":word_cover_equal,"source_cover_text_match":cover_text_equal,"original_pdf_cover_preserved_candidate":preserved,"geometry":grid,"blockers":blockers,"word_source_sha256":sha256(word).hexdigest(),"pdf_source_sha256":sha256(pdf).hexdigest()}),flush=True)
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
