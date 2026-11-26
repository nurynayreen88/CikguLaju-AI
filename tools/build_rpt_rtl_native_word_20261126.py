"""Private RTL RPT layout candidate; exact staged source, no academic promotion."""
from collections import Counter
from datetime import date
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
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from scripts.build_web_rpt_weekly_suggestions import read_weeks,SUBJECTS
from scripts.reschedule_web_rpt_teaching_weeks import pdf_rows,TOP
from tools.build_kssr_rpt_merged_week_batch_20261126 import mark,norm,text_cell,hyperlink,MARKER
from web.rpt_native_word_cover import add_word_cover,cover_png

ROOT=Path("rpt_2027/web_2027_pdfs")
BANDS=(35,198.89,408.89,533.89,713.89,818.89)
WIDTHS=(3.15,6.25,4.30,7.60,6.10)
HEADERS=("MINGGU / TARIKH","UNIT / TAJUK / PdP","SK","SP","CATATAN / BAHAN")
RTL=re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
BAD=re.compile(r"[\ufffd\ue000-\uf8ff\ufb50-\ufdff\ufe70-\ufeff]")
DATE=re.compile(r"\d{2}/\d{2}/2027")
WEEK=re.compile(r"\bM(\d{2})\b")

def clip_cells(page,rect):
    physical=[]
    for a,b in zip(BANDS[:4],BANDS[1:5]):
        cell=page.get_text("text",clip=fitz.Rect(a,rect.y0,b,rect.y1)).strip()
        if BAD.search(cell):raise ValueError("Source has unresolved or presentation-form glyph; need logical source adapter")
        physical.append(cell)
    whole=page.get_text("text",clip=rect)
    if Counter(norm(whole).split())!=Counter(norm(" ".join(physical)).split()):
        raise ValueError("Source text crosses RTL column boundary")
    return tuple(reversed(physical))

def extract(path,subject):
    dates,weeks=read_weeks(path,SUBJECTS[subject])
    assigned={(c,n):w for w,components in weeks.items() for c,ids in components.items() for n in ids}
    groups={};closures={};used=[];ids=[]
    with fitz.open(path) as pdf:
        rows=pdf_rows(pdf,True)
        assert len(rows)==len(assigned) and {i for i,_,_ in rows}==set(assigned)
        for ident,pageno,rect in rows:
            page=pdf[pageno]
            cells=clip_cells(page,rect)
            markers=[MARKER.fullmatch(line.strip()) for line in cells[0].splitlines()]
            assert [(m[1] or "",int(m[2])) for m in markers if m]==[ident]
            urls=[]
            for link in page.get_links():
                if rect.contains(link["from"]):
                    assert link["kind"]==fitz.LINK_URI
                    urls.append(link["uri"])
            used.extend(urls);ids.append(ident)
            groups.setdefault(assigned[ident],[]).append((ident,cells,urls))
        for page in list(pdf)[1:]:
            for draw in page.get_drawings():
                rect=draw["rect"]
                if draw["type"] not in ("f","fs") or abs(rect.x1-BANDS[-1])>.1 or abs(rect.width-105)>.1:continue
                label=page.get_text(clip=rect)
                if "Cuti sekolah" not in label:continue
                match=WEEK.search(label);days=DATE.findall(label)
                assert match and len(days)==4
                body=page.get_text(clip=fitz.Rect(BANDS[0],rect.y0,BANDS[-2],rect.y1)).strip()
                assert body and not MARKER.search(body)
                week=int(match[1]);item=(tuple(days),body)
                assert week not in closures or closures[week]==item
                closures[week]=item
        assert not set(groups)&set(closures)
        assert list(groups)==sorted(groups)
        assert Counter(used)==Counter(l["uri"] for p in list(pdf)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI)
    return dates,groups,closures,ids,used

def rtl_cell(cell,value,*,bold=False,center=False,shade=None):
    text_cell(cell,value.splitlines() or [""],bold=bold,center=center,shade=shade)
    for p in cell.paragraphs:
        if RTL.search(p.text):
            if not center:p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
            mark(p._p.get_or_add_pPr(),"w:bidi",{"w:val":"1"})
            for run in p.runs:
                if RTL.search(run.text):
                    run.font.name="Amiri"
                    run.font.size=Pt(10)
                    props=run._r.get_or_add_rPr()
                    fonts=props.find(qn("w:rFonts"))
                    if fonts is not None:fonts.set(qn("w:cs"),"Amiri")
                    mark(props,"w:rtl",{"w:val":"1"})
                    mark(props,"w:szCs",{"w:val":"20"})
                    mark(props,"w:lang",{"w:bidi":"ar-SA"})

def build_word(subject,year,root=ROOT):
    root=Path(root);key=f"{subject}:{year}"
    manifest=json.loads((root/"manifest.json").read_text())["files"]
    lock=json.loads((root/"original_cover_layout_verified.json").read_text())
    entry=manifest[key];source=root/entry["path"];raw=source.read_bytes()
    assert sha256(raw).hexdigest()==entry["sha256"]
    dates,groups,closures,ids,links=extract(source,subject)
    doc=Document();section=doc.sections[0]
    section.page_width=Cm(29.7);section.page_height=Cm(21)
    section.left_margin=section.right_margin=Cm(1.15)
    section.top_margin=section.bottom_margin=Cm(1.1)
    section.header_distance=section.footer_distance=Cm(.45)
    section.header.paragraphs[0].text=f"RPT 2027 · {subject.replace('_',' ').upper()} · TAHUN {year}"
    section.footer.paragraphs[0].text="RPT 2027 · DRAF SEMAKAN · Kumpulan A dan B"
    add_word_cover(doc,cover_png(raw,lock,key))
    table=doc.add_table(rows=1,cols=5);table.style="Table Grid";table.autofit=False
    table.alignment=WD_TABLE_ALIGNMENT.CENTER
    mark(table._tbl.tblPr,"w:bidiVisual",{"w:val":"1"})
    color="ECE4F6" if subject=="pendidikan_islam" else "E7EEDB"
    for i,(header,width) in enumerate(zip(HEADERS,WIDTHS)):
        table.columns[i].width=Cm(width);table.rows[0].cells[i].width=Cm(width)
        rtl_cell(table.rows[0].cells[i],header,bold=True,center=True,shade=color)
    mark(table.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    expected=[];ranges=[]
    def add_row():
        row=table.add_row()
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for cell,w in zip(row.cells,WIDTHS):cell.width=Cm(w)
        return row
    for week in sorted(set(groups)|set(closures)):
        first=len(table.rows)
        if week in closures:
            days,body=closures[week]
            row=add_row();rtl_cell(row.cells[1].merge(row.cells[4]),body)
        else:
            days=tuple(date.fromisoformat(d).strftime("%d/%m/%Y") for d in dates[week])
            for identity,cells,urls in groups[week]:
                row=add_row()
                for cell,value in zip(row.cells[1:],cells):rtl_cell(cell,value)
                for url in urls:hyperlink(row.cells[4],url)
                expected.append((len(table.rows)-1,identity,cells))
        last=len(table.rows)-1
        merged=table.cell(first,0)
        if last>first:merged=merged.merge(table.cell(last,0))
        rtl_cell(merged,f"{week:02d}\nKumpulan A\n{days[0]} – {days[1]}\nKumpulan B\n{days[2]} – {days[3]}",
                 bold=True,center=True,shade=color)
        ranges.append((first,last))
    stream=BytesIO();doc.save(stream);blob=stream.getvalue()
    check=Document(BytesIO(blob));t=check.tables[0]
    assert t._tbl.tblPr.find(qn("w:bidiVisual")) is not None
    for i,identity,cells in expected:
        assert all(norm(val) in norm(cell.text) for cell,val in zip(t.rows[i].cells[1:],cells))
    assert [i for _,i,_ in expected]==ids
    for first,last in ranges:
        assert all(t.cell(first,0)._tc is t.cell(i,0)._tc for i in range(first,last+1))
    assert Counter(rel.target_ref for rel in check.part.rels.values() if rel.reltype==RT.HYPERLINK)==Counter(set(links))
    return blob,raw,ids,links

def render(subject,year,out):
    blob,raw,ids,links=build_word(subject,year)
    name=f"RPT_{subject}_tahun_{year}_2027"
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
            found=[(m[1] or "",int(m[2])) for m in re.finditer(r"(?m)^(?:(PJ|PK) )?(?:PdP|Lesson) (\d{3})\s*$",text)]
            assert found==ids
            for p in list(pdf)[1:]:
                assert abs(p.rect.width-841.89)<2 and abs(p.rect.height-595.28)<2
                assert all(norm(h).casefold() in norm(p.get_text()).casefold() for h in HEADERS)
            assert Counter(l["uri"] for p in list(pdf)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI)==Counter(links)
            print(json.dumps({"subject":subject,"year":year,"lessons":len(ids),"links":len(links),
                              "pages_before":len(orig),"pages_after":len(pdf),
                              "status":"PRIVATE_LAYOUT_QA_ONLY_RTL_VISUAL_REVIEW_REQUIRED"}),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--subject",choices=("pendidikan_islam","bahasa_arab"),required=True)
    parser.add_argument("--year",type=int,choices=range(2,7),required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    render(args.subject,args.year,args.out)
