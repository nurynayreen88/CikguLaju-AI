"""Whole-lesson calendar alignment: no new IDs, no removed learning time."""
from collections import Counter
from datetime import date
import json,re
from pathlib import Path

def schedule(subject,year,rows,root):
    calendar=json.loads((Path(root)/"pendidikan_moral/induk_minggu_2027_ab.json").read_text())["weeks"]
    weeks=[(n,a,b) for n,(a,b) in enumerate(zip(calendar["A"],calendar["B"],strict=True),1)
           if n<=38 and n not in (6,18,19)]
    assert len(weeks)==35
    math=subject=="mathematics_dlp"
    normal=180 if math else 90 if year<=3 else 120
    short=120 if math else 60 if year<=3 else 90
    targets=[short if n in (1,5,20,35) else normal for n,_,_ in weeks]
    minutes=[]
    for c,_ in rows:
        values=re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(c[4]),re.I)
        assert len(values)==1,(subject,year,c[1],c[4])
        minutes.append(int(values[0]))
    assert sum(minutes)==(5760 if math else 2880 if year<=3 else 3840)
    assert all(n in (30,60,90,120,150) for n in minutes)
    # Preserve entire lessons and order. Exceptional weeks can use a single
    # extra 30-minute period; do not shorten a long RPH to fit a date boundary.
    prefix=[0]
    for m in minutes:prefix.append(prefix[-1]+m)
    states={0:(0,[])}
    for index,target in enumerate(targets):
        new={}
        for start,(cost,counts) in states.items():
            for stop in range(start+1,len(minutes)+1):
                used=prefix[stop]-prefix[start]
                if used>normal+30:break
                if len(minutes)-stop<len(targets)-index-1:break
                score=cost+((used-target)/30)**2+20*(max(0,used-normal)/30)**2
                if stop not in new or score<new[stop][0]:
                    new[stop]=(score,counts+[stop-start])
        states=new
    assert len(minutes) in states,(subject,year,"whole lesson schedule cannot fit")
    _,counts=states[len(minutes)]
    result=[];loads={};cursor=0
    def format_range(g):
        a=date.fromisoformat(g["start"]);b=date.fromisoformat(g["end"])
        return f"{a.day}-{b.day} {b:%b}" if a.month==b.month else f"{a.day} {a:%b}-{b.day} {b:%b}"
    for (n,a,b),count in zip(weeks,counts,strict=True):
        loads[n]=sum(minutes[cursor:cursor+count])
        for c,links in rows[cursor:cursor+count]:
            result.append(([ [f"Week {n:02d}", "A "+format_range(a),"B "+format_range(b)],*c[1:]],links))
        cursor+=count
    assert cursor==len(rows) and sum(loads.values())==sum(minutes)
    assert all(a[0][1:]==b[0][1:] and a[1]==b[1] for a,b in zip(rows,result,strict=True))
    print("DLP_WHOLE_WEEK",subject,year,"rows",len(rows),"minutes",sum(minutes),
          "histogram",dict(Counter(loads.values())),"extra_period_weeks",[n for n,m in loads.items() if m>normal],flush=True)
    return result,loads
