"""Compare the optimized RPT candidate to actual pinned RPH sources.

Run with the pinned main checkout as working directory. This inventory does
not edit source RPHs and never treats a partially intersected activity as
a complete new session.
"""
import argparse,json,re,sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from tools.verify_dlp_rph_workload_20261126 import plans,phase_rows,TIME

def key_for(identifier,label):
    m=re.search(r"(?:^|[-_])([LR]\d+)$",str(identifier),re.I)
    if m:return m[1][0].upper()+f"{int(m[1][1:]):02d}"
    m=re.search(r"\b(Lesson|Review)\s+(\d+)\b",str(label),re.I)
    assert m,(identifier,label)
    return m[1][0].upper()+f"{int(m[2]):02d}"

def main():
    a=argparse.ArgumentParser();a.add_argument("--plan",type=Path,required=True);a.add_argument("--out",type=Path,required=True);args=a.parse_args()
    candidate=json.loads(args.plan.read_text())["plans"]
    source={}
    for (sub,y),rows in plans():
        key=f"{'mathematics' if sub=='math' else 'science'}_dlp:{y}"
        inventory={}
        for identifier,label,phases,duration in rows:
            name=key_for(identifier,label);assert name not in inventory,(key,name)
            timeline=[];start=0
            for phase,teacher,pupils in phase_rows(phases):
                m=TIME.search(phase);assert m,(identifier,phase)
                end=start+int(m[1])
                assert teacher.strip() and pupils.strip()
                timeline.append({"phase":phase,"start":start,"end":end,"teacher":teacher,"pupils":pupils})
                start=end
            inventory[name]={"id":identifier,"label":label,"duration":duration,"phase_minutes":start,"phases":timeline}
        source[key]=inventory
    results=[]
    for p in candidate:
        key=p["key"];inventory=source[key];counts=Counter();coverage=Counter();issues=[]
        for week in p["weeks"]:
            for s in week["sessions"]:
                for part in s["source_parts"]:
                    label=part["source_id"];item=inventory[label]
                    lo,hi=part["from_minute"],part["to_minute"]
                    coverage[label]+=hi-lo
                    assert part["original_minutes"]==item["duration"],(key,label,part,item["duration"])
                    if item["duration"]!=item["phase_minutes"]:
                        issues.append({"source":label,"issue":"SOURCE_PHASE_DURATION_MISMATCH","declared":item["duration"],"actual":item["phase_minutes"]})
                    matched=[]
                    for phase in item["phases"]:
                        if max(lo,phase["start"])>=min(hi,phase["end"]):continue
                        whole=lo<=phase["start"] and phase["end"]<=hi
                        matched.append({**phase,"whole_phase":whole})
                    part["actual_rph_id"]=item["id"]
                    part["actual_rph_label"]=item["label"]
                    part["source_activity_matches"]=matched
                    status="WHOLE_PHASES_ONLY" if matched and all(x["whole_phase"] for x in matched) else "ACTIVITY_BOUNDARY_REVIEW"
                    part["activity_status"]=status;counts[status]+=1
        assert set(coverage)==set(inventory),(key,set(coverage)^set(inventory))
        assert all(coverage[k]==v["duration"] for k,v in inventory.items()),key
        unique_issues=list({x["source"]:x for x in issues}.values())
        p["rph_source_match"]={"count":len(inventory),"phase_review_counts":dict(counts),"source_issues":unique_issues,"release_ready":False}
        print("DLP_ACTUAL_RPH_MATCH",key,len(inventory),dict(counts),"source_phase_issues",len(unique_issues),flush=True)
        results.append(p)
    args.out.write_text(json.dumps({"release_ready":False,"plans":results},ensure_ascii=False,indent=2)+"\n")

if __name__=="__main__":main()
