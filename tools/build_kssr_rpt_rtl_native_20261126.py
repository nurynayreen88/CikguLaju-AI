"""Candidate native RTL Word RPT from exact published source rows; offline QA only."""
from collections import Counter
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import argparse,json,re,subprocess,tempfile,unicodedata
import fitz
from docx import Document
from docx.shared import Cm,Pt
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from tools.build_kssr_rpt_merged_week_batch_20261126 import mark,hyperlink,date_label,norm,HEADERS,WIDTHS
from scripts.reschedule_web_rpt_teaching_weeks import pdf_rows
from scripts.build_web_rpt_weekly_suggestions import read_weeks,SUBJECTS
from tools.rpt_source_table_polish import fixed_grid
from tools.rpt_kssr_physical_pages import paginate
from web.rpt_native_word_cover import add_word_cover,cover_png
from web.rpt_compact_pdf import RTL_PINS
ROOT=Path("rpt_2027/web_2027_pdfs")
# Mirror the audited five-column physical geometry (35..818.89).
BANDS=(35,198.89,408.89,533.89,713.89)
WEEK=re.compile(r"\bM(\d{2})\b")
DATE=re.compile(r"\d{2}/\d{2}/2027")
LESSON=re.compile(r"PdP (\d{3})")
RTL=re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]")
def logical(s):
    # Only compatibility glyphs in Arabic presentation blocks; no change to numbers/words.
    return "".join(unicodedata.normalize("NFKC",c) if 0xfb50<=ord(c)<=0xfdff or 0xfe70<=ord(c)<=0xfefc else c for c in s)
def cells(page,rect):
    out=[[] for _ in range(4)]
    source=[]
    for block in page.get_text("rawdict",clip=rect)["blocks"]:
        for line in block.get("lines",()):
            buckets=[[] for _ in out]
            for s in line["spans"]:
                for ch in s["chars"]:
                    v=ch["c"]
                    if "\ufffd" in v or any(0xe000<=ord(c)<=0xf8ff for c in v):raise ValueError("unresolved source glyph")
                    x0,_,x1,_=ch["bbox"]
                    mid=(x0+x1)/2
                    ix=[i for i,(a,b) in enumerate(zip(BANDS,BANDS[1:])) if a<=mid<b]
                    if not ix:
                        if not v.strip():continue
                        raise ValueError(("unassigned source character",page.number,v,ch["bbox"]))
                    # A PDF span can contain several independent cells; a glyph
                    # itself must not substantially straddle a physical rule.
                    a,b=BANDS[ix[0]:ix[0]+2]
                    if v.strip() and (x0<a-2 or x1>b+2):
                        raise ValueError(("cross-column glyph",page.number,v,ch["bbox"]))
                    buckets[3-ix[0]].append(logical(v));source.append(logical(v))
            for i,parts in enumerate(buckets):
                if parts and "".join(parts).strip():out[i].append("".join(parts).strip())
    # Compare all non-space glyphs; geometry may introduce a synthetic gap
    # between independent spans, but no original glyph may be discarded.
    glyphs=lambda s:Counter(c for c in s if not c.isspace())
    assert glyphs("".join(source))==glyphs("".join(x for cell in out for x in cell))
    assert all(out),("empty source cell",page.number,rect)
    return out
def set_cell(cell,lines,*,center=False,bold=False,shade=None):
    cell.text=""
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if center else WD_CELL_VERTICAL_ALIGNMENT.TOP
    for i,line in enumerate(lines):
        p=cell.paragraphs[0] if i==0 else cell.add_paragraph()
        p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(1)
        p.paragraph_format.line_spacing=1.05
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.RIGHT
        arab=bool(RTL.search(line))
        if arab:mark(p._p.get_or_add_pPr(),"w:bidi")
        r=p.add_run(line);r.font.name="Amiri" if arab else "Arial";r.font.size=Pt(9)
        r.bold=bold or bool(LESSON.fullmatch(line.strip()))
        if arab:
            props=r._r.get_or_add_rPr()
            props.rFonts.set(qn("w:cs"),"Amiri")
            mark(props,"w:rtl");mark(props,"w:szCs",{"w:val":18})
    if shade:mark(cell._tc.get_or_add_tcPr(),"w:shd",{"w:fill":shade})
def build_word(subject,year,*,root=ROOT):
    key=f"{subject}:{year}";root=Path(root)
    manifest=json.loads((root/"manifest.json").read_text())
    lock=json.loads((root/"original_cover_layout_verified.json").read_text())
    entry=manifest["files"][key];source=root/entry["path"];raw=source.read_bytes()
    assert sha256(raw).hexdigest()==entry["sha256"]==RTL_PINS[key]
    dates,weeks=read_weeks(source,SUBJECTS[subject])
    assigned={(c,n):w for w,parts in weeks.items() for c,ids in parts.items() for n in ids}
    groups={};closed={};expected=[];links=[]
    with fitz.open(source) as pdf:
        rows=pdf_rows(pdf,True)
        assert len(rows)==len(assigned) and set(i for i,_,_ in rows)==set(assigned)
        for identity,pageno,rect in rows:
            page=pdf[pageno];contents=cells(page,rect)
            assert [int(m[1]) for l in contents[0] if (m:=LESSON.fullmatch(l.strip()))]==[identity[1]]
            urls=[l["uri"] for l in page.get_links() if rect.contains(l["from"]) and l["kind"]==fitz.LINK_URI]
            groups.setdefault(assigned[identity],[]).append((identity,contents,urls));links.extend(urls)
        assert Counter(links)==Counter(l["uri"] for p in list(pdf)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI)
        for page in list(pdf)[1:]:
            for drawing in page.get_drawings():
                r=drawing["rect"]
                if drawing["type"] not in ("f","fs") or abs(r.width-105)>.1 or abs(r.x1-(page.rect.width-23))>.1:continue
                label=page.get_text(clip=r)
                if "Cuti sekolah" not in label and "School closed" not in label:continue
                w=WEEK.search(label);d=DATE.findall(label)
                assert w and len(d)==4
                body=page.get_text(clip=fitz.Rect(35,r.y0,r.x0,r.y1)).strip()
                assert body and not LESSON.search(body)
                closed[int(w[1])]=(d,body)
    assert not set(groups)&set(closed)
    doc=Document();sec=doc.sections[0]
    sec.page_width=Cm(29.7);sec.page_height=Cm(21)
    sec.left_margin=sec.right_margin=Cm(1.15);sec.top_margin=sec.bottom_margin=Cm(1.1)
    sec.header_distance=sec.footer_distance=Cm(.45)
    doc.styles["Normal"].font.name="Amiri";doc.styles["Normal"].font.size=Pt(9)
    sec.footer.paragraphs[0].text="RPT 2027 · DRAF SEMAKAN · Kumpulan A dan B"
    add_word_cover(doc,cover_png(raw,lock,key))
    t=doc.add_table(rows=1,cols=5);t.style="Table Grid";t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    shade="E0EEE4" if subject=="pendidikan_islam" else "E7E0F2"
    for i,(label,w) in enumerate(zip(HEADERS,WIDTHS)):
        t.columns[i].width=Cm(w);t.rows[0].cells[i].width=Cm(w)
        set_cell(t.rows[0].cells[i],[label],center=True,bold=True,shade=shade)
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    def row():
        r=t.add_row();mark(r._tr.get_or_add_trPr(),"w:cantSplit")
        for cell,w in zip(r.cells,WIDTHS):cell.width=Cm(w)
        return r
    for week in sorted(set(groups)|set(closed)):
        first=len(t.rows)
        if week in closed:
            d,body=closed[week];r=row();set_cell(r.cells[1].merge(r.cells[4]),[body])
        else:
            d=tuple(date_label(v) for v in dates[week])
            for identity,content,urls in groups[week]:
                r=row()
                for cell,lines in zip(r.cells[1:],content):set_cell(cell,lines)
                for url in urls:hyperlink(r.cells[4],url)
                expected.append((len(t.rows)-1,identity,content))
        last=len(t.rows)-1
        cell=t.cell(first,0)
        if last>first:cell=cell.merge(t.cell(last,0))
        set_cell(cell,[f"{week:02d}","Kumpulan A",f"{d[0]} – {d[1]}","Kumpulan B",f"{d[2]} – {d[3]}"],center=True,bold=True,shade="EAF1E3")
    fixed_grid(t,shade)
    mark(t._tbl.tblPr,"w:bidiVisual")
    for index,identity,content in expected:
        for cell,lines in zip(t.rows[index].cells[1:],content):
            assert norm(" ".join(p.text for p in cell.paragraphs if not p._p.xpath(".//w:hyperlink")))==norm(" ".join(lines))
    out=BytesIO();doc.save(out)
    # Conservative candidate pagination, verified by actual LO rendering.
    blob=paginate(out.getvalue(),budget=350)
    return blob,raw,source,[i[1] for i in expected],links
def render(subject,year,out):
    key=f"{subject}:{year}";blob,raw,source,ids,links=build_word(subject,year)
    name=f"RPT_{subject}_{year}_2027";word=out/(name+".docx");word.write_bytes(blob)
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",str(folder),str(word.resolve())],check=True,timeout=240)
        target=out/(name+".pdf")
        with fitz.open(folder/(name+".pdf")) as generated,fitz.open(source) as original,fitz.open() as final:
            final.insert_pdf(original,from_page=0,to_page=0);final.insert_pdf(generated,from_page=1)
            final.save(target,garbage=4,deflate=True)
        with fitz.open(target) as pdf,fitz.open(source) as original:
            doc=Document(BytesIO(blob))
            assert pdf[0].get_pixmap().samples==original[0].get_pixmap().samples
            assert len(pdf)==len(doc.tables)+1,("spill",len(pdf),len(doc.tables))
            actual=[]
            for p in list(pdf)[1:]:
                txt=p.get_text()
                assert all(norm(h).casefold() in norm(txt).casefold() for h in HEADERS),("header",p.number)
                assert all(d["rect"].y1<=p.rect.height-39 for d in p.get_drawings()),("bottom",p.number)
                actual.extend(int(m[1]) for m in re.finditer(r"(?m)^PdP (\d{3})\s*$",txt))
            assert actual==[i[1] for i in ids],("PdP parity",len(actual),len(ids))
            assert Counter(l["uri"] for p in list(pdf)[1:] for l in p.get_links() if l["kind"]==fitz.LINK_URI)==Counter(links)
            print(json.dumps({"key":key,"pdps":len(ids),"pages":len(pdf),"status":"TECHNICAL_CANDIDATE_VISUAL_REVIEW_REQUIRED"}),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--subject",required=True,choices=("pendidikan_islam","bahasa_arab"));p.add_argument("--year",required=True,type=int);p.add_argument("--out",required=True,type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);render(a.subject,a.year,a.out)
