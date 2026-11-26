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
    return len(vals)>=4 and (vals[0].splitlines()[0] in ("PdP","Mg.","MINGGU / KUMPULAN"))
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
def render(key,word,pdf,fill):
    result,changed=polish(word,fill)
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td);p=folder/"sample.docx";p.write_bytes(result)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"profile").as_uri(),"--headless","--convert-to","pdf","--outdir",td,str(p)],check=True,timeout=240)
        with fitz.open(stream=pdf,filetype="pdf") as old,fitz.open(folder/"sample.pdf") as new:
            assert len(new)>1 and all(p.get_text().strip() for p in list(new)[1:])
            # Report cover parity; a mismatch is a release blocker, not silently replaced.
            equal=old[0].rect==new[0].rect and old[0].get_pixmap().samples==new[0].get_pixmap().samples
            print("GRID_QA",json.dumps({"key":key,"tables_fixed":len(changed),"source_pages":len(old),"render_pages":len(new),"exact_cover_pixel_match":equal,"word_source_sha256":sha256(word).hexdigest(),"pdf_source_sha256":sha256(pdf).hexdigest()}),flush=True)
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
