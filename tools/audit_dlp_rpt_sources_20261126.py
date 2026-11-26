"""Read-only inventory of exact active DLP PDFs and matching native DOCX if available."""
import argparse,json,re
from pathlib import Path
from collections import Counter
from hashlib import sha256
import fitz
from docx import Document
from docx.oxml.ns import qn
from rpt_2027.dlp.documents import document_path,SUBJECTS
ROOT=Path("rpt_2027")
def audit(subject,year):
    key=f"{subject}:{year}"
    path=document_path(subject,year,root=ROOT/"dlp")
    assert path is not None,key
    digest=sha256(path.read_bytes()).hexdigest()
    lock=json.loads((ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
    candidates=[lock.get("dlp_year"+str(year),{}),lock.get("aligned_rpt_covers",{}).get(key,{}),lock.get("science_year6_covers",{}).get(key,{})]
    layout=next((x for x in candidates if x.get("source_sha256_by_subject_year",{}).get(key)==digest),None)
    assert layout is not None,(key,digest)
    with fitz.open(path) as pdf:
        assert abs(pdf[0].rect.width-layout["page_width"])<=layout["tolerance_pt"]
        assert abs(pdf[0].rect.height-layout["page_height"])<=layout["tolerance_pt"]
        body=[p.get_text() for p in list(pdf)[1:]]
        assert body and all(t.strip() for t in body)
        for p in pdf:
            assert p.get_pixmap(matrix=fitz.Matrix(.4,.4),alpha=False).width>0
        page=pdf[1]
        spans=[{"text":s["text"],"bbox":[round(v,1) for v in s["bbox"]],"origin":[round(v,1) for v in s["origin"]]}
               for b in page.get_text("dict")["blocks"] for line in b.get("lines",[]) for s in line["spans"]]
        draws=[{"rect":[round(v,1) for v in d["rect"]],"fill":d.get("fill"),"type":d["type"]}
               for d in page.get_drawings()]
        result={"key":key,"pdf":path.name,"sha256":digest,"pages":len(pdf),"cover_verified":True,
                "first_body_spans":spans[:120],"first_body_draws":draws[:80],
                "page_sizes":sorted({(round(p.rect.width,1),round(p.rect.height,1)) for p in pdf}),
                "source_replacement_chars":sum(t.count("\ufffd") for t in body)}
    word=document_path(subject,year,"docx",root=ROOT/"dlp")
    result["existing_word"]=None
    if word:
        d=Document(word)
        result["existing_word"]={"file":word.name,"sha256":sha256(word.read_bytes()).hexdigest(),
          "tables":[{"rows":len(t.rows),"cols":len(t.columns),"headers":[c.text for c in t.rows[0].cells],
          "repeated_headers":sum(row._tr.get_or_add_trPr().find(qn("w:tblHeader")) is not None for row in t.rows),
          "merged_week_cells":len(t._tbl.xpath(".//w:vMerge"))} for t in d.tables[:6]]}
    print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--subject",choices=SUBJECTS,required=True);p.add_argument("--year",type=int,choices=range(2,7),required=True);a=p.parse_args();audit(a.subject,a.year)
