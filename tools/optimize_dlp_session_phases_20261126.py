"""Phase-aware reallocation of fixed weekly slots; no source activity edits.
Keep all source order/durations, use reserve minutes to avoid cutting activities.
Private candidate only; composition and split sessions need academic review.
"""
import json,sys,bisect
from collections import Counter
from pathlib import Path
def optimize(data):
    result={}
    for key,v in data["sets"].items():
        sources={};slots=[]
        for w in v["weeks"]:
            for s in w["sessions"]:
                slots.append((w["week"],s["session"],s["minutes"]))
                for p in s["source_parts"]:
                    q=sources.setdefault(p["source_id"],{"meta":{x:p[x] for x in ("source_id","source_rph_id","source_label","original_minutes","title","standards")},"phases":{}})
                    for a in p["activities"]:
                        q["phases"][a["start"]]={x:a[x] for x in ("phase","start","end","teacher","pupils")}
        phase_edges={0};topic_edges={0};blocks=[];pos=0
        for q in sources.values():
            cur=0
            for a in sorted(q["phases"].values(),key=lambda a:a["start"]):
                assert a["start"]==cur
                cur=a["end"];blocks.append((pos+a["start"],pos+a["end"],q["meta"],a));phase_edges.add(pos+a["end"])
            assert cur==q["meta"]["original_minutes"]
            pos+=cur;topic_edges.add(pos)
        total=pos;remaining=sum(s[2] for s in slots);edges=sorted(topic_edges)
        dp={0:(0,None)};layers=[]
        for _,_,duration in slots:
            remaining-=duration;nxt={}
            for start,(cost,_) in dp.items():
                for end in range(max(start,total-remaining),min(total,start+duration)+1):
                    if end==start and start<total:continue
                    transitions=max(0,bisect.bisect_left(edges,end)-bisect.bisect_right(edges,start))
                    c=cost+100000*(end not in phase_edges)+100*transitions+10*(end not in topic_edges)+((duration-(end-start))**2 if start<total else 0)*0.001
                    if end not in nxt or c<nxt[end][0]:nxt[end]=(c,start)
            assert nxt,key
            layers.append(nxt);dp=nxt
        assert total in dp,key
        plan=[];end=total
        for (w,num,duration),layer in zip(reversed(slots),reversed(layers)):
            start=layer[end][1];plan.append((w,num,duration,start,end));end=start
        assert end==0
        rows=[];counts=Counter();coverage=Counter()
        for w,num,cap,a,b in reversed(plan):
            parts=[]
            for x,y,m,p in blocks:
                if x>=b or y<=a:continue
                l,r=max(a,x),min(b,y);coverage[(m["source_id"],p["start"])]+=r-l
                parts.append({"source":m,"phase":p,"allocated_from":p["start"]+l-x,"allocated_to":p["start"]+r-x,"whole_phase":(l,r)==(x,y)})
            if not parts:status="RESERVE"
            elif not all(p["whole_phase"] for p in parts):status="SPLIT_PHASE_REVIEW"
            elif len({p["source"]["source_id"] for p in parts})>1:status="COMBINED_SOURCE_REVIEW"
            elif a in topic_edges and b in topic_edges and b-a==cap:status="EXACT_RPH"
            else:status="WHOLE_PHASE_CONTINUATION_REVIEW"
            counts[status]+=1
            rows.append({"week":w,"session":num,"capacity":cap,"source_minutes":b-a,"reserve_minutes":cap-(b-a),"status":status,"parts":parts})
        assert all(coverage[(m["source_id"],p["start"])]==y-x for x,y,m,p in blocks)
        result[key]={"counts":dict(counts),"source_count":len(sources),"sessions":rows}
        print("PHASE_AWARE",key,dict(counts),flush=True)
    assert sum(v["source_count"] for v in result.values())==701
    assert sum(len(v["sessions"]) for v in result.values())==855
    return {"status":"PRIVATE_PHASE_AWARE_REVIEW","release_ready":False,"sets":result}
if __name__=="__main__":
    data=json.loads(Path(sys.argv[1]).read_text())
    Path(sys.argv[2]).write_text(json.dumps(optimize(data),ensure_ascii=False,indent=2)+"\n")
