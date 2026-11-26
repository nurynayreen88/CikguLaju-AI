"""Prepare only the independently verified Math Y2 release.
Leave other nine published PDFs and all original RPH sources unchanged.
"""
import json,re,hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import fitz
from tools.build_rpt_dlp_native_20261126 import ROOT
from tools.build_rpt_dlp_full_standards_20261126 import render
from tools.prepare_dlp_week_column_release_20261126 import verify_bottom
def main():
    key="mathematics_dlp:2";subject,year="mathematics_dlp",2
    base=ROOT/"full_standards_dlp_pdf_2027";mp=base/"manifest.json"
    cp=ROOT/"web_2027_pdfs/original_cover_layout_verified.json"
    m=json.loads(mp.read_text());cover=json.loads(cp.read_text())
    m.setdefault("session_first_by_set",{})[key]="20261126"
    sizes=[4,4,3,3,3,3,3,3,3,3,3]
    m["page_groups"][key]=sizes
    mp.write_text(json.dumps(m,indent=2)+"\n")
    target=base/m["files"][key]["path"]
    with TemporaryDirectory() as tmp:
        folder=Path(tmp)
        render(subject,year,folder,whole_weeks=True,compact_sizes=sizes)
        raw=(folder/f"RPT_{subject}_Year_{year}_2027.pdf").read_bytes()
        with fitz.open(stream=raw,filetype="pdf") as new,fitz.open(target) as previous:
            assert new[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples==previous[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples
            assert len(new)==13
            for p in list(new)[1:-1]:verify_bottom(p,key)
            body=" ".join(p.get_text() for p in list(new)[1:-1])
            assert body.count("Reinforcement / PBD")==5
        target.write_bytes(raw)
        digest=hashlib.sha256(raw).hexdigest()
        m["files"][key].update(sha256=digest,bytes=len(raw),pages=13)
        cover["full_standards_dlp_pdf_covers"]["source_sha256_by_subject_year"][key]=digest
        mp.write_text(json.dumps(m,indent=2)+"\n")
        cp.write_text(json.dumps(cover,indent=2,ensure_ascii=False)+"\n")
    from web.rpt_compact_pdf import dlp_whole_week_release
    assert dlp_whole_week_release(ROOT)
    from web.dlp_rpt_weekly_suggestions import published_weeks
    weeks=published_weeks("MATH_DLP",2)
    assert len(weeks)==35 and sum(len(w["labels"]) for w in weeks.values())==96
    assert sum(w["reserve_slots"] for w in weeks.values())==5
    for n,w in weeks.items():
        assert len(w["labels"])+w["reserve_slots"]==(2 if n in (1,5,20,35) else 3)
    print("MATH2_SESSION_RELEASE_OK",digest,flush=True)
if __name__=="__main__":main()
