"""Native editable DLP RPT from exact active PDF. No calendar or curriculum changes."""
import argparse,json,re,subprocess,tempfile
from pathlib import Path
from io import BytesIO
from hashlib import sha256
from collections import Counter
import fitz
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from rpt_2027.dlp.documents import document_path,SUBJECTS
from tools.build_kssr_rpt_merged_week_batch_20261126 import mark,norm,text_cell,hyperlink
from web.rpt_native_word_cover import add_word_cover,cover_png,selected_layout
ROOT=Path("rpt_2027")
PINS={
  "mathematics_dlp:2": "d66bf14378e2ceb00c12dbd3fd66ac19eb18d7ccc8437eda94e2c6db6b5441aa",
  "science_dlp:2": "c6d84f552078c1c1949e1e87c9a2329af64725c3b9d4ef5c683d8fc6a7c89a83",
  "mathematics_dlp:3": "0580026d81648f07283052e1f11c83eeecd50c6f552ab9a0d9a6535adfa7df09",
  "science_dlp:3": "8c518d0b0be79ae51c656e254e6588e14e01f7ace99f622449781cb58d59d7ed",
  "mathematics_dlp:4": "6f256b646bd558dccacea23c13e4283bb563e0949bdf937b2ddbd35fc14448d1",
  "science_dlp:4": "eff2cd8354c00aae176b069dc19aacbdcfb81b2ac84527b3c3c6c015ebdd2413",
  "mathematics_dlp:5": "4dd0f9109c0a45e0cff2586e8342a16282a88f25f1b8e498fa27bbf04be0fb39",
  "science_dlp:5": "8eee415688d9572b6c02046e3fc1bef5d0fedeea11871a52b9d39d01600601b2",
  "mathematics_dlp:6": "e90acb6896ce438d619b9d159081ee0ea7f39d27f62dfbd5a41d648bf038d488",
  "science_dlp:6": "991465fcfacc1b1925f9ded6cf12b8da7a9ac220c9321ef4011537900bdd97db"
}
BANDS=(35.5,138.9,293.4,396.8,671.8,806.5)
HEADS=("Date range A / B","Lesson / Unit","CS / LS","Learning evidence (PBD)","Book reference / Time")
WIDTHS=(3.55,5.45,3.65,9.7,4.75)
def verify_cover(pdf,layout):
    p=pdf[0]
    assert abs(p.rect.width-layout["page_width"])<=layout["tolerance_pt"]
    assert abs(p.rect.height-layout["page_height"])<=layout["tolerance_pt"]
    spans=[s for b in p.get_text("dict")["blocks"] for line in b.get("lines",[]) for s in line["spans"]]
    underscores=[s for s in spans if re.fullmatch(r"_{20,}",s["text"])]
    assert len(underscores)==2
    for box,span in zip(("school_row_top_left","teacher_row_top_left"),sorted(underscores,key=lambda s:s["bbox"][1])):
        assert fitz.Rect(layout[box]).contains(fitz.Rect(span["bbox"]))
    logo=[s for s in spans if s["text"].strip().upper()=="SCHOOL LOGO"]
    assert len(logo)==1 and fitz.Rect(layout["logo_interior_top_left"]).contains(fitz.Rect(logo[0]["bbox"]))
    assert fitz.Rect(layout["logo_interior_top_left"]).contains(fitz.Rect(layout["logo_image_safe_top_left"]))
    # Check all three overlay areas contain only original placeholder text.
    for field in ("school_row_top_left","teacher_row_top_left","logo_interior_top_left"):
        region=fitz.Rect(layout[field])
        for span in spans:
            if not region.intersects(fitz.Rect(span["bbox"])):continue
            assert re.fullmatch(r"_{20,}",span["text"]) or span["text"].strip().upper()=="SCHOOL LOGO",(field,span["text"])
def cells(page,top,bottom):
    clip=fitz.Rect(35.2,top,806.8,bottom)
    cols=[[] for _ in range(5)]
    for block in page.get_text("dict",clip=clip)["blocks"]:
        for line in block.get("lines",[]):
            for span in line["spans"]:
                v=span["text"]
                if not v.strip():continue
                x,y=span["origin"]
                idx=[i for i,(a,b) in enumerate(zip(BANDS,BANDS[1:])) if a-.3<=x<b-.3]
                assert len(idx)==1,(page.number,x,v)
                cols[idx[0]].append((y,x,v))
    out=[]
    for col in cols:
        lines=[]
        for item in sorted(col):
            if not lines or abs(lines[-1][0][0]-item[0])>.5:lines.append([])
            lines[-1].append(item)
        out.append([" ".join(v for _,_,v in sorted(line,key=lambda a:a[1])).strip() for line in lines])
    chars=lambda t:Counter(c for c in t if not c.isspace())
    assert chars(page.get_text(clip=clip))==chars("".join(v for col in out for v in col)),(page.number,top,bottom)
    return out
def extract(pdf):
    rows=[]
    all_links=[]
    for p in list(pdf)[1:]:
        rules=sorted({round(d["rect"].y0,3) for d in p.get_drawings() if d["type"]=="s" and d["rect"].height<.2 and abs(d["rect"].x0-35.5)<1 and abs(d["rect"].x1-806.5)<1})
        assert len(rules)>2,(p.number,rules)
        headers=cells(p,rules[0],rules[1])
        assert [norm(" ".join(c)) for c in headers]==list(HEADS),(p.number,headers)
        for top,bottom in zip(rules[1:],rules[2:]):
            c=cells(p,top,bottom)
            if not any(c):continue
            assert c[0] and any(c[1:]),(p.number,top,c)
            clip=fitz.Rect(35.2,top,806.8,bottom)
            links=[]
            for link in p.get_links():
                if clip.contains(link["from"]):
                    assert link["kind"]==fitz.LINK_URI
                    links.append(link["uri"])
            rows.append((c,links));all_links.extend(links)
        assert not p.get_text(clip=fitz.Rect(35.2,rules[-1]+1,806.8,550)).strip(),(p.number,"Unexpected content below table")
    assert rows
    assert Counter(all_links)==Counter(l["uri"] for p in list(pdf)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI)
    return rows
def build_word(subject,year,root=ROOT):
    key=f"{subject}:{year}"
    source=document_path(subject,year,root=Path(root)/"dlp")
    assert source is not None
    raw=source.read_bytes()
    assert sha256(raw).hexdigest()==PINS[key]
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
    layout=selected_layout(lock,key,PINS[key])
    with fitz.open(source) as pdf:
        verify_cover(pdf,layout)
        rows=extract(pdf)
    doc=Document();sec=doc.sections[0]
    sec.page_width=Cm(29.7);sec.page_height=Cm(21)
    sec.left_margin=sec.right_margin=Cm(1.2);sec.top_margin=sec.bottom_margin=Cm(1.05)
    sec.header_distance=sec.footer_distance=Cm(.4)
    doc.styles["Normal"].font.name="Arial";doc.styles["Normal"].font.size=Pt(8.5)
    sec.header.paragraphs[0].text=f"YEARLY TEACHING PLAN 2027 • {SUBJECTS[subject].upper()} (DLP) • YEAR {year}"
    sec.footer.paragraphs[0].text="Group A and Group B • CikguLaju"
    add_word_cover(doc,cover_png(raw,lock,key))
    t=doc.add_table(rows=1,cols=5);t.style="Table Grid";t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    shade="DCECDC" if subject=="science_dlp" else "D9E9F3"
    for i,(h,w) in enumerate(zip(HEADS,WIDTHS)):
        t.columns[i].width=Cm(w);t.rows[0].cells[i].width=Cm(w)
        text_cell(t.rows[0].cells[i],[h],bold=True,center=True,shade=shade)
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    groups=[]
    for c,links in rows:
        row=t.add_row();index=len(t.rows)-1
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for cell,w in zip(row.cells,WIDTHS):cell.width=Cm(w)
        for cell,vals in zip(row.cells[1:],c[1:]):text_cell(cell,vals or [""])
        for uri in links:hyperlink(row.cells[4],uri)
        label=tuple(c[0])
        if groups and groups[-1][0]==label:
            groups[-1]=(label,groups[-1][1],index)
        else:groups.append((label,index,index))
    for label,first,last in groups:
        cell=t.cell(first,0)
        if first<last:cell=cell.merge(t.cell(last,0))
        text_cell(cell,list(label),bold=True,center=True,shade=shade)
    stream=BytesIO();doc.save(stream);blob=stream.getvalue()
    check=Document(BytesIO(blob));t=check.tables[0]
    assert len(t.rows)==len(rows)+1
    for i,(c,_) in enumerate(rows,1):
        assert all(norm(cell.text)==norm(" ".join(v)) for cell,v in zip(t.rows[i].cells,c)),(key,i)
    for label,first,last in groups:
        assert all(t.cell(first,0)._tc is t.cell(i,0)._tc for i in range(first,last+1))
    return blob,raw,rows
def render(subject,year,out):
    blob,raw,rows=build_word(subject,year)
    name=f"RPT_{subject}_Year_{year}_2027"
    word=out/(name+".docx");word.write_bytes(blob)
    with tempfile.TemporaryDirectory() as td:
        folder=Path(td)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",str(folder),str(word.resolve())],check=True,timeout=180)
        target=out/(name+".pdf")
        with fitz.open(folder/(name+".pdf")) as gen,fitz.open(stream=raw,filetype="pdf") as old,fitz.open() as new:
            assert len(gen)>1
            new.insert_pdf(old,from_page=0,to_page=0);new.insert_pdf(gen,from_page=1)
            new.save(target,garbage=4,deflate=True)
        with fitz.open(target) as new,fitz.open(stream=raw,filetype="pdf") as old:
            assert old[0].get_pixmap().samples==new[0].get_pixmap().samples
            for page in list(new)[1:]:
                assert all(norm(h) in norm(page.get_text()) for h in HEADS)
                assert page.get_pixmap(matrix=fitz.Matrix(.5,.5),alpha=False).width>0
            def lessons(pdf):
                return re.findall(r"(?m)^Lesson\s+(\d+)\b","\n".join(p.get_text() for p in list(pdf)[1:]))
            assert lessons(new)==lessons(old) and lessons(new)
            print(json.dumps({"subject":subject,"year":year,"rows":len(rows),"numbered_lessons":len(lessons(old)),"pages_before":len(old),"pages_after":len(new),"status":"PRIVATE_LAYOUT_QA_ONLY"}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--subject",choices=SUBJECTS,required=True);p.add_argument("--year",type=int,choices=range(2,7),required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);render(a.subject,a.year,a.out)
