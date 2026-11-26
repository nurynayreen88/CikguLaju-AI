"""Approved session-first Year 2 Mathematics calendar.
Only selected by a checksum-locked release manifest; all original numbered RPHs remain unchanged.
"""
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json,re
from tools.build_rpt_dlp_native_20261126 import ROOT
from web.school_day_calendar import school_closure
from web.school_days_2027 import FRI_SAT,STATE_LABELS
def calendar_slots(root,subject,year):
    cal=json.loads((root/"pendidikan_moral/induk_minggu_2027_ab.json").read_text())["weeks"]
    states=set(STATE_LABELS.values())
    groups=(FRI_SAT,states-FRI_SAT)
    normal=[60,60,60] if subject=="mathematics_dlp" else [60,30] if year<=3 else [60,60]
    for n,pair in enumerate(zip(cal["A"],cal["B"],strict=True),1):
        if n>38:break
        # Preserve the approved DLP teaching-window exclusions. These are
        # explicit curriculum calendar decisions, not inferred holidays.
        if n in (6,18,19):continue
        available={}
        common=[]
        for group,span,group_states in zip(("A","B"),pair,groups,strict=True):
            start,end=map(date.fromisoformat,(span["start"],span["end"]))
            days=[start+timedelta(days=i) for i in range((end-start).days+1)]
            counts={s:sum(not school_closure(s,d) for d in days) for s in sorted(group_states)}
            available[group]=counts
            common.append(sum(any(not school_closure(s,d) for s in group_states) for d in days))
        # Shared RPT does not deduct state-only holidays for all schools.
        # A session can be placed on any available teaching day; individual
        # schools need actual timetable checking before proposing make-up slots.
        nslots=min(len(normal),*common)
        if not nslots:continue
        # Use the existing approved shorter windows as a conservative baseline.
        # Do not automatically reduce every week containing a public holiday.
        if n in (1,5,20,35) and subject=="mathematics_dlp":
            nslots=min(nslots,2)
        yield n,normal[:nslots],available,pair

def build(subject,year,rows,root=ROOT):
    source=[];review=0
    for c,links in rows:
        m=re.match(r"Lesson\s+(\d+)\b",c[1][0])
        if m:label=f"L{int(m[1]):02d}"
        else:
            assert c[1][0].startswith("Review")
            review+=1;label=f"R{review:02d}"
        duration=int(re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(c[4]),re.I)[0])
        source.append((label,duration,c[1],c[2]))
    assert len({l for l,*_ in source})==len(source)
    planned=[];cursor=0;offset=0;session=0;covered=defaultdict(int)
    for n,slots,days,pair in calendar_slots(root,subject,year):
        sessions=[]
        for duration in slots:
            remaining=duration;parts=[];session+=1
            while remaining and cursor<len(source):
                label,original,title,standards=source[cursor]
                take=min(remaining,original-offset)
                parts.append({"source_id":label,"from_minute":offset,"to_minute":offset+take,"original_minutes":original,"title":title,"standards":standards})
                covered[label]+=take
                remaining-=take;offset+=take
                if offset==original:cursor+=1;offset=0
            sessions.append({"session":session,"minutes":duration,"source_parts":parts,"reserve_minutes":remaining,
                             "status":"CONTENT_REVIEW_REQUIRED" if parts else "RESERVE_NOT_NUMBERED_RPH"})
        planned.append({"week":n,"dates":pair,"available_days_by_state":days,"sessions":sessions})
    assert len(planned)==35,(subject,year,"approved teaching windows",len(planned))
    assert cursor==len(source),(subject,year,"capacity insufficient",cursor,len(source))
    assert dict(covered)=={label:m for label,m,*_ in source}
    assert sum(len(w["sessions"]) for w in planned)==session
    return planned

def candidate_schedule(subject,year,rows,root):
    assert (subject,year)==("mathematics_dlp",2)
    weeks=build(subject,year,rows,root)
    index=0;out=[];loads={};weekly=[];reserve_no=0
    reserve_evidence=[
        'Use a class shop survey to construct and interpret a bar chart. Compare two prices and calculate the total cost of selected items.',
        'Read a pictograph of canteen sales and compare quantities. Use a price list to calculate the change from a given amount of money.',
        'Compare two shopping baskets against a fixed budget. Use a frequency table to justify which items to choose and calculate the balance.',
        'Identify and correct an incorrect bar-chart reading and an incorrect change calculation. Explain both corrections using the given data.',
        'Complete an individual PBD task using a new shop data table: interpret the quantities, compare prices and calculate the total and change. Explain the answers.'
    ]
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
                out.append(([labels,["Reinforcement / PBD follow-up",f"Reserve session {reserve_no+1} — no new standard"],field,[reserve_evidence[reserve_no]],c[4]],links))
                reserve_no+=1
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
    assert len(out)==101 and len(original)==96 and reserve_no==5
    assert all(x[0][1:]==y[0][1:] and x[1]==y[1] for x,y in zip(rows,original,strict=True))
    return out,loads,weekly

