"""Read-only audit: original DLP source, live schedule, capacity-respecting candidate.
No production files, RPH IDs, lesson content or release manifest changed.
"""
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
import json,re
import fitz
from tools.build_rpt_dlp_native_20261126 import ROOT,PINS,extract,document_path
from tools.dlp_whole_lesson_calendar_20261126 import schedule
from web.dlp_rpt_weekly_suggestions import date_ranges

def audit():
    calendar=json.loads((ROOT/"pendidikan_moral/induk_minggu_2027_ab.json").read_text())["weeks"]
    weeks=[(i,a,b) for i,(a,b) in enumerate(zip(calendar["A"],calendar["B"],strict=True),1) if i<=38 and i not in (6,18,19)]
    dates={i:tuple((date.fromisoformat(g["start"]),date.fromisoformat(g["end"])) for g in (a,b)) for i,a,b in weeks}
    for key in PINS:
        subject,y=key.split(":");year=int(y)
        with fitz.open(document_path(subject,year,root=ROOT/"dlp")) as pdf:
            rows=extract(pdf)
        live,loads=schedule(subject,year,rows,ROOT)
        normal=180 if subject=="mathematics_dlp" else 90 if year<=3 else 120
        short=120 if subject=="mathematics_dlp" else 60 if year<=3 else 90
        entries=[];original=defaultdict(list);actual=defaultdict(list);review=0
        for (c,_),(d,_) in zip(rows,live,strict=True):
            duration=int(re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(c[4]),re.I)[0])
            m=re.match(r"Lesson\s+(\d+)\b",c[1][0])
            if m:label=f"L{int(m[1]):02}"
            else:review+=1;label=f"R{review:02}"
            entries.append((label,duration))
            original[" ".join(c[0])].append((label,duration))
            actual[int(re.search(r"\d+",d[0][0]).group())].append((label,duration))
        # Capacity-respecting comparison only: allocate 30-min units in
        # order, carrying over a long lesson if it spans a week boundary.
        # Prefer remaining weeks for revision rather than inventing lesson IDs.
        # Reserve the original total teaching minutes across all teaching weeks.
        # Use a dynamic program that minimizes splits and deviations from
        # proportionate weekly teaching loads; allow zero only if necessary.
        targets=[short if n in (1,5,20,35) else normal for n,_,_ in weeks]
        total=sum(m for _,m in entries)
        assert sum(targets)>=total,(key,sum(targets),total)
        bounds={0};offset=0
        for _,m in entries:offset+=m;bounds.add(offset)
        dp={0:(0,[])}
        for i,cap in enumerate(targets):
            nxt={}
            remaining=sum(targets[i+1:])
            for used,(score,plan) in dp.items():
                for m in range(30,min(cap,total-used)+1,30):
                    end=used+m
                    if total-end>remaining or total-end<30*(len(targets)-i-1):continue
                    cost=score+(0 if end in bounds else 45)+((m-cap)/30)**2
                    if end not in nxt or cost<nxt[end][0]:nxt[end]=(cost,plan+[m])
            dp=nxt
        assert total in dp,key
        candidate=dp[total][1];pos=0;starts=[];end=0
        for label,m in entries:starts.append((end,end+m,label));end+=m
        print("AUDIT_SET",key,"source_duration_histogram",dict(Counter(m for _,m in entries)),"annual",total,"weekly_cap",normal,"source_date_groups",len(original),"over_cap_weeks",[n for n,v in loads.items() if v>normal],flush=True)
        for (n,_,_),cap,m in zip(weeks,targets,candidate,strict=True):
            end=pos+m
            segments=[(label,min(b,end)-max(a,pos),"continued" if a<pos else "start") for a,b,label in starts if a<end and b>pos]
            assert sum(v for _,v,_ in segments)==m<=cap
            print("AUDIT_WEEK",key,n,"current",actual[n],"cap",cap,"candidate",segments,flush=True)
            pos=end
        assert pos==total
        print("AUDIT_ORIGINAL",key,json.dumps(dict(original),ensure_ascii=False),flush=True)
if __name__=="__main__":audit()
