"""Session-first DLP calendar, private candidate only.
Derive the number of slots from the approved weekly policy and shared school
closures, then map all original source teaching time in order. Do not confuse
source topic IDs with new session IDs or claim unreviewed activities are ready.
"""
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
import json,re
import fitz
from tools.build_rpt_dlp_native_20261126 import ROOT,PINS,extract,document_path
from web.school_day_calendar import school_closure
from web.school_days_2027 import FRI_SAT,STATE_LABELS

def calendar_slots(root,subject,year):
    cal=json.loads((root/"pendidikan_moral/induk_minggu_2027_ab.json").read_text())["weeks"]
    states=set(STATE_LABELS.values())
    groups=(FRI_SAT,states-FRI_SAT)
    normal=[60,60,60] if subject=="mathematics_dlp" else [60,30] if year<=3 else [60,60]
    for n,pair in enumerate(zip(cal["A"],cal["B"],strict=True),1):
        if n>38:break
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
    assert cursor==len(source),(subject,year,"capacity insufficient",cursor,len(source))
    assert dict(covered)=={label:m for label,m,*_ in source}
    assert sum(len(w["sessions"]) for w in planned)==session
    return planned

def main():
    output={"status":"PRIVATE_SESSION_FIRST_CANDIDATE","release_ready":False,"sets":{}}
    for key in PINS:
        subject,y=key.split(":");year=int(y)
        with fitz.open(document_path(subject,year,root=ROOT/"dlp")) as pdf:rows=extract(pdf)
        weeks=build(subject,year,rows)
        sessions=[s for w in weeks for s in w["sessions"]]
        used=sum(s["minutes"]-s["reserve_minutes"] for s in sessions)
        source_count=len({p["source_id"] for s in sessions for p in s["source_parts"]})
        expected=5760 if subject=="mathematics_dlp" else 2880 if year<=3 else 3840
        assert used==expected and source_count==len(rows)
        output["sets"][key]=weeks
        print("SESSION_FIRST_OK",key,"weeks",len(weeks),"slots",len(sessions),"source",source_count,"minutes",used,"reserve_minutes",sum(s["reserve_minutes"] for s in sessions),"weekly_counts",[(w["week"],len(w["sessions"])) for w in weeks],flush=True)
    Path("dlp_session_first_candidate.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":main()
