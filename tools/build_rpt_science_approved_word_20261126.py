"""Private editable Science SK Y5/Y6 from the actual approved PDF, not old staged RPT."""
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
from rpt_2027.sains import sk_documents
from scripts.build_web_rpt_weekly_suggestions import approved_science_weeks, SCIENCE_PDP
from tools.build_kssr_rpt_merged_week_batch_20261126 import text_cell, mark, norm
from web.rpt_native_word_cover import add_word_cover, cover_png

ROOT=Path("rpt_2027")
PINS={5:"281d25b8b37cfda50caa22ebcc9ee235767e1bfb4a8a4cfad171a5bf324a1e8b",
      6:"0f168595c8c6259c455f143aeeb98489152a85cc599e5c1d60db88d19503d477"}
BANDS=(31.5,150.5,320.6,417.0,714.7,794.1)
WIDTHS=(4.15,5.95,3.37,10.40,2.78)
WEEK=re.compile(r"^M(\d{2})\b")

def extract(path,year):
    plan=approved_science_weeks(path,year)
    expected=[(int(w),n) for w,row in plan.items() for n in row[4][""]]
    rows=[];headers=None;seen=[]
    with fitz.open(path) as pdf:
        for page in list(pdf)[1:]:
            assert not page.get_links(),"Unexpected source links"
            rules=sorted(round(d["rect"].y0,2) for d in page.get_drawings()
                         if d["rect"].height<.2 and abs(d["rect"].x0-BANDS[0])<1
                         and abs(d["rect"].x1-BANDS[-1])<1)
            ys=[]
            for y in rules:
                if not ys or y-ys[-1]>0.5:ys.append(y)
            assert len(ys)>2,"Table rules missing"
            page_header=0
            for top,bottom in zip(ys,ys[1:]):
                if bottom-top<3:continue
                # Read the native text once; independent cell clips can lose a glyph
                # at a boundary due to font metrics. Assign whole spans by origin.
                # Reject any actual multi-column overflow instead of silently dropping text.
                rect=fitz.Rect(BANDS[0]-1,top,BANDS[-1]+1,bottom)
                by_col=[[] for _ in range(5)]
                original=[]
                for block in page.get_text("dict",clip=rect)["blocks"]:
                    for line in block.get("lines",()):
                        per_line=[[] for _ in range(5)]
                        for span in line["spans"]:
                            text=span["text"]
                            if not text.strip():continue
                            x=span["origin"][0]
                            cols=[i for i,(l,r) in enumerate(zip(BANDS,BANDS[1:]))
                                  if l-.5<=x<r-.5]
                            assert len(cols)==1,(page.number,top,"Unknown span origin",x)
                            i=cols[0]
                            assert span["bbox"][2]<=BANDS[i+1]+2,(page.number,top,"Span overflows cell",i,span["bbox"])
                            original.append(text);per_line[i].append(text)
                        for i,parts in enumerate(per_line):
                            if parts:by_col[i].append(" ".join(parts))
                cells=["\n".join(lines).strip() for lines in by_col]
                if not any(cells):continue
                letters=lambda v:Counter(c for c in v if not c.isspace())
                assert letters("".join(original))==letters("".join(cells)),"Source character loss"
                if "MINGGU" in cells[0].upper() and not WEEK.match(cells[0]):
                    if headers is None:headers=tuple(cells)
                    assert tuple(map(norm,cells))==tuple(map(norm,headers)),"Source header changed"
                    page_header+=1
                    continue
                numbers=[int(n) for cell in cells[1:] for n in SCIENCE_PDP.findall(cell)]
                week=WEEK.match(cells[0])
                if numbers:
                    assert len(numbers)==1 and week,"Invalid lesson week or row"
                    seen.append((int(week[1]),numbers[0]))
                else:
                    assert week,"Unclassified non-lesson row"
                rows.append((int(week[1]),tuple(cells),tuple(numbers)))
            assert page_header==1,"Missing repeated original headings"
    assert headers and all(headers)
    assert seen==expected,(len(seen),len(expected),"Source teaching identity mismatch")
    return headers,rows,expected

def build_word(year,root=ROOT):
    source=sk_documents.document_path(year,root=Path(root)/"sains")
    assert source is not None
    raw=source.read_bytes()
    assert sha256(raw).hexdigest()==PINS[year]
    lock=json.loads((Path(root)/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
    headers,rows,expected=extract(source,year)
    doc=Document();s=doc.sections[0]
    s.page_width=Cm(29.7);s.page_height=Cm(21)
    s.left_margin=s.right_margin=Cm(1.15)
    s.top_margin=s.bottom_margin=Cm(1.1)
    s.header_distance=s.footer_distance=Cm(.45)
    doc.styles["Normal"].font.name="Arial";doc.styles["Normal"].font.size=Pt(8.5)
    s.header.paragraphs[0].text=""
    s.footer.paragraphs[0].text="RPT 2027 · Kumpulan A dan B"
    add_word_cover(doc,cover_png(raw,lock,f"sains:{year}"))
    table=doc.add_table(rows=1,cols=5);table.style="Table Grid";table.autofit=False
    table.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,(text,width) in enumerate(zip(headers,WIDTHS)):
        table.columns[i].width=Cm(width);table.rows[0].cells[i].width=Cm(width)
        text_cell(table.rows[0].cells[i],text.splitlines(),bold=True,center=True,shade="DCECDC")
    mark(table.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    groups=[]
    for week,cells,numbers in rows:
        row=table.add_row();i=len(table.rows)-1
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for j,(cell,text,width) in enumerate(zip(row.cells,cells,WIDTHS)):
            cell.width=Cm(width)
            if j:format_source_cell(cell,text.splitlines() or [""],text_cell,preserve=j==1)
        if groups and groups[-1][0]==week:
            assert norm(groups[-1][3])==norm(cells[0]),"Week labels differ"
            groups[-1]=(week,groups[-1][1],i,cells[0])
        else:groups.append((week,i,i,cells[0]))
    for week,first,last,label in groups:
        merged=table.cell(first,0)
        if first!=last:merged=merged.merge(table.cell(last,0))
        text_cell(merged,label.splitlines(),bold=True,center=True,shade="EAF1E3")
    fixed_grid(table,"DCECDC")
    out=BytesIO();doc.save(out);blob=out.getvalue()
    check=Document(BytesIO(blob));t=check.tables[0]
    assert len(t.rows)==len(rows)+1
    for i,(_,cells,_) in enumerate(rows,1):
        assert all(norm(c.text)==norm(x) for c,x in zip(t.rows[i].cells,cells))
    for _,first,last,_ in groups:
        assert all(t.cell(first,0)._tc is t.cell(i,0)._tc for i in range(first,last+1))
    return blob,raw,expected,headers

def render(year,out):
    blob,raw,expected,headers=build_word(year)
    name=f"RPT_SAINS_SK_TAHUN_{year}_2027"
    word=out/(name+".docx");word.write_bytes(blob)
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),
                        "--headless","--convert-to","pdf","--outdir",str(folder),str(word.resolve())],
                        timeout=180,check=True)
        target=out/(name+".pdf")
        with fitz.open(folder/(name+".pdf")) as gen, fitz.open(stream=raw,filetype="pdf") as orig,fitz.open() as final:
            assert len(gen)>1
            final.insert_pdf(orig,from_page=0,to_page=0);final.insert_pdf(gen,from_page=1)
            final.save(target,garbage=4,deflate=True)
        with fitz.open(target) as pdf,fitz.open(stream=raw,filetype="pdf") as orig:
            assert pdf[0].get_pixmap().samples==orig[0].get_pixmap().samples
            text="\n".join(p.get_text() for p in list(pdf)[1:])
            assert [int(n) for n in SCIENCE_PDP.findall(text)]==[n for _,n in expected]
            for p in list(pdf)[1:]:
                assert abs(p.rect.width-841.89)<2 and abs(p.rect.height-595.28)<2
                assert all(norm(h).casefold() in norm(p.get_text()).casefold() for h in headers)
            print(json.dumps({"year":year,"lessons":len(expected),"pages_before":len(orig),
                              "pages_after":len(pdf),"status":"PRIVATE_LAYOUT_QA_ONLY"}),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--year",type=int,choices=PINS,required=True)
    parser.add_argument("--out",type=Path,required=True);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);render(args.year,args.out)
