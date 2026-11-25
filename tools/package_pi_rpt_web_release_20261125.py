"""Prepare only the five PI Web PDFs and matching indexes in a separate checkout.
Retain exact production cover graphics and metadata; no deployment or user data.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import fitz

COUNTS={2:112,3:148,4:152,5:144,6:142}
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    return json.loads(p.read_text(encoding="utf8"))
def write(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf8")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("artifact",type=Path)
    parser.add_argument("checkout",type=Path)
    a=parser.parse_args()
    root=a.checkout/"rpt_2027/web_2027_pdfs"
    mp=root/"manifest.json"
    cp=root/"original_cover_layout_verified.json"
    wp=a.checkout/"web/rpt_weekly_suggestions_2027.json"
    manifest,cover,weekly=map(read,(mp,cp,wp))
    schedule=read(a.artifact/"teacher_schedule.json")
    assert schedule["source_commit"]=="758f15c44e06dc8d9923cb9eb5137c9e77503d14"
    for year,count in COUNTS.items():
        key=f"pendidikan_islam:{year}"
        entry=manifest["files"][key]
        path=root/entry["path"]
        assert sha(path)==entry["sha256"]==cover["source_sha256_by_subject_year"][key]
        new=a.artifact/f"RPT_Pendidikan_Islam_Tahun_{year}_2027_preview.pdf"
        tmp=path.with_suffix(".new.pdf")
        with fitz.open(path) as old, fitz.open(new) as body, fitz.open() as combined:
            original=old[0].get_pixmap(alpha=False)
            combined.insert_pdf(old,from_page=0,to_page=0)
            combined.insert_pdf(body,from_page=1)
            combined.save(tmp,garbage=4,deflate=True)
        with fitz.open(tmp) as checked:
            first=checked[0].get_pixmap(alpha=False)
            assert first.samples==original.samples,(year,"cover altered")
            ids=[int(x) for p in list(checked)[1:] for x in re.findall(r"PdP (\d{3})",p.get_text())]
            assert ids==list(range(1,count+1))
            assert all(abs(p.rect.width-841.9)<2 and abs(p.rect.height-595.3)<2 for p in checked)
            pages=len(checked)
        tmp.replace(path)
        digest=sha(path)
        entry.update(sha256=digest,bytes=path.stat().st_size,pages=pages,source_stage="PI_698_NATIVE_RPH_20261125",full_school_closures_rescheduled=True)
        cover["source_sha256_by_subject_year"][key]=digest
        # Keep the exact existing weekly-suggestion schema.
        weeks=schedule["years"][str(year)]["weeks"]
        weekly[f"PI:{year}"]={w:[*v["dates"],{"":v["pdp"]}] for w,v in weeks.items() if v["pdp"]}
        actual=[n for w,v in sorted(weekly[f"PI:{year}"].items(),key=lambda x:int(x[0])) for n in v[4][""]]
        assert actual==ids and max(map(int,weekly[f"PI:{year}"]))<=38
        print("PI_WEB_RELEASE_CANDIDATE",year,count,pages,digest,flush=True)
    manifest["pages"]=sum(v["pages"] for v in manifest["files"].values())
    write(mp,manifest)
    write(cp,cover)
    # Preserve production compact per-subject format.
    wp.write_text("{\n"+",\n".join(json.dumps(k)+":"+json.dumps(v,separators=(",",":")) for k,v in sorted(weekly.items()))+"\n}\n",encoding="utf8")

if __name__=="__main__":
    main()
