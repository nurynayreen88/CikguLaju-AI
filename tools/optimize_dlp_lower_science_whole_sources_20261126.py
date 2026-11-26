"""Science Y2/Y3: optimize whole-source delivery rather than cut arbitrary phases.
35 weeks with one 30 and one 60 min session, either order. Keep all source IDs
and their order; only combine adjacent 30 min RPHs from the same unit.
Private review: split/extension/reinforcement content not yet released.
"""
import json,sys
from pathlib import Path
from functools import lru_cache
from collections import Counter
def allocate(key,source):
    n=len(source)
    def choices(i,h,cap):
        if i==n:return [(i,0,[],0,cap)]
        r=source[i]["original_minutes"]-h
        out=[]
        if r<=cap:
            out.append((i+1,0,[(i,h,r)],0,cap-r))
            if r==30 and cap==60 and i+1<n and source[i+1]["original_minutes"]==30 and source[i]["title"][-1]==source[i+1]["title"][-1]:
                out.append((i+2,0,[(i,h,r),(i+1,0,30)],1,0))
        if r==60 and cap==30:out.append((i,30,[(i,0,30)],10,0))
        if not h:out.append((i,h,[],3,cap))
        return out
    @lru_cache(None)
    def best(w,i,h):
        if w==35:return (0,[]) if i==n and h==0 else (10**8,[])
        ans=(10**8,[])
        for a,b in [(60,30),(30,60)]:
            for j,g,p,c,r in choices(i,h,a):
                for l,m,q,e,s in choices(j,g,b):
                    t,tail=best(w+1,l,m)
                    cost=t+c+e+(r+s)/30*.1
                    if cost<ans[0]:ans=(cost,[(a,p,r),(b,q,s)]+tail)
        return ans
    cost,plan=best(0,0,0)
    assert len(plan)==70
    coverage=Counter();counts=Counter();out=[];last=None
    for j,(cap,parts,reserve) in enumerate(plan,1):
        for i,a,t in parts:
            assert coverage[source[i]["source_id"]]==a
            coverage[source[i]["source_id"]]+=t
        status=("REINFORCEMENT_REVIEW" if not parts else "SPLIT_SOURCE_REVIEW" if any(source[i]["original_minutes"]!=t for i,a,t in parts) else "COMBINED_SAME_UNIT_REVIEW" if len(parts)>1 else "EXTENSION_REVIEW" if reserve else "EXACT_RPH")
        counts[status]+=1
        p=[{"source":source[i],"offset":a,"minutes":t} for i,a,t in parts]
        out.append({"session":j,"week_index":(j+1)//2,"capacity":cap,"source_parts":p,"reserve_minutes":reserve,"status":status,"reinforcement_source":last if not parts else None})
        if p:last=p[-1]["source"]["source_id"]
    assert coverage=={m["source_id"]:m["original_minutes"] for m in source}
    assert sum(x["reserve_minutes"] for x in out)==270
    assert all(sorted([a["capacity"],b["capacity"]])==[30,60] for a,b in zip(out[::2],out[1::2]))
    print("LOWER_SCIENCE_WHOLE_SOURCE",key,dict(counts),flush=True)
    return {"counts":dict(counts),"sessions":out}
def main(input,output):
    data=json.loads(Path(input).read_text());sets={}
    for key in ("science_dlp:2","science_dlp:3"):
        source={}
        for s in data["sets"][key]["sessions"]:
            for p in s["parts"]:
                m=p["source"];source.setdefault(m["source_id"],m)
        sets[key]=allocate(key,list(source.values()))
    Path(output).write_text(json.dumps({"status":"PRIVATE_CONTENT_REVIEW","release_ready":False,"sets":sets},indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main(*sys.argv[1:])
