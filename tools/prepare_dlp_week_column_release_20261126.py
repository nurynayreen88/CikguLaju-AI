"""Generate and validate all compact DLP releases without changing the schedule."""
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import json,subprocess,fitz,re
from tools.build_rpt_dlp_full_standards_20261126 import build_word,render
from tools.build_rpt_dlp_native_20261126 import ROOT,PINS
from tools.rpt_dlp_compact_pagination_20261126 import measure_weeks,choose_sizes

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
                    # Every table bottom must be a full-width stroke, with
                    # no filled first-column cell or border below that stroke.
                    drawings=p.get_drawings()
                    full=[d["rect"] for d in drawings if d["type"]=="s" and d["rect"].height<1 and d["rect"].width>p.rect.width*.85]
                    assert full,(key,p.number,"missing bottom edge")
                    bottom=max(r.y1 for r in full)
                    assert max(d["rect"].y1 for d in drawings)<=bottom+1.5,(key,p.number,"overhanging grid")
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
