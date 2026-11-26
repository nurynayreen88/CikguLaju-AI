"""Private multi-subject RPT layout QA, using exact released five-column cells.

Preserve original PDF cover bytes visually; never replace production files.
Native Word reconstructs verified table cells, NOT PDF images of teaching pages.
No schedule/standard inference. Unsupported geometry, links or glyphs fail closed.
"""
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
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Cm
from scripts.build_web_rpt_weekly_suggestions import ROOT, SUBJECTS, read_weeks, WEEK, DATE, LESSON
from scripts.reschedule_web_rpt_teaching_weeks import pdf_rows
from web.rpt_native_word_cover import personalize_word

# The live route overrides English integrated, Maths Y4–6 and Sains Y5–6.
# Never use the superseded manifest files for those years. RTL subjects need
# separate Jawi/Arabic shaping and hyperlink-preserving QA.
SCOPE = {
    "bahasa_melayu": (2,3,4,5,6), "pendidikan_moral": (2,3,4,5,6),
    "pjpk": (2,3,4,5,6), "psv": (2,3,4,5,6), "muzik": (2,3,4,5,6),
    "rbt": (4,5,6), "sejarah": (4,5,6), "matematik": (2,3), "sains": (2,3,4),
}
BANDS = (35,140,320,445,655,818.89)
HEAD = ("MINGGU / TARIKH","UNIT / TAJUK / PDP","SK","SP","CATATAN / BAHAN")
def digest(raw): return sha256(raw).hexdigest()
def norm(s): return re.sub(r"\s+"," ",s).strip()
def mark(el, tag, **attrs):
    item=OxmlElement(tag)
    for key,val in attrs.items(): item.set(qn("w:"+key),str(val))
    el.append(item)
    return item

def spans(page, rect):
    return [s for b in page.get_text("dict",clip=rect)["blocks"] for l in b.get("lines",[])
            for s in l["spans"] if s["text"].strip()]
def cell_text(page, rect):
    value=page.get_text(clip=rect).strip()
    if "\ufffd" in value or any(0xe000<=ord(c)<=0xf8ff for c in value):
        raise ValueError("Unresolved source glyph")
    return value

def extract(source, slug):
    with fitz.open(source) as doc:
        if any(abs(p.rect.width-841.89)>2 or abs(p.rect.height-595.28)>2 for p in doc):
            raise ValueError("Non-standard A4 landscape source")
        if any(p.get_links() for p in list(doc)[1:]):
            raise ValueError("Source has links: need hyperlink-aware native Word reconstruction")
        dates, weeks = read_weeks(source,SUBJECTS[slug])
        identity_to_week={(comp,n):week for week,by in weeks.items() for comp,nums in by.items() for n in nums}
        rows=pdf_rows(doc,False)
        if len(rows)!=len(identity_to_week) or set(r[0] for r in rows)!=set(identity_to_week):
            raise ValueError("Weekly source identity mismatch")
        # The original source header is read from its actual geometry.
        headings=tuple(cell_text(doc[1],fitz.Rect(a,49,b,78.7)) for a,b in zip(BANDS,BANDS[1:]))
        if not all(headings):
            raise ValueError("Unrecognized original header")
        groups=[]
        seen=[]
        for page in list(doc)[1:]:
            week_cells={}
            for drawing in page.get_drawings():
                r=drawing["rect"]
                if drawing["type"] not in ("f","fs") or abs(r.x0-BANDS[0])>.15 or abs(r.width-105)>.15 or r.y0<78.6:
                    continue
                label=cell_text(page,r)
                w=WEEK.search(label)
                ds=DATE.findall(label)
                if not w or len(ds)!=4:
                    raise ValueError("Unrecognized source week label")
                week=int(w[1])
                key=(week,tuple(ds))
                if key in week_cells: raise ValueError("Duplicate week band on page")
                week_cells[key]=(r,label)
            for key,(r,label) in sorted(week_cells.items(),key=lambda kv:kv[1][0].y0):
                matching=[x for x in rows if x[1]==page.number and x[2].y0>=r.y0-.2 and x[2].y1<=r.y1+.2]
                cells=[]
                if not matching:
                    note=cell_text(page,fitz.Rect(BANDS[1],r.y0,BANDS[-1],r.y1))
                    if not note: raise ValueError("Unlabelled empty source week")
                    cells=[(None,(note,"","",""))]
                else:
                    for ident,_,clip in matching:
                        if identity_to_week[ident]!=key[0]: raise ValueError("Week allocation changed")
                        vals=tuple(cell_text(page,fitz.Rect(a,clip.y0,b,clip.y1)) for a,b in zip(BANDS[1:],BANDS[2:]))
                        joined=norm(" ".join(vals))
                        # Check source row content as a multiset of words; table
                        # extraction may interleave adjacent columns on a baseline.
                        if Counter(joined.split())!=Counter(norm(cell_text(page,clip)).split()):
                            raise ValueError("Source cell content not exactly recovered")
                        if not any(LESSON.fullmatch(s["text"].strip()) for s in spans(page,clip)):
                            raise ValueError("Source lesson marker missing")
                        cells.append((ident,vals));seen.append(ident)
                if groups and groups[-1][0]==key:
                    # Only merge consecutive identical week AND dates.
                    if norm(groups[-1][1])!=norm(label):
                        raise ValueError("Different week labels on continuation; require editorial review")
                    groups[-1][2].extend(cells)
                else:
                    groups.append((key,label,cells))
        if seen!=[r[0] for r in rows]: raise ValueError("Source row sequence changed")
        if len({g[0] for g in groups})!=len(groups): raise ValueError("Non-contiguous source week")
        return headings,groups

def fill(cell,value,*,bold=False,center=False,shade=None,size=8.4):
    cell.text=""
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER if center else WD_CELL_VERTICAL_ALIGNMENT.TOP
    for i,line in enumerate(value.splitlines() or [""]):
        p=cell.paragraphs[0] if i==0 else cell.add_paragraph()
        p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(1.3)
        p.paragraph_format.line_spacing=1.05
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
        run=p.add_run(line);run.font.name="Arial";run.font.size=Pt(size)
        run.bold=bold or bool(LESSON.fullmatch(line.strip()))
    if shade: mark(cell._tc.get_or_add_tcPr(),"w:shd",fill=shade)
def table(doc,widths):
    t=doc.add_table(rows=1,cols=len(widths))
    t.style="Table Grid";t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Pt(w)
    for c,w in zip(t.rows[0].cells,widths):c.width=Pt(w)
    return t
def add_row(t,widths):
    r=t.add_row();mark(r._tr.get_or_add_trPr(),"w:cantSplit")
    for c,w in zip(r.cells,widths):c.width=Pt(w)
    return r

def cover(doc,slug,year,source):
    # Native editable replica of the approved cover's three-field structure.
    # PDF uses the exact original first page. Word geometric/visual parity
    # must be reviewed separately; it is not declared identical yet.
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(25);p.paragraph_format.space_after=Pt(12)
    t=table(doc,(130,));r=t.rows[0];r.height=Pt(130)
    from docx.enum.table import WD_ROW_HEIGHT_RULE
    r.height_rule=WD_ROW_HEIGHT_RULE.EXACTLY
    fill(r.cells[0],"LOGO SEKOLAH",center=True,size=9)
    with fitz.open(source) as original:
        cover_lines=[line.strip() for line in original[0].get_text().splitlines() if line.strip()]
    title=next((line for line in cover_lines if "RANCANGAN PENGAJARAN TAHUNAN" in line),None)
    subtitle=next((line for line in cover_lines if re.search(r"TAHUN\\s+"+str(year)+r"\\b",line,re.I)),None)
    if not title or not subtitle: raise ValueError("Original cover title/subject not recovered")
    for line in (title,subtitle):
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(12)
        run=p.add_run(line);run.bold=True;run.font.size=Pt(20 if line.startswith("RANCANGAN") else 15)
    fields=table(doc,(170,490))
    row=fields.rows[0];row.height=Pt(56);row.height_rule=WD_ROW_HEIGHT_RULE.EXACTLY
    fill(row.cells[0],"NAMA SEKOLAH",bold=True,center=True,shade="F5F8F6")
    fill(row.cells[1],"__________________________________________",shade="F5F8F6",size=11)
    row=add_row(fields,(170,490));row.height=Pt(56);row.height_rule=WD_ROW_HEIGHT_RULE.EXACTLY
    fill(row.cells[0],"NAMA GURU",bold=True,center=True,shade="F5F8F6")
    fill(row.cells[1],"__________________________________________",shade="F5F8F6",size=11)
    doc.add_page_break()

def build(slug,year,out,manifest,layout):
    key=f"{slug}:{year}";entry=manifest["files"][key]
    source=ROOT/entry["path"];raw=source.read_bytes()
    if digest(raw)!=entry["sha256"] or layout["source_sha256_by_subject_year"][key]!=entry["sha256"]:
        raise ValueError("Original PDF or cover source mismatch")
    headings,groups=extract(source,slug)
    doc=Document();section=doc.sections[0]
    section.page_width=Pt(841.89);section.page_height=Pt(595.28)
    section.left_margin=Pt(35);section.right_margin=Pt(23)
    section.top_margin=Pt(36);section.bottom_margin=Pt(35)
    section.header_distance=Pt(15);section.footer_distance=Pt(16)
    section.different_first_page_header_footer=True
    section.header.paragraphs[0].text=f"RPT 2027 | {slug.replace('_',' ').upper()} | TAHUN {year}"
    section.footer.paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.RIGHT
    section.footer.paragraphs[0].add_run("Halaman ")
    mark(section.footer.paragraphs[0]._p,"w:fldSimple",instr="PAGE")
    doc.styles["Normal"].font.name="Arial";doc.styles["Normal"].font.size=Pt(8.4)
    cover(doc,slug,year,source)
    widths=tuple(b-a for a,b in zip(BANDS,BANDS[1:]))
    t=table(doc,widths)
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:tblHeader")
    mark(t.rows[0]._tr.get_or_add_trPr(),"w:cantSplit")
    for c,h in zip(t.rows[0].cells,headings):fill(c,h,bold=True,center=True,shade="FFF4BB",size=8.4)
    checks=[]
    for _,label,rows in groups:
        first=len(t.rows)
        for ident,values in rows:
            row=add_row(t,widths)
            if ident is None:
                fill(row.cells[1].merge(row.cells[4]),values[0])
            else:
                for cell,value in zip(row.cells[1:],values):fill(cell,value)
            checks.append((ident,values))
        cell=t.cell(first,0)
        if len(rows)>1:cell=cell.merge(t.cell(first+len(rows)-1,0))
        fill(cell,label,bold=True,center=True,shade="EAF1E3",size=8)
    folder=out/slug;folder.mkdir(parents=True,exist_ok=True)
    word=folder/f"tahun_{year}.docx";pdf=folder/f"tahun_{year}.pdf";doc.save(word)
    check=Document(word);assert len(check.tables)==3
    t=check.tables[2];assert len(t.rows)==len(checks)+1
    assert t.rows[0]._tr.get_or_add_trPr().find(qn("w:tblHeader")) is not None
    for row,(ident,values) in zip(t.rows[1:],checks):
        if ident is None: assert norm(row.cells[1].text)==norm(values[0])
        else: assert tuple(norm(c.text) for c in row.cells[1:])==tuple(norm(v) for v in values)
    # Synthetic profile verifies the three-field cover and untouched body.
    from PIL import Image
    img=BytesIO();Image.new("RGB",(80,100),"#336699").save(img,format="PNG")
    personalized=personalize_word(word.read_bytes(),{"school":"SEKOLAH CONTOH","teacher":"GURU CONTOH","logo":img.getvalue()})
    p=Document(BytesIO(personalized))
    assert p.tables[1].cell(0,1).text=="SEKOLAH CONTOH"
    assert p.tables[1].cell(1,1).text=="GURU CONTOH"
    assert p.tables[0].cell(0,0)._tc.xpath(".//w:drawing")
    assert p.tables[2]._tbl.xml==check.tables[2]._tbl.xml
    with tempfile.TemporaryDirectory() as tmp:
        temp=Path(tmp)
        subprocess.run(["libreoffice","-env:UserInstallation="+(temp/"lo").as_uri(),"--headless",
                        "--convert-to","pdf","--outdir",str(temp),str(word.resolve())],check=True,timeout=150)
        with fitz.open(temp/pdf.name) as converted,fitz.open(source) as original,fitz.open() as final:
            final.insert_pdf(original,from_page=0,to_page=0)
            final.insert_pdf(converted,from_page=1)
            final.save(pdf,garbage=4,deflate=True)
        with fitz.open(pdf) as final,fitz.open(source) as original:
            assert final[0].get_pixmap().samples==original[0].get_pixmap().samples
            for page in list(final)[1:]:
                text=norm(page.get_text())
                assert all(norm(h) in text for h in headings),(key,page.number+1,"missing repeated headers")
            # Compare all source body cell tokens with rendered body; headers,
            # cover and pagination may add tokens, but cannot erase lesson data.
            before=Counter(norm(" ".join(v for _,vals in checks for v in vals)).split())
            after=Counter(norm(" ".join(p.get_text() for p in list(final)[1:])).split())
            if before-after: raise ValueError("Word PDF lost source content tokens")
            pages=final.page_count
    return {"key":key,"pdp":sum(i is not None for i,_ in checks),"weeks":len(groups),"pages_before":entry["pages"],
            "pages_after":pages,"source_sha256":entry["sha256"],"word_sha256":digest(word.read_bytes()),
            "pdf_sha256":digest(pdf.read_bytes()),"profile_three_fields_test":True,
            "status":"QA_ONLY_NATIVE_WORD_COVER_VISUAL_REVIEW_REQUIRED"}

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--subject",required=True,choices=SCOPE)
    parser.add_argument("--out",required=True,type=Path);args=parser.parse_args()
    m=json.loads((ROOT/"manifest.json").read_text("utf8"))
    layout=json.loads((ROOT/"original_cover_layout_verified.json").read_text("utf8"))
    args.out.mkdir(parents=True,exist_ok=True)
    results=[]
    for year in SCOPE[args.subject]:
        try:results.append(build(args.subject,year,args.out,m,layout))
        except Exception as exc:
            results.append({"key":f"{args.subject}:{year}","status":"HOLD","reason":str(exc)[:250]})
    print(json.dumps(results,ensure_ascii=False,indent=2))
    (args.out/"report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2))
    if any(r["status"]=="HOLD" for r in results):raise SystemExit(1)

if __name__=="__main__":main()
