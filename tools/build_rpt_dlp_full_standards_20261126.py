"""DLP RPT redesign: actual source rows, reviewed CS/LS descriptions, unified cover."""
import argparse,json,re,subprocess,tempfile
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from collections import Counter
import fitz
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from tools.build_rpt_dlp_native_20261126 import PINS,extract,verify_cover,ROOT,SUBJECTS,document_path
from tools.build_kssr_rpt_merged_week_batch_20261126 import mark,norm,text_cell,hyperlink
from web.rpt_native_word_cover import add_word_cover,selected_layout
HEADS=("Week / Date range (A / B)","Lesson / Unit","Content Standard (CS)","Learning Standard (LS)","Learning evidence (PBD)","Book reference / Time")
WIDTHS=(3.45,4.15,4.05,6.1,6.0,3.45)
CODE=re.compile(r"(?<![\d.])\d+\.\d+(?:\.\d+)?(?:\([ivx]+\))?|\([ivx]+\)",re.I)
def descriptions(lines,bank):
    joined=" ".join(lines)
    current=None;parent=None;values={"cs":[],"ls":[]}
    # Match all explicit code and Roman sub-item tokens, in source order.
    token=re.compile(r"\bCS\b|\bLS\b|"+CODE.pattern,re.I)
    cursor=0
    for m in token.finditer(joined):
        gap=joined[cursor:m.start()]
        if gap.strip(" /,;:.-–&()\t\n"):raise ValueError(("unparsed standard field",joined,gap))
        cursor=m.end();item=m.group()
        if item.upper() in ("CS","LS"):
            current=item.lower();parent=None;continue
        if not current:raise ValueError(("code has no CS/LS label",joined,item))
        if item.startswith("("):
            if not parent:raise ValueError(("subitem has no parent",joined,item))
            item=parent+item
        else:parent=item.split("(")[0]
        table=bank[current]
        text=bank.get("parts",{}).get(item) if "(" in item else table.get(item)
        if not text:raise ValueError(("missing reviewed description",current,item,joined))
        values[current].append(item+" "+text)
    if joined[cursor:].strip(" /,;:.-–&()\t\n"):raise ValueError(("unparsed trailing standard field",joined))
    if not all(values.values()):raise ValueError(("missing explicit CS/LS",joined))
    return values["cs"],values["ls"]
def source_cover(subject,year,root):
    # Use the actual common KSSR cover as the template, retaining all logo
    # and teacher/school name geometry. Remove only the subject/year text.
    manifest=json.loads((root/"web_2027_pdfs"/"manifest.json").read_text())["files"]
    template=manifest["bahasa_melayu:2"]
    path=root/"web_2027_pdfs"/template["path"]
    assert sha256(path.read_bytes()).hexdigest()==template["sha256"]
    with fitz.open(path) as orig,fitz.open() as doc:
        doc.insert_pdf(orig,from_page=0,to_page=0)
        page=doc[0]
        spans=[s for b in page.get_text("dict")["blocks"] for line in b.get("lines",[]) for s in line["spans"]]
        candidates=[s for s in spans if "BAHASA MELAYU" in s["text"].upper() and "TAHUN 2" in s["text"].upper()]
        assert len(candidates)==1,[(s["text"],s["bbox"]) for s in spans]
        old=candidates[0];r=fitz.Rect(old["bbox"])
        assert 199<r.y0<r.y1<318
        page.add_redact_annot(r,fill=(1,1,1),cross_out=False)
        page.apply_redactions(images=0,graphics=0,text=0)
        label=f"{SUBJECTS[subject].upper()} (DLP)  |  YEAR {year}"
        # New label uses the same centered band and original font size/ink.
        ink=tuple(((old["color"]>>n)&255)/255 for n in (16,8,0))
        font=fitz.Font("hebo")
        size=old["size"]
        width=font.text_length(label,fontsize=size)
        page.insert_text(((page.rect.width-width)/2,old["origin"][1]),label,fontsize=size,fontname="hebo",color=ink)
        before=orig[0].get_text().replace(old["text"],"").strip().split()
        after=page.get_text().replace(label,"").strip().split()
        assert before==after,(before,after)
        assert not re.search(r"cuti|holiday|break|teaching allocation",page.get_text(),re.I)
        assert "LOGO SEKOLAH" in page.get_text() and "NAMA SEKOLAH" in page.get_text() and "NAMA GURU" in page.get_text()
        return doc.tobytes(garbage=4,deflate=True),page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).tobytes("png")
def append_notes(doc,lines):
    # The previous cover's complete guidance, teaching allocation, holiday
    # dates and source citations are moved, not deleted. Holiday table last.
    assert "Teaching allocation" in lines and "Main school breaks" in lines
    begin=lines.index("Teaching allocation");cut=lines.index("Main school breaks")
    assert begin<cut
    doc.add_page_break()
    doc.add_heading("Teaching information and source references",level=1)
    for line in lines[begin:cut]:
        if line in ("Teaching allocation","Using the schedule"):
            doc.add_heading(line,level=2)
        else:doc.add_paragraph(line)
    end=next(i for i in range(cut+1,len(lines)) if lines[i].startswith("CS ="))
    holidays=lines[cut+1:end]
    assert holidays[:2]==["Group A","Group B"],holidays
    assert len(holidays[2:])%3==0,holidays
    for line in lines[end:]:doc.add_paragraph(line)
    doc.add_heading("Main school breaks",level=2)
    t=doc.add_table(rows=1,cols=3);t.style="Table Grid";t.autofit=False
    for i,v in enumerate(("School break","Group A","Group B")):text_cell(t.rows[0].cells[i],[v],bold=True,shade="E8F0E9")
    for i in range(2,len(holidays),3):
        row=t.add_row()
        for cell,v in zip(row.cells,holidays[i:i+3]):text_cell(cell,[v])
    return lines[begin:cut]+lines[end:]+holidays[2:]
def build_word(subject,year,root=ROOT):
    root=Path(root);key=f"{subject}:{year}"
    path=document_path(subject,year,root=root/"dlp")
    raw=path.read_bytes();assert sha256(raw).hexdigest()==PINS[key]
    lock=json.loads((root/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
    with fitz.open(path) as old:
        verify_cover(old,selected_layout(lock,key,PINS[key]))
        rows=extract(old)
        notes=[line.strip() for line in old[0].get_text().splitlines() if line.strip()]
    bank=json.loads((root/"dlp"/"standard_descriptions"/f"{subject.split('_')[0]}_year{year}.json").read_text())
    cover,png=source_cover(subject,year,root)
    doc=Document();sec=doc.sections[0]
    sec.page_width=Cm(29.7);sec.page_height=Cm(21)
    sec.left_margin=sec.right_margin=Cm(1.2);sec.top_margin=sec.bottom_margin=Cm(1.05)
    sec.header_distance=sec.footer_distance=Cm(.4)
    doc.styles["Normal"].font.name="Arial";doc.styles["Normal"].font.size=Pt(9)
    sec.header.paragraphs[0].text=f"YEARLY TEACHING PLAN 2027 | {SUBJECTS[subject].upper()} (DLP) | YEAR {year}"
    sec.footer.paragraphs[0].text="Group A and Group B | CikguLaju"
    add_word_cover(doc,png)
    t=doc.add_table(rows=1,cols=6);t.style="Table Grid";t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    shade="DCECDC" if subject=="science_dlp" else "D9E9F3"
    for i,(h,w) in enumerate(zip(HEADS,WIDTHS)):
        t.columns[i].width=Cm(w);t.rows[0].cells[i].width=Cm(w)
        text_cell(t.rows[0].cells[i],[h],bold=True,center=True,shade=shade)
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    groups=[];expected=[];failures=[]
    taught_cs=[];taught_ls=[]
    for c,links in rows:
        try:
            if 'Review taught standards' in ' '.join(c[2]) and 'Review' in ' '.join(c[1]):
                assert taught_cs and taught_ls,(key,c[1])
                cs=list(dict.fromkeys(taught_cs));ls=list(dict.fromkeys(taught_ls))
                taught_cs=[];taught_ls=[]
            else:
                cs,ls=descriptions(c[2],bank)
                taught_cs.extend(cs);taught_ls.extend(ls)
        except ValueError as err:failures.append({"lesson":c[1],"field":c[2],"error":str(err)});continue
        row=t.add_row();index=len(t.rows)-1
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for cell,w in zip(row.cells,WIDTHS):cell.width=Cm(w)
        vals=(c[0],c[1],cs,ls,c[3],c[4])
        for cell,lines in zip(row.cells[1:],vals[1:]):text_cell(cell,lines or [""])
        for url in links:hyperlink(row.cells[-1],url)
        expected.append(vals)
        label=tuple(c[0])
        if groups and groups[-1][0]==label:groups[-1]=(label,groups[-1][1],index)
        else:groups.append((label,index,index))
    assert not failures,(key,json.dumps(failures,ensure_ascii=False))
    for label,first,last in groups:
        cell=t.cell(first,0)
        if first<last:cell=cell.merge(t.cell(last,0))
        text_cell(cell,list(label),bold=True,center=True,shade=shade)
    preserved_notes=append_notes(doc,notes)
    stream=BytesIO();doc.save(stream);blob=stream.getvalue()
    check=Document(BytesIO(blob));assert len(check.tables[0].rows)==len(rows)+1
    for i,vals in enumerate(expected,1):
        assert all(norm(cell.text)==norm(" ".join(v)) for cell,v in zip(check.tables[0].rows[i].cells,vals)),(key,i)
    assert all(v[2] and v[3] for v in expected)
    return blob,cover,rows,expected,preserved_notes
def render(subject,year,out):
    blob,cover,rows,expected,notes=build_word(subject,year)
    name=f"RPT_{subject}_Year_{year}_2027"
    word=out/(name+".docx");word.write_bytes(blob)
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",str(folder),str(word.resolve())],check=True,timeout=180)
        target=out/(name+".pdf")
        with fitz.open(folder/(name+".pdf")) as gen,fitz.open(stream=cover,filetype="pdf") as front,fitz.open() as new:
            assert len(gen)>2
            new.insert_pdf(front,from_page=0,to_page=0);new.insert_pdf(gen,from_page=1)
            new.save(target,garbage=4,deflate=True)
        with fitz.open(target) as new:
            assert "Main school breaks" not in new[0].get_text()
            assert "Main school breaks" in new[-1].get_text()
            body="\n".join(p.get_text() for p in list(new)[1:])
            for val in notes:
                assert norm(val) in norm(body),(subject,year,"appendix",val)
            assert re.findall(r"(?m)^Lesson\s+(\d+)\b",body)==[re.search(r"\bLesson\s+(\d+)",' '.join(c[1])).group(1) for c,_ in rows if re.search(r"\bLesson\s+(\d+)",' '.join(c[1]))]
            for v in expected:
                for line in v[2]+v[3]:
                    assert norm(line) in norm(body),(subject,year,line)
            print(json.dumps({"key":f"{subject}:{year}","rows":len(rows),"pages":len(new),"cs_entries":sum(len(v[2]) for v in expected),"ls_entries":sum(len(v[3]) for v in expected),"status":"PRIVATE_LAYOUT_QA_ONLY"}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--subject",choices=SUBJECTS,required=True);p.add_argument("--year",type=int,choices=range(2,7),required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);render(a.subject,a.year,a.out)
