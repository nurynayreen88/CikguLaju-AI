"""Fixed two 60-minute sessions for Science Year 4/5, preserving all source IDs."""
import json,re
from pathlib import Path
from datetime import date
from tools.dlp_math2_session_calendar_20261126 import calendar_slots
def schedule(subject,year,rows,root):
    assert subject=="science_dlp" and year in (4,5)
    assert len(rows)==(69 if year==4 else 70)
    out=[];loads={};i=0;short=0
    def label(g):
        a,b=map(date.fromisoformat,(g["start"],g["end"]))
        return f"{a.day}-{b.day} {b:%b}" if a.month==b.month else f"{a.day} {a:%b}-{b.day} {b:%b}"
    for n,slots,available,pair in calendar_slots(root,subject,year):
        assert slots==[60,60]
        labels=[f"Week {n:02d}","A "+label(pair[0]),"B "+label(pair[1])]
        loads[n]=120
        for _ in slots:
            if i<len(rows):
                c,links=rows[i];i+=1
                minutes=int(re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(c[4]),re.I)[0])
                assert minutes in (30,60)
                short+=minutes==30
                out.append(([labels,*c[1:]],links))
            else:
                assert year==4 and n==38 and len(out)==69
                c,links=rows[-1]
                codes=json.loads((Path(root)/"dlp/standard_descriptions/review_mappings.json").read_text())["mappings"]["science_dlp:4"]["R10"]
                out.append(([labels,["Reinforcement / PBD follow-up","Reserve session — no new standard"],["LS "+", ".join(codes)],["Compare two simple-machine arrangements, explain how they reduce effort and justify a choice using observations from a familiar tool."],c[4]],links))
    assert i==len(rows) and len(out)==70 and len(loads)==35
    assert short==(10 if year==4 else 12)
    assert all(a[0][1:]==b[0][1:] and a[1]==b[1] for a,b in zip(rows,out[:i],strict=True))
    return out,loads
