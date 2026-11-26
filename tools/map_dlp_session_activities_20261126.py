"""Map every session-first slot to its exact original RPH activities.
Private review artifact; do not publish an incomplete activity or new ID.
"""
import json,re,sys
from collections import defaultdict,Counter
from pathlib import Path
from tools.verify_dlp_rph_workload_20261126 import plans,phase_rows,TIME

def main(infile,outfile):
    data=json.loads(Path(infile).read_text())
    assert data["status"]=="PRIVATE_SESSION_FIRST_CANDIDATE"
    output={"status":"PRIVATE_SESSION_ACTIVITY_REVIEW","release_ready":False,"sets":{}}
    total_sources=0
    for (subject,year),rows in plans():
        key=f"{'mathematics' if subject=='math' else 'science'}_dlp:{year}"
        actual={};review=0
        for identifier,label,phases,duration in rows:
            m=re.search(r"\bLesson\s+(\d+)\b",label,re.I)
            if m:k=f"L{int(m[1]):02d}"
            else:
                assert re.search(r"review|revision|consolidation",label,re.I),(key,label)
                review+=1;k=f"R{review:02d}"
            assert k not in actual
            blocks=[];cursor=0
            for name,teacher,pupils in phase_rows(phases):
                t=TIME.search(name);assert t,(key,k,name)
                m=int(t[1]);assert m>0 and teacher.strip() and pupils.strip()
                blocks.append({"phase":name[:t.start()],"start":cursor,"end":cursor+m,"teacher":teacher,"pupils":pupils})
                cursor+=m
            assert cursor==duration,(key,k,cursor,duration)
            actual[k]={"source_rph_id":identifier,"source_label":label,"minutes":duration,"phases":blocks}
        total_sources+=len(actual)
        counts=Counter();covered=defaultdict(list);weeks=[]
        for w in data["sets"][key]:
            sessions=[]
            for s in w["sessions"]:
                parts=[];partial=False
                for p in s["source_parts"]:
                    original=actual[p["source_id"]]
                    assert original["minutes"]==p["original_minutes"]
                    a,b=p["from_minute"],p["to_minute"]
                    assert 0<=a<b<=original["minutes"]
                    covered[p["source_id"]].append((a,b))
                    blocks=[]
                    for block in original["phases"]:
                        x,y=max(a,block["start"]),min(b,block["end"])
                        if x>=y:continue
                        full=x==block["start"] and y==block["end"]
                        partial|=not full
                        blocks.append({**block,"allocated_from":x,"allocated_to":y,"allocated_minutes":y-x,
                                       "whole_phase":full,"review_required":not full})
                    assert sum(b["allocated_minutes"] for b in blocks)==p["to_minute"]-p["from_minute"]
                    parts.append({**p,"source_rph_id":original["source_rph_id"],"source_label":original["source_label"],"activities":blocks})
                if not parts:status="RESERVE_NOT_NUMBERED_RPH"
                elif len(parts)==1 and parts[0]["from_minute"]==0 and parts[0]["to_minute"]==parts[0]["original_minutes"] and not s["reserve_minutes"]:
                    status="EXACT_ORIGINAL_RPH"
                elif partial:status="ACTIVITY_SPLIT_REVIEW"
                else:status="SESSION_COMPOSITION_REVIEW"
                counts[status]+=1
                sessions.append({**s,"source_parts":parts,"status":status})
            weeks.append({**w,"sessions":sessions})
        assert set(covered)==set(actual)
        for k,parts in covered.items():
            cursor=0
            for a,b in parts:
                assert a==cursor,(key,k,parts)
                cursor=b
            assert cursor==actual[k]["minutes"]
        output["sets"][key]={"weeks":weeks,"counts":dict(counts)}
        print("SESSION_ACTIVITY_MAP",key,json.dumps(dict(counts)),flush=True)
    assert total_sources==701
    Path(outfile).write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print("SESSION_ACTIVITY_MAP_COMPLETE",total_sources,"release_ready",False,flush=True)
if __name__=="__main__":main(sys.argv[1],sys.argv[2])
