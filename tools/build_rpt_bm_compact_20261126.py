"""Private layout QA for 36 currently served KSSR RPT PDF sources.

Use the existing audited source row geometry, exact printed week allocation,
and checksum-locked cover, not guessed dates or generic PDF-to-Word conversion.
The 2026-style five columns are the previously audited PR #441 convention.
No academic promotion; no output or Word binary committed to public GitHub.
English integrated, Mathematics Y4–6, Science Y5–6 and RTL sources require
their own source adapters; never substitute an older staged PDF.
"""
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
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.opc.constants import RELATIONSHIP_TYPE as RT

from scripts.reschedule_web_rpt_teaching_weeks import pdf_rows
from scripts.build_web_rpt_weekly_suggestions import read_weeks, SUBJECTS
from web.rpt_native_word_cover import add_word_cover, cover_png

ROOT=Path("rpt_2027/web_2027_pdfs")
SCOPE={
    "bahasa_melayu":(2,3,4,5,6),
}
assert sum(map(len,SCOPE.values()))==5
HEADERS=("MINGGU / TARIKH","UNIT / TAJUK / PdP","SK","SP","CATATAN / BAHAN")
COLORS={"bahasa_melayu":"D9E9F3","pendidikan_moral":"E7E0F2",
        "pjpk":"DCECDC","psv":"F5E4D4","muzik":"E8DEF2","rbt":"F5E6D1",
        "sejarah":"E6E2D4","sains":"DCECDC","matematik":"D9E9F3"}
# Explicit table source bands used by the existing five-column reflow.
BANDS=(140.0,320.0,445.0,655.0,818.89)
WIDTHS=(3.15,6.25,4.30,7.60,6.10)
MARKER=re.compile(r"(?:(PJ|PK) )?(?:PdP|Lesson) (\d{3})")
DATE_RE=re.compile(r"\d{2}/\d{2}/2027")
WEEK_RE=re.compile(r"\bM(\d{2})\b")

def mark(el,tag,attrs=None):
    child=OxmlElement(tag)
    for key,val in (attrs or {}).items():child.set(qn(key),str(val))
    el.append(child)
    return child

def norm(v):
    return re.sub(r"\s+"," ",v).strip()

def extract_cells(page,rect):
    # Assign whole native text spans to source column bands. Refuse any
    # cross-column text instead of silently clipping it.
    lines=[line for block in page.get_text("dict",clip=rect)["blocks"]
           for line in block.get("lines",())]
    result=[[] for _ in range(4)]
    source=[]
    for line in lines:
        current=[[] for _ in range(4)]
        for span in line["spans"]:
            value=span["text"]
            if not value.strip():continue
            x0,y0,x1,y1=span["bbox"]
            idx=[i for i,(a,b) in enumerate(zip(BANDS,BANDS[1:]))
                 if a-1<=x0 and x1<=b+1]
            if len(idx)!=1:raise ValueError("Source span crosses a column boundary: "+value[:60])
            current[idx[0]].append(value)
            source.append(value)
        for i,parts in enumerate(current):
            if parts:result[i].append(" ".join(parts))
    if not result[0]:raise ValueError("Source RPT has no topic")
    if Counter(norm(" ".join(source)).split())!=Counter(norm(" ".join(x for c in result for x in c)).split()):
        raise ValueError("Source span preservation failed")
    if any("\ufffd" in x or any(0xe000<=ord(c)<=0xf8ff for c in x) for cell in result for x in cell):
        raise ValueError("Source contains unresolved glyph")
    return tuple(result)

def printed_closures(pdf):
    result={}
    for page in list(pdf)[1:]:
        for draw in page.get_drawings():
            r=draw["rect"]
            if draw["type"] not in ("f","fs") or abs(r.width-105)>.1 or abs(r.x0-35)>.1:
                continue
            label=page.get_text(clip=r)
            if "Cuti sekolah" not in label:continue
            m=WEEK_RE.search(label)
            dates=DATE_RE.findall(label)
            if not m or len(dates)!=4:raise ValueError("Unclear source closure")
            text=page.get_text(clip=fitz.Rect(140,r.y0,818.89,r.y1)).strip()
            if not text or MARKER.search(text):raise ValueError("Invalid source closure content")
            item=(tuple(dates),text)
            if int(m[1]) in result and result[int(m[1])]!=item:raise ValueError("Conflicting source closure")
            result[int(m[1])]=item
    return result

def extract(source,subject):
    dates,weeks=read_weeks(source,SUBJECTS[subject])
    assignments={(c,n):w for w,components in weeks.items() for c,ids in components.items() for n in ids}
    groups={}
    with fitz.open(source) as pdf:
        rows=pdf_rows(pdf,False)
        if len(rows)!=len(assignments) or set(i for i,_,_ in rows)!=set(assignments):
            raise ValueError("Source weekly IDs disagree with native PDF rows")
        seen=[]
        used_links=[]
        for identity,pageno,rect in rows:
            page=pdf[pageno]
            cells=extract_cells(page,rect)
            markers=[MARKER.fullmatch(x.strip()) for x in cells[0]]
            markers=[(m[1] or "",int(m[2])) for m in markers if m]
            if markers!=[identity]:raise ValueError("Source identity mismatch")
            links=[]
            for link in page.get_links():
                if rect.contains(link["from"]):
                    if link["kind"]!=fitz.LINK_URI:raise ValueError("Unknown source link type")
                    links.append(link["uri"])
            used_links.extend(links)
            week=assignments[identity]
            groups.setdefault(week,[]).append((identity,cells,links))
            seen.append(identity)
        if list(groups)!=sorted(groups):raise ValueError("Source chronological groups out of order")
        closures=printed_closures(pdf)
        if set(closures)&set(groups):raise ValueError("Source closure includes lessons")
        all_links=[l["uri"] for p in list(pdf)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI]
        if Counter(all_links)!=Counter(used_links):raise ValueError("Unassigned source hyperlinks")
    return dates,groups,closures,seen,used_links

def text_cell(cell,lines,*,bold=False,center=False,shade=None):
    cell.text=""
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if center else WD_CELL_VERTICAL_ALIGNMENT.TOP
    for i,line in enumerate(lines):
        p=cell.paragraphs[0] if i==0 else cell.add_paragraph()
        p.paragraph_format.space_before=Pt(0)
        p.paragraph_format.space_after=Pt(1)
        p.paragraph_format.line_spacing=1.05
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
        r=p.add_run(line);r.font.name="Arial";r.font.size=Pt(8.5)
        r.bold=bold or bool(MARKER.fullmatch(line.strip()))
    if shade:mark(cell._tc.get_or_add_tcPr(),"w:shd",{"w:fill":shade})

def hyperlink(cell,url):
    if not url.startswith(("https://","http://")):raise ValueError("Unapproved source URI")
    p=cell.add_paragraph()
    p.paragraph_format.space_after=Pt(1)
    rid=p.part.relate_to(url,RT.HYPERLINK,is_external=True)
    link=mark(p._p,"w:hyperlink",{"r:id":rid})
    run=mark(link,"w:r");props=mark(run,"w:rPr")
    mark(props,"w:color",{"w:val":"205A83"});mark(props,"w:u",{"w:val":"single"})
    mark(run,"w:t").text="Rujukan sumber"

def date_label(d):
    return date.fromisoformat(d).strftime("%d/%m/%Y")

def build_word(subject,year,manifest,lock,*,root=ROOT):
    key=f"{subject}:{year}"
    entry=manifest["files"][key];source=Path(root)/entry["path"];raw=source.read_bytes()
    if sha256(raw).hexdigest()!=entry["sha256"]:raise ValueError("Live RPT digest changed")
    dates,groups,closures,source_ids,links=extract(source,subject)
    doc=Document();section=doc.sections[0]
    section.page_width=Cm(29.7);section.page_height=Cm(21)
    section.left_margin=section.right_margin=Cm(1.15)
    section.top_margin=section.bottom_margin=Cm(1.1)
    section.header_distance=section.footer_distance=Cm(.45)
    normal=doc.styles["Normal"];normal.font.name="Arial";normal.font.size=Pt(8.5)
    section.header.paragraphs[0].text=f"RPT 2027 · {subject.replace('_',' ').upper()} · TAHUN {year}"
    section.footer.paragraphs[0].text="RPT 2027 · DRAF SEMAKAN · Kumpulan A dan B"
    add_word_cover(doc,cover_png(raw,lock,key))
    t=doc.add_table(rows=1,cols=5);t.style="Table Grid";t.autofit=False
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,(header,width) in enumerate(zip(HEADERS,WIDTHS,strict=True)):
        t.columns[i].width=Cm(width);t.rows[0].cells[i].width=Cm(width)
        text_cell(t.rows[0].cells[i],[header],bold=True,center=True,shade=COLORS[subject])
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    expected=[];ranges=[]
    def add_row():
        row=t.add_row()
        mark(row._tr.get_or_add_trPr(),"w:cantSplit")
        for c,w in zip(row.cells,WIDTHS,strict=True):c.width=Cm(w)
        return row
    for week in sorted(set(groups)|set(closures)):
        first=len(t.rows)
        if week in closures:
            d,body=closures[week]
            row=add_row();text_cell(row.cells[1].merge(row.cells[4]),[body])
        else:
            d=tuple(date_label(x) for x in dates[week])
            for identity,cells,urls in groups[week]:
                row=add_row()
                for cell,content in zip(row.cells[1:],cells,strict=True):text_cell(cell,content or [""])
                for url in urls:hyperlink(row.cells[4],url)
                expected.append((len(t.rows)-1,identity,cells))
        last=len(t.rows)-1
        merged=t.cell(first,0)
        if last>first:merged=merged.merge(t.cell(last,0))
        text_cell(merged,[f"{week:02d}","Kumpulan A",f"{d[0]} – {d[1]}","Kumpulan B",f"{d[2]} – {d[3]}"],
                  bold=True,center=True,shade="EAF1E3")
        ranges.append((first,last))
    stream=BytesIO();doc.save(stream)
    blob=stream.getvalue()
    check=Document(BytesIO(blob))
    assert len(check.tables)==1
    table=check.tables[0]
    assert table.rows[0]._tr.get_or_add_trPr().find(qn("w:tblHeader")) is not None
    for first,last in ranges:
        assert all(table.cell(first,0)._tc is table.cell(i,0)._tc for i in range(first,last+1))
    for i,identity,cells in expected:
        for cell,source_lines in zip(table.rows[i].cells[1:],cells,strict=True):
            assert all(line in cell.text for line in source_lines)
        assert table.rows[i]._tr.get_or_add_trPr().find(qn("w:cantSplit")) is not None
    assert [i for _,i,_ in expected]==source_ids
    assert Counter(rel.target_ref for rel in check.part.rels.values() if rel.reltype==RT.HYPERLINK)==Counter(set(links))
    return blob,raw,source,source_ids,links,ranges

def render(subject,year,out,manifest,lock):
    key=f"{subject}:{year}"
    entry=manifest["files"][key]
    blob,raw,source,source_ids,links,ranges=build_word(subject,year,manifest,lock)
    name=f"RPT_{subject}_tahun_{year}_2027"
    word=out/(name+".docx");word.write_bytes(blob)
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless",
                        "--convert-to","pdf","--outdir",str(folder),str(word.resolve())],check=True,timeout=150)
        target=out/(name+".pdf")
        with fitz.open(folder/(name+".pdf")) as generated, fitz.open(source) as original,fitz.open() as final:
            assert len(generated)>1
            final.insert_pdf(original,from_page=0,to_page=0)
            final.insert_pdf(generated,from_page=1)
            final.save(target,garbage=4,deflate=True)
        with fitz.open(target) as pdf,fitz.open(source) as original:
            assert pdf[0].get_pixmap().samples==original[0].get_pixmap().samples
            text="\n".join(p.get_text() for p in list(pdf)[1:])
            ids=[(m[1] or "",int(m[2])) for m in re.finditer(r"(?m)^(?:(PJ|PK) )?(?:PdP|Lesson) (\d{3})\s*$",text)]
            assert ids==source_ids,(key,"Rendered IDs differ",len(ids),len(source_ids))
            for p in list(pdf)[1:]:
                assert abs(p.rect.width-841.89)<2 and abs(p.rect.height-595.28)<2
                assert all(norm(h).casefold() in norm(p.get_text()).casefold() for h in HEADERS),(key,p.number,"Missing column headings")
            assert Counter(l["uri"] for p in list(pdf)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI)==Counter(links)
            pages=len(pdf)
    return {"key":key,"lessons":len(source_ids),"weeks":len(ranges),"pages_before":entry["pages"],"pages_after":pages,
            "source_sha256":entry["sha256"],"word_sha256":sha256(word.read_bytes()).hexdigest(),
            "pdf_sha256":sha256(target.read_bytes()).hexdigest(),"status":"PRIVATE_LAYOUT_QA_ONLY"}

def main():
    p=argparse.ArgumentParser();p.add_argument("--subject",choices=SCOPE,required=True)
    p.add_argument("--out",type=Path,required=True);args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/"manifest.json").read_text())
    lock=json.loads((ROOT/"original_cover_layout_verified.json").read_text())
    results=[];failed=[]
    for year in SCOPE[args.subject]:
        try:
            result=render(args.subject,year,args.out,manifest,lock)
            results.append(result);print(json.dumps(result),flush=True)
        except Exception as exc:
            failed.append({"subject":args.subject,"year":year,"error":str(exc)})
            print(json.dumps(failed[-1]),flush=True)
    print(json.dumps({"passed":results,"failed":failed}),flush=True)
    if failed:raise SystemExit(1)

if __name__=="__main__":main()
