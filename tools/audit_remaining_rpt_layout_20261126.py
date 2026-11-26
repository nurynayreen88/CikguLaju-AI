"""Read-only layout audit of remaining released source files, no identity or Word uploads."""
import io,json,re
from pathlib import Path
import fitz
from docx import Document
from docx.oxml.ns import qn
from web.rpt_2027_all_http import ROOT,SCHOOL_RPTS
from web import rpt_2027_kssr_bm_word as bm
from web import kp2027_year1_rpt_combined as kp
from web.rpt_compact_pdf import RTL_PINS
def report_pdf(key,raw):
    with fitz.open(stream=raw,filetype="pdf") as d:
        rows=[]
        for p in list(d)[1:]:
            txt=p.get_text().strip()
            draws=p.get_drawings()
            rows.append({"page":p.number+1,"blank":not txt,"has_lines":any(x["type"] in ("s","fs") for x in draws),"width":round(p.rect.width,1),"height":round(p.rect.height,1)})
        print("PDF_AUDIT",json.dumps({"key":key,"pages":len(d),"blank_pages":[x["page"] for x in rows if x["blank"]],"cover_has_holiday":bool(re.search(r"Cuti Penggal|Cuti Sekolah|Main school breaks",d[0].get_text(),re.I)),"body_geometry":sorted(set((x["width"],x["height"]) for x in rows)),"pages_without_lines":[x["page"] for x in rows if not x["has_lines"]]},ensure_ascii=False),flush=True)
def report_word(key,raw):
    d=Document(io.BytesIO(raw))
    tables=[]
    for t in d.tables:
        if not t.rows:continue
        pr=t._tbl.tblPr
        width=pr.find(qn("w:tblW"))
        tables.append({"rows":len(t.rows),"columns":len(t.columns),"width_type":width.get(qn("w:type")) if width is not None else None,"autofit":t.autofit,"repeat":t.rows[0]._tr.get_or_add_trPr().find(qn("w:tblHeader")) is not None,"empty_rows":[i for i,row in enumerate(t.rows,1) if all(not c.text.strip() for c in row.cells)]})
    print("WORD_AUDIT",json.dumps({"key":key,"tables":tables},ensure_ascii=False),flush=True)
for y in bm.YEARS:
    source=bm.word_document(y,root=ROOT)
    if source:report_word(f"BM:{y}",source[0].read_bytes())
    else:print("UNAVAILABLE",f"BM:{y}:docx")
    report_pdf(f"BM:{y}",(ROOT/"compact_bm_pdf_2027"/"bahasa_melayu"/f"tahun_{y}.pdf").read_bytes())
for key in RTL_PINS:
    subject,y=key.split(":")
    report_pdf(key,(ROOT/"compact_rtl_pdf_2027"/subject/f"tahun_{y}.pdf").read_bytes())
for subject in kp.SUBJECTS:
    for fmt in kp.FORMATS:
        raw,_,_=kp.document(subject,fmt)
        (report_pdf if fmt=="pdf" else report_word)(f"KP2027:{subject}",raw)
for school,subjects in SCHOOL_RPTS.items():
    for slug,module in subjects.items():
        for y in module.YEARS:
            for fmt in module.FORMATS:
                path=module.document_path(y,fmt)
                key=f"{school}:{slug}:{y}"
                if path is None:print("UNAVAILABLE",key,fmt);continue
                (report_pdf if fmt=="pdf" else report_word)(key,path.read_bytes())
print("PPKI: backend-only, not audited by offline file checks; requires actual authorized download.")
