"""Build complete content candidate for lower Science session slots.
Original induction, assessment and closure retained. Split guided activity
uses the two specifically written parts, not arbitrary truncated text.
"""
import json,sys
from pathlib import Path
from collections import Counter
def phase(name,minutes,teacher,pupils,source_id):
    assert minutes>0 and teacher.strip() and pupils.strip()
    return dict(phase=name,minutes=minutes,teacher=teacher,pupils=pupils,source_id=source_id)
def build(allocation,original,authored):
    out={}
    for key in ("science_dlp:2","science_dlp:3"):
        sources={}
        for s in original["sets"][key]["sessions"]:
            for p in s["parts"]:
                sid=p["source"]["source_id"]
                q=sources.setdefault(sid,{"meta":p["source"],"phases":{}})
                a=p["phase"]
                q["phases"][a["start"]]=a
        def get(sid):
            q=sources[sid]
            return [phase(a["phase"],a["end"]-a["start"],a["teacher"],a["pupils"],sid) for a in sorted(q["phases"].values(),key=lambda a:a["start"])]
        content=[];split_ids=set();extra_ids=set();covered=Counter()
        for s in allocation["sets"][key]["sessions"]:
            status=s["status"];parts=s["source_parts"];num=s["session"];cap=s["capacity"];activities=[]
            ids=[p["source"]["source_id"] for p in parts]
            for p,sid in zip(parts,ids):covered[sid]+=p["minutes"]
            if status=="SPLIT_SOURCE_REVIEW":
                sid=ids[0];base=get(sid);assert len(base)==4 and cap==30
                a=authored["split_sources"][key][sid];split_ids.add(sid)
                if parts[0]["offset"]==0:
                    p=a["part1"];activities=[base[0],phase("Guided main activity",25,p["teacher"],p["pupils"],sid)]
                else:
                    p=a["part2"];activities=[phase("Recap and continued activity",5,p["teacher"],p["pupils"],sid),base[2],base[3]]
            elif status in ("EXACT_RPH","COMBINED_SAME_UNIT_REVIEW"):
                for sid in ids:activities.extend(get(sid))
            elif status in ("EXTENSION_REVIEW","REINFORCEMENT_REVIEW"):
                a=authored["reinforcement_sessions"][key][str(num)];extra_ids.add(str(num));sid=a["source"]
                extra=phase("Targeted reinforcement",30,a["teacher"],a["pupils"],sid)
                if ids:
                    assert ids==[sid];activities=get(sid);activities.insert(-2,extra)
                else:
                    assert sid==s["reinforcement_source"];activities=[extra];ids=[sid]
            else:raise ValueError(status)
            assert sum(a["minutes"] for a in activities)==cap,(key,num,status)
            content.append({"session":num,"week_index":s["week_index"],"minutes":cap,"status":status,"source_ids":ids,"source_metadata":[sources[i]["meta"] for i in ids],"activities":activities})
        assert split_ids==set(authored["split_sources"][key])
        assert extra_ids==set(authored["reinforcement_sessions"][key])
        assert covered=={sid:q["meta"]["original_minutes"] for sid,q in sources.items()}
        assert len(content)==70
        out[key]=content
        print("LOWER_SCIENCE_CONTENT_OK",key,"sessions",len(content),"source_ids",len(sources),"split_sources",len(split_ids),"new_reinforcement",len(extra_ids),flush=True)
    return {"status":"PRIVATE_CONTENT_CANDIDATE","release_ready":False,"sets":out}
if __name__=="__main__":
    a,b,c,o=sys.argv[1:]
    result=build(*(json.loads(Path(p).read_text()) for p in (a,b,c)))
    Path(o).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
