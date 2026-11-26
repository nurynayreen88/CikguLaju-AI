"""Generate and validate all compact DLP releases without changing the schedule."""
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import json,subprocess,fitz,re
from tools.build_rpt_dlp_full_standards_20261126 import build_word,render
from tools.build_rpt_dlp_native_20261126 import ROOT,PINS
from tools.rpt_dlp_compact_pagination_20261126 import measure_weeks,choose_sizes

def verify_bottom(p,key):
    # LibreOffice may emit a single long stroke OR separate contiguous strokes
    # (for example where cell-edge weights differ). Measure the actual six
    # columns, then require their complete bottom edge, not one PDF path.
    drawings=p.get_drawings()
    columns={}
    for d in drawings:
        r=d["rect"]
        if d["type"]=="f" and r.width>30 and r.height>10:
            k=(round(r.x0,1),round(r.x1,1))
            columns[k]=max(columns.get(k,0),r.y1)
    assert len(columns)==6,(key,p.number,"six physical columns",columns)
    bottom=max(columns.values())
    assert bottom-min(columns.values())<1.5,(key,p.number,"uneven cell bottoms",columns)
    left=min(k[0] for k in columns);right=max(k[1] for k in columns)
    # Compare all grid drawings against the cell baseline, including the
    # first-column vertical borders. Tolerance includes stroke thickness.
    assert max(d["rect"].y1 for d in drawings)<=bottom+1.5,(key,p.number,"overhanging grid",bottom,max(d["rect"].y1 for d in drawings))
    intervals=sorted((d["rect"].x0,d["rect"].x1) for d in drawings
        if d["type"]=="s" and d["rect"].height<1.5 and abs(d["rect"].y1-bottom)<1.5 and d["rect"].width>1)
    cursor=left
    for a,b in intervals:
        if a<=cursor+1.5:cursor=max(cursor,b)
    assert cursor>=right-1.5,(key,p.number,"incomplete bottom edge",intervals,left,right)
    print("DLP_BOTTOM_OK",key,p.number,round(bottom,2),flush=True)

def main():
    base=ROOT/"full_standards_dlp_pdf_2027"
    mp=base/"manifest.json"
    cp=ROOT/"web_2027_pdfs/original_cover_layout_verified.json"
    manifest=json.loads(mp.read_text());cover=json.loads(cp.read_text())
    assert manifest["schedule"]=="whole_lesson_20261126"
    plans={};entries={};outputs={}
    with TemporaryDirectory() as tmp:
        folder=Path(tmp)
        for key,pin in PINS.items():
            subject,y=key.split(":");year=int(y)
            sizes=manifest["page_groups"][key]
            assert sum(sizes)==35
            render(subject,year,folder,whole_weeks=True,compact_sizes=sizes)
            raw=(folder/f"RPT_{subject}_Year_{year}_2027.pdf").read_bytes()
            rel=f"{subject}/tahun_{year}.pdf"
            with fitz.open(stream=raw,filetype="pdf") as doc,fitz.open(base/rel) as previous:
                assert doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples==previous[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples,key
                assert len(doc)==len(previous),(key,len(doc),len(previous))
                for p,count in zip(list(doc)[1:-1],sizes,strict=True):
                    verify_bottom(p,key)
                    assert len(re.findall(r"(?m)^Week\s+\d{2}\s*$",p.get_text()))==count,(key,p.number,count)
                entries[key]={"path":rel,"source_sha256":pin,"sha256":sha256(raw).hexdigest(),"bytes":len(raw),"pages":len(doc)}
                print("WEEK_COLUMN_FIXED",key,"old",len(previous),"new",len(doc),"weeks",sizes,flush=True)
            plans[key]=sizes;outputs[rel]=raw
    assert set(plans)==set(PINS)
    manifest.update(files=entries,page_groups=plans)
    cover["full_standards_dlp_pdf_covers"]["source_sha256_by_subject_year"]={k:v["sha256"] for k,v in entries.items()}
    for rel,raw in outputs.items():(base/rel).write_bytes(raw)
    mp.write_text(json.dumps(manifest,indent=2)+"\n")
    cp.write_text(json.dumps(cover,indent=2,ensure_ascii=False)+"\n")
    from web.rpt_compact_pdf import dlp_whole_week_release
    assert dlp_whole_week_release(ROOT)
if __name__=="__main__":main()
