"""Private RTL RPT layout candidate; exact staged source, no academic promotion."""
from collections import Counter
from copy import deepcopy
from math import ceil
from docx.text.paragraph import Paragraph
from docx.table import _Cell
from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import argparse
import json
import re
import subprocess
import tempfile
import unicodedata
import fitz
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from scripts.build_web_rpt_weekly_suggestions import read_weeks,SUBJECTS
from scripts.reschedule_web_rpt_teaching_weeks import pdf_rows,TOP
from tools.build_kssr_rpt_merged_week_batch_20261126 import mark,norm,text_cell,hyperlink,MARKER
from web.rpt_native_word_cover import add_word_cover,cover_png

ROOT=Path("rpt_2027/web_2027_pdfs")
BANDS=(35,198.89,408.89,533.89,713.89,818.89)
WIDTHS=(3.15,6.25,4.30,7.60,6.10)
HEADERS={
    "pendidikan_islam":("ميڠݢو / تاريخ","بيدڠ / تاجوق / ڤدڤ","ستندرد كاندوڠن","ستندرد ڤمبالجرن","چاتتن / باهن"),
    "bahasa_arab":("الأسبوع / التاريخ","الوحدة / الموضوع / الدرس","معيار المحتوى","معيار التعلم","الملاحظات / الوسائل"),
}
RTL=re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
BAD=re.compile(r"[\ufffd\ue000-\uf8ff]")
PRESENTATION=re.compile(r"[\ufb50-\ufdff\ufe70-\ufefc]")
DATE=re.compile(r"\d{2}/\d{2}/2027")
WEEK=re.compile(r"\bM(\d{2})\b")

def logical_glyphs(text):
    # Only Unicode-defined Arabic compatibility decompositions. Never guess
    # spelling or reverse visual strings. Manual logical-order QA remains required.
    if BAD.search(text):raise ValueError("Unresolved source glyph")
    result=PRESENTATION.sub(lambda m:unicodedata.normalize("NFKC",m.group()),text)
    if BAD.search(result) or PRESENTATION.search(result):raise ValueError("No safe Unicode decomposition")
    return result


# A PDF from ReportLab contains already shaped visual Arabic. PyMuPDF's
# extracted reading order may reverse digits inside those native spans.
# Restore only numeric atoms using the original physical glyph positions;
# never infer the Arabic spelling or reverse the entire sentence.
NUMBER_ATOM=re.compile(r"[0-9\u0660-\u0669\u06f0-\u06f9]+(?:[./–-][0-9\u0660-\u0669\u06f0-\u06f9]+)*")
def numeric_text(glyphs):
    source="".join(g["c"] for g in glyphs)
    # A multi-codepoint ligature may not have one coordinate per char.
    # Do not assign guessed positions; map each source char to its glyph.
    positions=[g for g in glyphs for _ in g["c"]]
    def physical(match):
        entries=list(zip(match.group(),positions[match.start():match.end()]))
        if len(entries)<2:return match.group()
        x=lambda pair:(pair[1]["bbox"][0]+pair[1]["bbox"][2])/2
        ordered="".join(c for c,g in sorted(entries,key=x))
        assert Counter(ordered)==Counter(match.group())
        return ordered
    return logical_glyphs(NUMBER_ATOM.sub(physical,source))

def numeric_atoms_by_geometry(page,clip):
    values=[]
    for b in page.get_text("rawdict",clip=clip)["blocks"]:
        for line in b.get("lines",()):
            for span in line["spans"]:
                value=numeric_text(span["chars"])
                values.extend(m.group() for m in NUMBER_ATOM.finditer(value))
    return values

def clip_cells(page,rect):
    # A glyph's bounding box can touch the neighboring cell even when the
    # native line belongs to one column. Read the whole row once, preserving
    # the exact text order within each native span and assigning by geometry.
    columns=[[] for _ in range(4)]
    original=[]
    for block in page.get_text("rawdict",clip=rect)["blocks"]:
        for line in block.get("lines",()):
            parts=[[] for _ in range(4)]
            for span in line["spans"]:
                value=numeric_text(span["chars"])
                if not value.strip():continue
                x0,_,x1,_=span["bbox"]
                overlaps=[max(0,min(x1,b)-max(x0,a)) for a,b in zip(BANDS[:4],BANDS[1:5])]
                i=max(range(4),key=lambda j:overlaps[j])
                if overlaps[i]<=0 or max(0,x1-x0)-overlaps[i]>2.5:
                    # PyMuPDF sometimes joins disjoint native spans across
                    # columns. Recover the original cell strings from the
                    # entire source row using raw glyph coordinates, below.
                    return clip_cells_glyphwise(page,rect)
                original.append(value)
                parts[i].append(value)
            for i,values in enumerate(parts):
                if values:columns[i].append(" ".join(values))
    physical=["\n".join(lines).strip() for lines in columns]
    letters=lambda v:Counter(c for c in v if not c.isspace())
    if letters("".join(original))!=letters("".join(physical)):
        raise ValueError("Source RTL character loss")
    return tuple(reversed(physical))


def clip_cells_glyphwise(page,rect):
    columns=[[] for _ in range(4)]
    original=[]
    for block in page.get_text("rawdict",clip=rect)["blocks"]:
        for line in block.get("lines",()):
            parts=[[] for _ in range(4)]
            for span in line["spans"]:
                for glyph in span["chars"]:
                    value=logical_glyphs(glyph["c"])
                    if not value.strip():
                        continue
                    x0,_,x1,_=glyph["bbox"]
                    x=(x0+x1)/2
                    matching=[i for i,(a,b) in enumerate(zip(BANDS[:4],BANDS[1:5])) if a<=x<b]
                    if len(matching)!=1:
                        raise ValueError(f"Ambiguous RTL glyph at page {page.number+1}")
                    original.append(value)
                    parts[matching[0]].append(glyph)
            for i,items in enumerate(parts):
                if not items:continue
                out=[]
                sequence=[]
                previous=None
                for glyph in items:
                    x0,_,x1,_=glyph["bbox"]
                    if previous is not None:
                        p0,p1=previous
                        if max(x0-p1,p0-x1)>2:
                            sequence.append({"c":" ","bbox":[p0,0,p1,0]})
                    sequence.append(glyph)
                    previous=(x0,x1)
                columns[i].append(numeric_text(sequence))
    physical=["\n".join(lines).strip() for lines in columns]
    letters=lambda v:Counter(c for c in v if not c.isspace())
    assert letters("".join(original))==letters("".join(physical))
    # Do not auto-publish glyphwise candidates: original logical order
    # and word spacing must still be checked visually by a reviewer.
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
        if not RTL.search(p.text):
            if not center:p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
            continue
        if not center:p.alignment=WD_ALIGN_PARAGRAPH.LEFT
        # OOXML pPr order matters: bidi must precede spacing and jc.
        ppr=p._p.get_or_add_pPr()
        bidi=OxmlElement("w:bidi");bidi.set(qn("w:val"),"1")
        ppr.insert_element_before(bidi,"w:adjustRightInd","w:snapToGrid","w:spacing","w:ind","w:contextualSpacing","w:mirrorIndents","w:suppressOverlap","w:jc","w:textDirection","w:textAlignment","w:rPr","w:sectPr","w:pPrChange")
        raw=p.text
        # Rebuild the runs, leaving numeric tokens explicitly LTR and the
        # Arabic/Jawi script in a native complex-script run.
        for child in list(p._p):
            if child.tag==qn("w:r"):p._p.remove(child)
        def add(value,number=False):
            if not value:return
            run=p.add_run(value)
            run.bold=bold
            run.font.name="Amiri"
            run.font.size=Pt(9.5)
            props=run._r.get_or_add_rPr()
            fonts=props.find(qn("w:rFonts"))
            if fonts is not None:fonts.set(qn("w:cs"),"Amiri")
            mark(props,"w:szCs",{"w:val":"19"})
            mark(props,"w:rtl",{"w:val":"0" if number else "1"})
            mark(props,"w:lang",{"w:bidi":"ar-SA"})
        at=0
        for m in NUMBER_ATOM.finditer(raw):
            add(raw[at:m.start()])
            add("\u200e"+m.group()+"\u200e",True)
            at=m.end()
        add(raw[at:])

def paginate_rtl(doc,table,ranges):
    # Conservative physical blocks; preserve the source cells and the RTL runs.
    # Leave white space rather than force a full-height table.
    widths=[c.width.pt for c in table.columns]
    def cell_height(cell,width):
        return 8+sum(13*max(1,sum(max(1,ceil(len(line)*5.3/max(20,width-14))) for line in p.text.splitlines() or [""])) for p in cell.paragraphs)
    def row_height(i):
        offset=0;heights=[]
        for tc in table.rows[i]._tr.tc_lst:
            span=tc.grid_span
            if offset:
                heights.append(cell_height(_Cell(tc,table),sum(widths[offset:offset+span])))
            offset+=span
        return max(heights+[24])
    header=max(cell_height(c,w) for c,w in zip(table.rows[0].cells,widths))
    budget=405
    blocks=[]
    for a,b in ranges:
        label=cell_height(table.cell(a,0),widths[0])
        part=[];h=0
        for i in range(a,b+1):
            rh=row_height(i)
            if part and (header+max(label,h+rh)>budget or len(part)>=5):
                blocks.append((a,part,max(label,h)));part=[];h=0
            part.append(i);h+=rh
        if part:blocks.append((a,part,max(label,h)))
    pages=[];current=[];total=header
    for a,rows,h in blocks:
        if current and (total+h>budget or sum(len(r) for _,r in current)+len(rows)>5):
            pages.append(current);current=[];total=header
        current.append((a,rows));total+=h
    if current:pages.append(current)
    before=[tuple(c.text for c in r.cells) for r in table.rows[1:]]
    anchor=table._tbl
    for n,blocks in enumerate(pages):
        if n:
            el=OxmlElement("w:p");anchor.addprevious(el)
            pf=Paragraph(el,doc).paragraph_format
            pf.keep_with_next=False;pf.keep_together=False
            pf.space_before=Pt(0);pf.space_after=Pt(0);pf.line_spacing=Pt(1)
            sec=deepcopy(doc.element.body.sectPr)
            for child in list(sec):
                if child.tag in (qn("w:headerReference"),qn("w:footerReference"),qn("w:pgNumType")):sec.remove(child)
            typ=sec.find(qn("w:type"))
            if typ is None:
                typ=OxmlElement("w:type");sec.insert_element_before(typ,"w:pgSz","w:pgMar","w:cols","w:docGrid")
            typ.set(qn("w:val"),"nextPage")
            el.get_or_add_pPr().append(sec)
        clone=deepcopy(anchor)
        for tr in list(clone.tr_lst)[1:]:clone.remove(tr)
        for a,indices in blocks:
            for k,i in enumerate(indices):
                row=deepcopy(table.rows[i]._tr)
                if k==0 and i!=a:
                    row.replace(row.tc_lst[0],deepcopy(table.rows[a]._tr.tc_lst[0]))
                clone.append(row)
        for j,tr in enumerate(clone.tr_lst):
            for el in tr.xpath(".//w:p"):
                pf=Paragraph(el,doc).paragraph_format
                pf.keep_with_next=j<len(clone.tr_lst)-1
                pf.keep_together=True;pf.widow_control=False
        anchor.addprevious(clone)
    anchor.getparent().remove(anchor)
    for section in doc.sections:section.top_margin=section.bottom_margin=Cm(1.5)
    assert [tuple(c.text for c in r.cells) for t in doc.tables for r in t.rows[1:]]==before
    assert all(t._tbl.tblPr.find(qn("w:bidiVisual")) is not None for t in doc.tables)

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
    section.footer.paragraphs[0].text="RPT 2027 · Kumpulan A dan B"
    add_word_cover(doc,cover_png(raw,lock,key))
    table=doc.add_table(rows=1,cols=5);table.style="Table Grid";table.autofit=False
    table.alignment=WD_TABLE_ALIGNMENT.CENTER
    mark(table._tbl.tblPr,"w:bidiVisual",{"w:val":"1"})
    color="ECE4F6" if subject=="pendidikan_islam" else "E7EEDB"
    for i,(header,width) in enumerate(zip(HEADERS[subject],WIDTHS)):
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
        assert all(norm(val) in norm(cell.text.replace("\u200e","")) for cell,val in zip(t.rows[i].cells[1:],cells))
    assert [i for _,i,_ in expected]==ids
    for first,last in ranges:
        assert all(t.cell(first,0)._tc is t.cell(i,0)._tc for i in range(first,last+1))
    assert Counter(rel.target_ref for rel in check.part.rels.values() if rel.reltype==RT.HYPERLINK)==Counter(set(links))
    paginate_rtl(doc,table,ranges)
    stream=BytesIO();doc.save(stream);blob=stream.getvalue()
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
            assert len(pdf)==len(Document(BytesIO(blob)).tables)+1,(subject,year,"spill page")
            assert all(d["rect"].y1<=p.rect.height-39 for p in list(pdf)[1:] for d in p.get_drawings()),(subject,year,"bottom clearance")
            text="\n".join(p.get_text() for p in list(pdf)[1:])
            found=[(m[1] or "",int(m[2])) for m in re.finditer(r"(?m)^(?:(PJ|PK) )?(?:PdP|Lesson) (\d{3})\s*$",text)]
            assert found==ids
            for p in list(pdf)[1:]:
                assert abs(p.rect.width-841.89)<2 and abs(p.rect.height-595.28)<2
                assert all(norm(h) in norm(unicodedata.normalize('NFKC',p.get_text())) for h in HEADERS[subject])
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
