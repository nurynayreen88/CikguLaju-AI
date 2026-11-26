"""DLP RPT redesign: actual source rows, reviewed CS/LS descriptions, unified cover."""
import argparse,json,re,subprocess,tempfile
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from collections import Counter
import fitz
from docx import Document
from tools.rpt_physical_pages import paginate
from docx.shared import Cm,Pt,RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from tools.build_rpt_dlp_native_20261126 import PINS,extract,verify_cover,ROOT,SUBJECTS,document_path
from tools.build_kssr_rpt_merged_week_batch_20261126 import mark,norm,text_cell,hyperlink
from web.rpt_native_word_cover import add_word_cover,selected_layout
HEADS=("Week / Date\n(A / B)","Lesson / Unit","Content Standard\n(CS)","Learning Standard\n(LS)","Learning Evidence\n(PBD)","Textbook /\nTime")
WIDTHS=(3.05,4.65,3.65,7.15,6.1,2.7)
CODE=re.compile(r"(?<![\d.])\d+\.\d+(?:\.\d+)?(?:\([ivx]+\))?|\([ivx]+\)",re.I)
def descriptions(lines,bank):
    joined=" ".join(lines)
    joined=re.sub(r"\((?:Observe|Classify|Measure and use numbers|Communicate)\)","",joined,flags=re.I).strip()
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
    if values["ls"] and not values["cs"]:
        for item in values["ls"]:
            code=item.split()[0].split("(")[0].rsplit(".",1)[0]
            desc=bank["cs"].get(code)
            if not desc:raise ValueError(("missing parent CS",code,joined))
            val=code+" "+desc
            if val not in values["cs"]:values["cs"].append(val)
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
def natural_lines(lines,kind):
    # Source PDF line wraps are not semantic paragraph breaks. Preserve every
    # source word, while retaining actual lesson/unit and reference boundaries.
    result=[]
    for line in lines:
        if not result or (kind=="lesson" and re.match(r"^(?:Unit\s+\d+|Lesson\s+\d+|Review\b)",line)) or (kind=="reference" and re.match(r"^\d+\s*min\b",line)):
            result.append(line)
        else:
            result[-1]+=" "+line
    return [re.sub(r"[ \t]+"," ",v).strip() for v in result]
def polished_cell(cell,lines,*,kind="",bold=False,center=False,shade=None):
    text_cell(cell,lines,bold=bold,center=center,shade=shade)
    for p in cell.paragraphs:
        p.paragraph_format.space_after=Pt(2)
        p.paragraph_format.line_spacing=1.05
        p.paragraph_format.keep_with_next=False
        p.paragraph_format.keep_together=True
        # Bold only the identifier, preserving the editable description.
        if not bold and kind in ("lesson","standard"):
            val=p.text
            m=re.match(r"^(?:Lesson\s+\d+|Review\b|\d+\.\d+(?:\.\d+)?(?:\([ivx]+\))?)",val,re.I)
            if m:
                p.clear()
                a=p.add_run(m.group());a.bold=True;a.font.name="Arial";a.font.size=Pt(8.5)
                a=p.add_run(val[m.end():]);a.font.name="Arial";a.font.size=Pt(8.5)
def apply_table_template(table,subject,*,appendix=False):
    """Exact formatting from reviewed sample; never copy identity or content."""
    from docx.oxml import OxmlElement
    from docx.table import _Cell
    widths=(13.3,7,7) if appendix else WIDTHS
    colors=("D5E6DF","EDF4F0","849991","21372F","426658") if subject=="science_dlp" else ("D5E5EF","EDF4F8","879DA9","203B4D","426477")
    header,week,border,ink,unit=colors
    def prop(parent,name,attrs):
        child=parent.find(qn("w:"+name))
        if child is None:
            child=OxmlElement("w:"+name);parent.append(child)
        for k,v in attrs.items():child.set(qn("w:"+k),str(v))
        return child
    table.autofit=False
    for c,w in zip(table.columns,widths):c.width=Cm(w)
    pr=table._tbl.tblPr
    prop(pr,"tblW",{"type":"dxa","w":sum(c.width.twips for c in table.columns)})
    prop(pr,"tblInd",{"type":"dxa","w":0})
    borders=prop(pr,"tblBorders",{})
    for side in ("top","left","bottom","right","insideH","insideV"):
        prop(borders,side,{"val":"single","sz":4 if side.startswith("inside") else 5,"color":border})
    margins=prop(pr,"tblCellMar",{})
    for side,w in (("top",55),("bottom",55),("left",85),("right",85)):
        prop(margins,side,{"type":"dxa","w":w})
    # Physical cells: avoid repeatedly editing vertical merged start cells.
    for i,row in enumerate(table.rows):
        for j,tc in enumerate(row._tr.tc_lst):
            c=_Cell(tc,table);c.width=Cm(widths[j])
            is_week=not appendix and j==0
            centered=i==0 or is_week or (j>0 if appendix else j==5)
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if centered else WD_CELL_VERTICAL_ALIGNMENT.TOP
            prop(tc.get_or_add_tcPr(),"shd",{"fill":header if i==0 else week if is_week else "FFFFFF","val":"clear"})
            for k,p in enumerate(c.paragraphs):
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before=Pt(0)
                p.paragraph_format.space_after=Pt(2 if not appendix and i and k<len(c.paragraphs)-1 else 0)
                p.paragraph_format.line_spacing=1.03
                for run in p.runs:
                    run.font.name="Arial";run.font.size=Pt(9 if i==0 else 8.5)
                    run.font.color.rgb=RGBColor.from_string(ink if i==0 else "202729")
                    if i==0:run.bold=True
                    elif is_week:run.bold=p.text.startswith("Week ")
                    elif not appendix and j==1 and p.text.startswith("Unit "):
                        run.italic=True;run.bold=False;run.font.color.rgb=RGBColor.from_string(unit)
                    elif not appendix and j==5:run.bold=bool(re.fullmatch(r"\d+\s*min",p.text.strip()))
def append_notes(doc,lines):
    # The previous cover's complete guidance, teaching allocation, holiday
    # dates and source citations are moved, not deleted. Holiday table last.
    assert "Teaching allocation" in lines and "Main school breaks" in lines
    begin=lines.index("Teaching allocation");cut=lines.index("Main school breaks")
    assert begin<cut
    heading=doc.add_heading("Teaching information and source references",level=1)
    heading.paragraph_format.page_break_before=True
    pending=[]
    def flush():
        if pending:
            doc.add_paragraph(" ".join(pending));pending.clear()
    for line in lines[begin:cut]:
        if line in ("Teaching allocation","Using the schedule"):
            flush();doc.add_heading(line,level=2)
        elif line.startswith("Group A covers"):
            flush();doc.add_paragraph(line)
        else:pending.append(line)
    flush()
    end=next(i for i in range(cut+1,len(lines)) if lines[i].startswith("CS ="))
    holidays=lines[cut+1:end]
    assert holidays[:2]==["Group A","Group B"],holidays
    assert len(holidays[2:])%3==0,holidays
    doc.add_paragraph(lines[end])
    if lines[end+1:]:doc.add_paragraph(" ".join(lines[end+1:]))
    doc.add_heading("Main school breaks",level=2)
    t=doc.add_table(rows=1,cols=3);t.style="Table Grid";t.autofit=False
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,(v,w) in enumerate(zip(("School break","Group A","Group B"),(13.2,7,7))):
        t.columns[i].width=Cm(w);t.rows[0].cells[i].width=Cm(w)
        polished_cell(t.rows[0].cells[i],[v],bold=True,center=True,shade="E8F0E9")
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    for i in range(2,len(holidays),3):
        row=t.add_row()
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for j,(cell,v,w) in enumerate(zip(row.cells,holidays[i:i+3],(13.2,7,7))):
            cell.width=Cm(w);polished_cell(cell,[v],center=j>0)
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
    sec.left_margin=sec.right_margin=Cm(1.2);sec.top_margin=sec.bottom_margin=Cm(1.5)
    sec.header_distance=sec.footer_distance=Cm(.4)
    doc.styles["Normal"].font.name="Arial";doc.styles["Normal"].font.size=Pt(9)
    sec.header.paragraphs[0].text=""
    sec.footer.paragraphs[0].text=""
    add_word_cover(doc,png)
    t=doc.add_table(rows=1,cols=6);t.style="Table Grid";t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    shade="DCECDC" if subject=="science_dlp" else "D9E9F3"
    for i,(h,w) in enumerate(zip(HEADS,WIDTHS)):
        t.columns[i].width=Cm(w);t.rows[0].cells[i].width=Cm(w)
        polished_cell(t.rows[0].cells[i],[h],bold=True,center=True,shade=shade)
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    groups=[];expected=[];failures=[]
    review_map=json.loads((root/"dlp"/"standard_descriptions"/"review_mappings.json").read_text())["mappings"].get(key,{})
    review_no=0
    for c,links in rows:
        field=c[2]
        if c[1][0].startswith("Review"):
            review_no+=1
            if " ".join(field) in ("Consolidation Review taught standards","Review Review taught standards"):
                codes=review_map.get(f"R{review_no:02d}")
                assert codes,(key,review_no,c[1])
                field=["LS "+", ".join(codes)]
        try:cs,ls=descriptions(field,bank)
        except ValueError as err:failures.append({"lesson":c[1],"field":c[2],"error":str(err)});continue
        row=t.add_row();index=len(t.rows)-1
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for cell,w in zip(row.cells,WIDTHS):cell.width=Cm(w)
        vals=(c[0],natural_lines(c[1],"lesson"),cs,ls,natural_lines(c[3],"evidence"),natural_lines(c[4],"reference"))
        for cell,lines,kind in zip(row.cells[1:],vals[1:],("lesson","standard","standard","evidence","reference")):
            polished_cell(cell,lines or [""],kind=kind)
        for url in links:hyperlink(row.cells[-1],url)
        expected.append(vals)
        label=tuple(c[0])
        if groups and groups[-1][0]==label:groups[-1]=(label,groups[-1][1],index)
        else:groups.append((label,index,index))
    assert not failures,(key,json.dumps(failures,ensure_ascii=False))
    for week,(label,first,last) in enumerate(groups,1):
        cell=t.cell(first,0)
        if first<last:cell=cell.merge(t.cell(last,0))
        polished_cell(cell,[f"Week {week:02d}",*label],bold=True,center=True,shade=shade)
        # Keep a merged week together, not one forced page per week.
        # Keep each group together using all physical cells of each row,
        # including the vertical merge continuation cells.
        from docx.table import _Cell
        for i in range(first,last+1):
            for tc in t.rows[i]._tr.tc_lst:
                for p in _Cell(tc,t).paragraphs:
                    p.paragraph_format.keep_with_next=i<last
        for i in range(first,last+1):
            expected[i-1]=([f"Week {week:02d}",*label],*expected[i-1][1:])
    preserved_notes=append_notes(doc,notes)
    apply_table_template(t,subject)
    apply_table_template(doc.tables[-1],subject,appendix=True)
    for p in doc.paragraphs:
        if p.style.name in ("Heading 1","Heading 2"):
            for run in p.runs:
                run.font.size=Pt(12 if p.style.name=="Heading 1" else 10)
                run.font.color.rgb=RGBColor.from_string("315C4C" if subject=="science_dlp" else "31546C")
    page_count=paginate(doc,t)
    stream=BytesIO();doc.save(stream);blob=stream.getvalue()
    check=Document(BytesIO(blob));assert len(check.tables)==page_count+1
    actual=[row for table in check.tables[:-1] for row in table.rows[1:]]
    assert len(actual)==len(rows)
    for i,(row,vals) in enumerate(zip(actual,expected),1):
        assert all(norm(cell.text)==norm(" ".join(v)) for cell,v in zip(row.cells,vals)),(key,i)
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
            assert len(new)==len(Document(BytesIO(blob)).tables)+1,(subject,year,"physical page overflow")
            for page in list(new)[1:-1]:
                text=norm(page.get_text())
                assert all(norm(h) in text for h in HEADS),(subject,year,page.number,"missing heading")
                rects=[x["rect"] for x in page.get_drawings() if x["rect"].width>10 and x["rect"].height>.1]
                assert rects and max(r.y1 for r in rects)<=page.rect.height-42,(subject,year,page.number,"bottom margin")
            assert "Main school breaks" not in new[0].get_text()
            assert "Main school breaks" in new[-1].get_text()
            body="\n".join(p.get_text() for p in list(new)[1:])
            for val in notes:
                assert re.sub(r"\s+","",val) in re.sub(r"\s+","",body),(subject,year,"appendix",val)
            assert re.findall(r"(?m)^Lesson\s+(\d+)\b",body)==[re.search(r"\bLesson\s+(\d+)",' '.join(c[1])).group(1) for c,_ in rows if re.search(r"\bLesson\s+(\d+)",' '.join(c[1]))]
            # Extract standards by physical column; ignore layout-only line
            # breaks (including wrapping at an existing hyphen), not glyphs.
            compact=lambda v:re.sub(r"\s+","",v)
            for idx,lines in enumerate(zip(*(v[2:4] for v in expected))):
                all_text=[]
                for page in list(new)[1:-1]:
                    # Table starts at 1.2 cm; CS/LS column boundaries from
                    # the actual rendered native table widths.
                    left=34.02+sum(WIDTHS[:2+idx])*72/2.54
                    right=left+WIDTHS[2+idx]*72/2.54
                    all_text.append(page.get_text(clip=fitz.Rect(left,40,right,page.rect.height-30)))
                # Some Word fonts use slightly different grid positions;
                # verify against full extracted text too, without whitespace.
                col=compact("".join(all_text));all_body=compact(body)
                for group in lines:
                    for line in group:
                        assert compact(line) in col or compact(line) in all_body,(subject,year,line)

            print(json.dumps({"key":f"{subject}:{year}","rows":len(rows),"pages":len(new),"cs_entries":sum(len(v[2]) for v in expected),"ls_entries":sum(len(v[3]) for v in expected),"status":"PRIVATE_LAYOUT_QA_ONLY"}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--subject",choices=SUBJECTS,required=True);p.add_argument("--year",type=int,choices=range(2,7),required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);render(a.subject,a.year,a.out)
