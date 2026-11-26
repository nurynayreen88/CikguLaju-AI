"""Render the 22 source-preserving 60-minute Science Y4/5 RPH candidates.
Use exact original renderer and standards; do not mutate live source JSON.
"""
import json,sys,copy,re
from pathlib import Path
from io import BytesIO
from docx import Document
import fitz
from dlp_year2_rph import _pdf,_word
from staging.dlp.year4 import render_science as y4
from staging.dlp.year5 import render_science as y5

def main(config_path,plan_path,outpath):
    config=json.loads(Path(config_path).read_text())["sets"]
    allocation=json.loads(Path(plan_path).read_text())["sets"]
    out=Path(outpath);out.mkdir(parents=True,exist_ok=True)
    teacher={"class":"Bestari","time":"08:00 - 09:00","date":"2027-01-12","students":"30"}
    total=0
    for year,module,plans in [(4,y4,y4.load_plans()),(5,y5,y5.load_plans()[1])]:
        key=f"science_dlp:{year}"
        byid={p["id"].split("-")[-1]:p for p in plans}
        expected={}
        for s in allocation[key]["sessions"]:
            if s["status"]=="WHOLE_PHASE_CONTINUATION_REVIEW":
                ids={p["source"]["source_id"] for p in s["parts"]}
                assert len(ids)==1 and s["source_minutes"]==30 and s["reserve_minutes"]==30
                assert all(p["whole_phase"] for p in s["parts"])
                expected[next(iter(ids))]=s
        assert set(expected)==set(config[key]),(key,set(expected)^set(config[key]))
        for k,s in expected.items():
            original=byid[k]
            assert original["minutes"]==30
            p=copy.deepcopy(original);activity=config[key][k]
            assert activity["minutes"]==30
            if year==4:
                p["phases"].insert(-2,activity)
            else:
                p["phases"].insert(-2,(f"{activity['phase']} · 30 min",activity["teacher"],activity["pupils"]))
                p["label"]=re.sub(r"30 min$", "60 min",p["label"])
            p["minutes"]=60
            # Additional resources used by this specific activity; existing
            # teaching materials and all original objective/standard text kept.
            p["materials"] += "; activity-specific cards, diagrams or recorded results as described in targeted reinforcement"
            assert p["phases"][:2]+p["phases"][3:]==original["phases"]
            for field in ("content_standards","learning_standards","objective"):
                assert p[field]==original[field]
            for ext,renderer in (("docx",_word),("pdf",_pdf)):
                target=out/f"SCIENCE_Y{year}_{k}_60min.{ext}"
                with target.open("wb") as stream:module.render_plan(stream,p,renderer,teacher=teacher)
                assert target.stat().st_size>1000
                if ext=="docx":
                    doc=Document(target)
                    txt=" ".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
                    assert activity["teacher"] in txt and activity["pupils"] in txt
                else:
                    with fitz.open(target) as pdf:
                        assert len(pdf)==1,(year,k,"layout",len(pdf))
            total+=1
        print("SCIENCE_REINFORCEMENT_RENDERED",year,len(expected),flush=True)
    assert total==22
if __name__=="__main__":main(*sys.argv[1:])
