"""Release both Science RPTs only after native Word/PDF geometry and route QA."""
import json,hashlib,subprocess
from tempfile import TemporaryDirectory
from pathlib import Path
import fitz
from tools.build_rpt_dlp_native_20261126 import ROOT
from tools.build_rpt_dlp_full_standards_20261126 import build_word,render
from tools.rpt_dlp_compact_pagination_20261126 import measure_weeks,choose_sizes
from tools.prepare_dlp_week_column_release_20261126 import verify_bottom
def main():
    base=ROOT/"full_standards_dlp_pdf_2027";mp=base/"manifest.json"
    cp=ROOT/"web_2027_pdfs/original_cover_layout_verified.json"
    m=json.loads(mp.read_text());cover=json.loads(cp.read_text())
    for year in (4,5):
        key=f"science_dlp:{year}"
        m.setdefault("session_first_by_set",{})[key]="20261126"
        mp.write_text(json.dumps(m,indent=2)+"\n")
        target=base/m["files"][key]["path"]
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            blob,*_=build_word("science_dlp",year,whole_weeks=True,pilot=True)
            pilot=folder/"pilot.docx";pilot.write_bytes(blob)
            subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",str(folder),str(pilot)],check=True,timeout=180)
            with fitz.open(pilot.with_suffix(".pdf")) as d:heights=measure_weeks(d)
            assert len(heights)==35
            sizes=choose_sizes(heights)
            render("science_dlp",year,folder,whole_weeks=True,compact_sizes=sizes)
            raw=(folder/f"RPT_science_dlp_Year_{year}_2027.pdf").read_bytes()
            with fitz.open(stream=raw,filetype="pdf") as new,fitz.open(target) as old:
                assert new[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples==old[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples
                pages=len(new)
                assert pages==len(sizes)+2
                for p in list(new)[1:-1]:verify_bottom(p,key)
                assert " ".join(p.get_text() for p in list(new)[1:-1]).count("Reinforcement / PBD")==int(year==4)
            target.write_bytes(raw)
            digest=hashlib.sha256(raw).hexdigest()
            m["files"][key].update(sha256=digest,bytes=len(raw),pages=pages)
            m["page_groups"][key]=sizes
            cover["full_standards_dlp_pdf_covers"]["source_sha256_by_subject_year"][key]=digest
            mp.write_text(json.dumps(m,indent=2)+"\n")
            cp.write_text(json.dumps(cover,indent=2,ensure_ascii=False)+"\n")
    from web.rpt_compact_pdf import dlp_whole_week_release
    assert dlp_whole_week_release(ROOT)
    from web.dlp_rpt_weekly_suggestions import published_weeks
    for year in (4,5):
        weeks=published_weeks("SCIENCE_DLP",year)
        assert len(weeks)==35
        assert sum(len(w["labels"]) for w in weeks.values())==(69 if year==4 else 70)
        assert all(len(w["labels"])+w["reserve_slots"]==2 for w in weeks.values())
        print("SCIENCE_FIXED_RPT_RELEASE_OK",year,35,70,flush=True)
if __name__=="__main__":main()
