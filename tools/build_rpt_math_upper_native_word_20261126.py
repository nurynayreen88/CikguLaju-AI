"""Private native Word/PDF layout for exact approved Mathematics SK Y4–6."""
from collections import Counter
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import argparse
import json
import re
import subprocess
import tempfile
import fitz
from docx import Document
from tools.rpt_source_table_polish import format_source_cell, fixed_grid
from docx.shared import Cm, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from rpt_2027.matematik import sk_documents
from tools.build_kssr_rpt_merged_week_batch_20261126 import mark,norm,text_cell
from web.rpt_native_word_cover import add_word_cover,cover_png

ROOT=Path("rpt_2027")
BANDS=(41,141,198,370,576,811)
WIDTHS=(3.56,2.03,6.12,7.33,8.36)
HEADERS=("Minggu dan tarikh","Lesson","Unit dan tajuk","SK, SP dan rujukan","Evidens pentaksiran")
WEEK=re.compile(r"^M(\d{2})\b")
LESSON=re.compile(r"^(\d{3})\s+(30|60) min$")
TEAL=(8/255,100/255,93/255)

def spans_by_column(page,top,bottom):
    columns=[[] for _ in range(5)]
    all_text=[]
    for block in page.get_text("dict",clip=fitz.Rect(40,top,812,bottom))["blocks"]:
        for line in block.get("lines",()):
            parts=[[] for _ in range(5)]
            for span in line["spans"]:
                value=span["text"]
                if not value.strip():continue
                x=span["origin"][0]
                matches=[i for i,(l,r) in enumerate(zip(BANDS,BANDS[1:])) if l-.5<=x<r-.5]
                assert len(matches)==1,(page.number,top,"Unknown column origin",x)
                i=matches[0]
                parts[i].append(value)
                all_text.append(value)
            for i,values in enumerate(parts):
                if values:columns[i].append(" ".join(values))
    cells=tuple("\n".join(c).strip() for c in columns)
    letters=lambda s:Counter(c for c in s if not c.isspace())
    assert letters("".join(all_text))==letters("".join(cells))
    return cells

def extract(source):
    rows=[];intro=None;expected=[]
    with fitz.open(source) as pdf:
        for p in list(pdf)[1:]:
            assert not p.get_links(),"Unexpected links in approved Math PDF"
            draws=p.get_drawings()
            candidates=[d["rect"] for d in draws if d.get("fill") and
                        max(abs(a-b) for a,b in zip(d["fill"],TEAL))<.015 and
                        abs(d["rect"].x0-BANDS[0])<1 and abs(d["rect"].x1-BANDS[-1])<1]
            assert len(candidates)==1,(p.number,"Original header rectangle missing",len(candidates))
            h=candidates[0]
            headers=spans_by_column(p,h.y0,h.y1)
            assert tuple(map(norm,headers))==HEADERS,(p.number,"Unexpected source headings")
            preamble=p.get_text("text",clip=fitz.Rect(0,0,p.rect.width,h.y0)).strip()
            if intro is None:intro=preamble
            elif preamble:assert preamble==intro,"Unexpected extra pre-table content"
            ys=[h.y1]
            rules=sorted(d["rect"].y0 for d in draws if d["rect"].height<.2 and
                         abs(d["rect"].x0-BANDS[0])<1 and abs(d["rect"].x1-BANDS[-1])<1 and
                         d["rect"].y0>h.y1+.5)
            for y in rules:
                if y-ys[-1]>.5:ys.append(y)
            assert len(ys)>1
            for top,bottom in zip(ys,ys[1:]):
                if bottom-top<3:continue
                cells=spans_by_column(p,top,bottom)
                if not any(cells):continue
                week=WEEK.match(cells[0])
                assert week,(p.number,top,"Unclassified source row")
                lesson=LESSON.fullmatch(norm(cells[1]))
                if lesson:
                    assert all(cells)
                    expected.append((int(week[1]),int(lesson[1]),int(lesson[2])))
                else:
                    assert cells[1] and not any(cells[2:]),"Unclassified closure row"
                rows.append((int(week[1]),cells,bool(lesson)))
    assert intro
    assert [n for _,n,_ in expected]==list(range(1,118))
    assert Counter(m for _,_,m in expected)=={30:42,60:75}
    assert max(w for w,_,_ in expected)==38
    assert not {w for w,_,_ in expected}&{6,18,19}
    return intro,rows,expected

def build_word(year,root=ROOT):
    source=sk_documents.document_path(year,root=Path(root)/"matematik")
    assert source is not None
    raw=source.read_bytes()
    assert sha256(raw).hexdigest()==sk_documents.DIGESTS[year]
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
    intro,rows,expected=extract(source)
    doc=Document();s=doc.sections[0]
    s.page_width=Cm(29.7);s.page_height=Cm(21)
    s.left_margin=s.right_margin=Cm(1.15)
    s.top_margin=s.bottom_margin=Cm(1.1)
    s.header_distance=s.footer_distance=Cm(.45)
    doc.styles["Normal"].font.name="Arial";doc.styles["Normal"].font.size=Pt(8.5)
    s.footer.paragraphs[0].text=f"RPT 2027 · Matematik SK Tahun {year} · Kumpulan A dan B"
    add_word_cover(doc,cover_png(raw,lock,f"matematik:{year}"))
    for i,line in enumerate(intro.splitlines()):
        p=doc.add_paragraph()
        p.paragraph_format.space_after=Pt(2)
        r=p.add_run(line);r.bold=i==0;r.font.size=Pt(14 if i==0 else 8.5)
    t=doc.add_table(rows=1,cols=5);t.style="Table Grid";t.autofit=False
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,(name,w) in enumerate(zip(HEADERS,WIDTHS)):
        t.columns[i].width=Cm(w);t.rows[0].cells[i].width=Cm(w)
        text_cell(t.rows[0].cells[i],[name],bold=True,center=True,shade="D9E9F3")
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    groups=[]
    for week,cells,teaching in rows:
        row=t.add_row();i=len(t.rows)-1
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for c,w in zip(row.cells,WIDTHS):c.width=Cm(w)
        if teaching:
            for j,(c,value) in enumerate(zip(row.cells[1:],cells[1:]),1):
                format_source_cell(c,value.splitlines(),text_cell,preserve=j==1)
        else:
            text_cell(row.cells[1].merge(row.cells[4]),cells[1].splitlines(),shade="EAF1E3")
        if groups and groups[-1][0]==week:
            assert norm(groups[-1][3])==norm(cells[0]),"Source week dates differ"
            groups[-1]=(week,groups[-1][1],i,cells[0])
        else:groups.append((week,i,i,cells[0]))
    for _,first,last,label in groups:
        c=t.cell(first,0)
        if first<last:c=c.merge(t.cell(last,0))
        text_cell(c,label.splitlines(),bold=True,center=True,shade="EAF1E3")
    fixed_grid(t,"D9E9F3")
    out=BytesIO();doc.save(out);blob=out.getvalue()
    check=Document(BytesIO(blob));table=check.tables[0]
    assert len(table.rows)==len(rows)+1
    for i,(_,cells,teaching) in enumerate(rows,1):
        assert norm(table.cell(i,0).text)==norm(cells[0])
        if teaching:
            assert all(norm(c.text)==norm(v) for c,v in zip(table.rows[i].cells[1:],cells[1:]))
        else:
            assert norm(table.cell(i,1).text)==norm(cells[1])
    for _,first,last,_ in groups:
        assert all(table.cell(first,0)._tc is table.cell(i,0)._tc for i in range(first,last+1))
    return blob,raw,expected

def render(year,out):
    blob,raw,expected=build_word(year)
    name=f"RPT_MATEMATIK_SK_TAHUN_{year}_2027"
    word=out/(name+".docx");word.write_bytes(blob)
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),
                        "--headless","--convert-to","pdf","--outdir",str(folder),str(word.resolve())],timeout=180,check=True)
        target=out/(name+".pdf")
        with fitz.open(folder/(name+".pdf")) as gen,fitz.open(stream=raw,filetype="pdf") as orig,fitz.open() as final:
            assert len(gen)>1
            final.insert_pdf(orig,from_page=0,to_page=0);final.insert_pdf(gen,from_page=1)
            final.save(target,garbage=4,deflate=True)
        with fitz.open(target) as pdf,fitz.open(stream=raw,filetype="pdf") as orig:
            assert pdf[0].get_pixmap().samples==orig[0].get_pixmap().samples
            text="\n".join(p.get_text() for p in list(pdf)[1:])
            found=[(int(n),int(m)) for n,m in re.findall(r"(?m)^(\d{3})\s*\n(30|60) min\s*$",text)]
            assert found==[(n,m) for _,n,m in expected],(len(found),len(expected))
            for p in list(pdf)[1:]:
                assert abs(p.rect.width-841.89)<2 and abs(p.rect.height-595.28)<2
                assert all(norm(h).casefold() in norm(p.get_text()).casefold() for h in HEADERS)
            print(json.dumps({"year":year,"lessons":len(expected),"minutes":sum(m for _,_,m in expected),
                              "pages_before":len(orig),"pages_after":len(pdf),"status":"PRIVATE_LAYOUT_QA_ONLY"}),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--year",type=int,choices=(4,5,6),required=True)
    parser.add_argument("--out",type=Path,required=True);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);render(args.year,args.out)
