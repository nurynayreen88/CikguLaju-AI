"""Create a complete whole-week release only after every generated document passes."""
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import fitz
from tools.build_rpt_dlp_full_standards_20261126 import render
from tools.build_rpt_dlp_native_20261126 import PINS,ROOT

def main():
    base=ROOT/"full_standards_dlp_pdf_2027"
    manifest_path=base/"manifest.json"
    cover_path=ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json"
    manifest=json.loads(manifest_path.read_text())
    cover=json.loads(cover_path.read_text())
    entries={};outputs={}
    with TemporaryDirectory() as tmp:
        out=Path(tmp)
        for key,source in PINS.items():
            subject,y=key.split(":");year=int(y)
            render(subject,year,out,whole_weeks=True)
            raw=(out/f"RPT_{subject}_Year_{year}_2027.pdf").read_bytes()
            rel=f"{subject}/tahun_{year}.pdf"
            with fitz.open(stream=raw,filetype="pdf") as doc,fitz.open(base/rel) as previous:
                assert doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples==previous[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples,key
                assert not any(re.fullmatch(r"\d+\s*min(?:utes)?",line.strip(),re.I) for p in list(doc)[1:-1] for line in p.get_text().splitlines()),key
                entries[key]={"path":rel,"source_sha256":source,"sha256":sha256(raw).hexdigest(),"bytes":len(raw),"pages":len(doc)}
            outputs[rel]=raw
    assert set(entries)==set(PINS)
    manifest.update(schedule="whole_lesson_20261126",files=entries)
    cover["full_standards_dlp_pdf_covers"]["source_sha256_by_subject_year"]={k:v["sha256"] for k,v in entries.items()}
    for rel,raw in outputs.items():(base/rel).write_bytes(raw)
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    cover_path.write_text(json.dumps(cover,indent=2,ensure_ascii=False)+"\n")
    from web.rpt_compact_pdf import dlp_whole_week_release
    assert dlp_whole_week_release(ROOT)
    print("DLP_WHOLE_RELEASE_ALL_TEN_VERIFIED",flush=True)

if __name__=="__main__":main()
