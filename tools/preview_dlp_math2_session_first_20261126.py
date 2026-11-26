"""Build real Year 2 Mathematics Word/PDF candidate from session-first schedule.
All 96 RPHs retained exactly; remaining five slots are reinforcement reserve,
not fabricated lesson IDs. Other subjects and live manifest remain untouched.
"""
import json,re
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import fitz
from tools.build_rpt_dlp_full_standards_20261126 import build_word,render
from tools.build_rpt_dlp_native_20261126 import ROOT
from tools.build_dlp_session_first_candidate_20261126 import build
from tools.rpt_dlp_compact_pagination_20261126 import measure_weeks,choose_sizes
from tools.prepare_dlp_week_column_release_20261126 import verify_bottom
from datetime import date
import subprocess

def candidate_schedule(subject,year,rows,root):
    assert (subject,year)==("mathematics_dlp",2)
    weeks=build(subject,year,rows,root)
    index=0;out=[];loads={};weekly=[]
    def label(g):
        a,b=map(date.fromisoformat,(g["start"],g["end"]))
        return f"{a.day}-{b.day} {b:%b}" if a.month==b.month else f"{a.day} {a:%b}-{b.day} {b:%b}"
    for w in weeks:
        a,b=w["dates"];n=w["week"]
        labels=[f"Week {n:02d}","A "+label(a),"B "+label(b)]
        used=[]
        for s in w["sessions"]:
            if not s["source_parts"]:
                assert s["reserve_minutes"]==60 and index==len(rows)
                # Explicit reserve slots retain the final approved review's
                # learning standards and evidence. Not a new Lesson/RPH ID.
                c,links=rows[-1]
                field=c[2]
                if " ".join(field) in ("Consolidation Review taught standards","Review Review taught standards"):
                    mappings=json.loads((Path(root)/"dlp/standard_descriptions/review_mappings.json").read_text())["mappings"]["mathematics_dlp:2"]
                    field=["LS "+", ".join(mappings["R18"])]
                out.append(([labels,["Reinforcement / PBD follow-up","Reserve session — no new standard"],field,c[3],c[4]],links))
                continue
            assert len(s["source_parts"])==1
            p=s["source_parts"][0]
            assert (p["from_minute"],p["to_minute"],p["original_minutes"])==(0,60,60)
            c,links=rows[index];index+=1
            out.append(([labels,*c[1:]],links))
            used.append(p["source_id"])
        loads[n]=len(used)*60
        weekly.append({"week":n,"dates":w["dates"],"source_ids":used,"reserve_slots":len(w["sessions"])-len(used)})
    assert index==len(rows)==96
    assert sum(loads.values())==5760
    assert sum(w["reserve_slots"] for w in weekly)==5
    original=[r for r in out if r[0][1][0]!="Reinforcement / PBD follow-up"]
    assert len(out)==101 and len(original)==96
    assert all(x[0][1:]==y[0][1:] and x[1]==y[1] for x,y in zip(rows,original,strict=True))
    return out,loads,weekly

def main():
    out=Path("math2_session_first_review");out.mkdir(exist_ok=True)
    subject="mathematics_dlp";year=2
    captured={}
    def adapter(subject,year,rows,root):
        result,loads,weekly=candidate_schedule(subject,year,rows,root)
        captured["weekly"]=weekly
        return result,loads
    with patch("tools.dlp_whole_lesson_calendar_20261126.schedule",adapter):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            blob,*_=build_word(subject,year,whole_weeks=True,pilot=True)
            pilot=folder/"pilot.docx";pilot.write_bytes(blob)
            subprocess.run(["libreoffice","-env:UserInstallation="+(folder/"lo").as_uri(),"--headless","--convert-to","pdf","--outdir",str(folder),str(pilot)],check=True,timeout=180)
            with fitz.open(pilot.with_suffix(".pdf")) as pdf:heights=measure_weeks(pdf)
            assert len(heights)==35
            sizes=choose_sizes(heights)
        render(subject,year,out,whole_weeks=True,compact_sizes=sizes)
    pdf=out/f"RPT_{subject}_Year_{year}_2027.pdf"
    old=ROOT/"full_standards_dlp_pdf_2027"/subject/"tahun_2.pdf"
    with fitz.open(pdf) as new,fitz.open(old) as previous:
        assert new[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples==previous[0].get_pixmap(matrix=fitz.Matrix(2,2)).samples
        for p in list(new)[1:-1]:verify_bottom(p,"mathematics_dlp:2")
        weeks=[int(n) for p in list(new)[1:-1] for n in re.findall(r"(?m)^Week\s+(\d{2})\s*$",p.get_text())]
        assert weeks==[w["week"] for w in captured["weekly"]]
        body=" ".join(p.get_text() for p in list(new)[1:-1])
        assert body.count("Reinforcement / PBD")==5,(body.count("Reinforcement / PBD"),"reserve slots")
        print("MATH2_SESSION_FIRST_DOCUMENT_OK",len(new),"pages",sizes,"96 source RPH preserved",flush=True)
    (out/"weekly_candidate.json").write_text(json.dumps({"status":"PRIVATE_REVIEW","source_rph_count":96,"weekly":captured["weekly"],"page_groups":sizes},indent=2)+"\n")
if __name__=="__main__":main()
