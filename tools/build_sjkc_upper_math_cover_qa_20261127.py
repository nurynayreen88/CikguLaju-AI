"""Read-only SJKC Year 3 cover reference; generate candidate cover variants only.
No production paths, downloads, profile calls or existing RPT writes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import fitz

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"rpt_2027/sjkc/matematik/RPT_2027_Matematik_SJKC_Tahun_3.pdf"
LOCK=ROOT/"rpt_2027/web_2027_pdfs/original_cover_layout_verified.json"
KEY="matematik_sjkc:3"

def digest(data): return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    out=ap.parse_args().out.resolve()
    if out.is_relative_to(ROOT/"rpt_2027"): raise ValueError("production path")
    out.mkdir(parents=True,exist_ok=True)
    lock=json.loads(LOCK.read_text())["sjkc_matematik_year3"]
    raw=SOURCE.read_bytes()
    assert digest(raw)==lock["source_sha256_by_subject_year"][KEY]
    with fitz.open(stream=raw,filetype="pdf") as src,fitz.open() as cover:
        cover.insert_pdf(src,from_page=0,to_page=0)
        p=cover[0]
        assert abs(p.rect.width-lock["page_width"])<=lock["tolerance_pt"]
        assert abs(p.rect.height-lock["page_height"])<=lock["tolerance_pt"]
        slots={k:lock[k] for k in ("logo_interior_top_left","logo_image_safe_top_left","school_row_top_left","teacher_row_top_left")}
        assert all(p.rect.contains(fitz.Rect(v)) for v in slots.values())
        assert fitz.Rect(slots["logo_interior_top_left"]).contains(fitz.Rect(slots["logo_image_safe_top_left"]))
        spans=[{"text":s["text"],"bbox":s["bbox"],"size":s["size"],"font":s["font"],"color":s["color"]} for b in p.get_text("dict")["blocks"] if b.get("type")==0 for l in b["lines"] for s in l["spans"]]
        cover.save(out/"REFERENCE_EXISTING_Y3_COVER.pdf")
        p.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(out/"REFERENCE_EXISTING_Y3_COVER.png")
        qa=fitz.open(stream=cover.tobytes(),filetype="pdf")
        q=qa[0]
        for k,v in slots.items():
            q.draw_rect(fitz.Rect(v),color=(0.8,0.15,0.15),width=0.8,overlay=True)
        q.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(out/"REFERENCE_Y3_PROFILE_SLOT_QA.png")
        qa.close()
        # Detect title spans for review before changing any year label. Do not
        # assume that embedded fonts, Chinese year glyphs or background are reusable.
        title_spans=[s for s in spans if re.search(r"(?i)tahun\s*3\b|year\s*3\b|三年级|三年級|第[三3]年",s["text"])]
        evidence={"status":"REFERENCE_READY_NEW_COVERS_NOT_APPROVED","source_sha256":digest(raw),"source_path":str(SOURCE.relative_to(ROOT)),"verified_layout":lock,"cover_spans":spans,"year_title_candidate_spans":title_spans,"new_cover_years":[4,5,6],"release":False}
        (out/"cover_reference_manifest.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
        print(json.dumps({"source_sha256":digest(raw),"slots":slots,"year_title_candidates":title_spans,"all_cover_text":p.get_text()},ensure_ascii=False))
    assert digest(SOURCE.read_bytes())==digest(raw)

if __name__=="__main__":main()
