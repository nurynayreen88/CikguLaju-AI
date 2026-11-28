"""Read-only source-locked fixed-slot plan for all seven outstanding DLP RPTs.

This is a planning/QA artifact, not a release. No new lesson IDs, source
edits, PDF publication, RPH activation or manifest changes.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse,json,re
import fitz
from tools.build_rpt_dlp_native_20261126 import ROOT,PINS,extract,document_path
from tools.dlp_math2_session_calendar_20261126 import build,calendar_slots

SETS=[("mathematics_dlp",y) for y in range(3,7)]+[("science_dlp",y) for y in (2,3,6)]


def optimized_build(subject,year,rows):
    """Allocate 30-minute source atoms without greedily forcing boundaries.

    Preserve source order and all original minutes; minimize cross-source
    slots first and then avoid splitting source blocks where feasible.
    The result is still a review candidate, not a new RPH.
    """
    source=[];review=0;atoms=[]
    for c,_ in rows:
        m=re.match(r"Lesson\s+(\d+)\b",c[1][0])
        if m:label=f"L{int(m[1]):02d}"
        else:review+=1;label=f"R{review:02d}"
        times=re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(c[4]),re.I)
        assert len(times)==1
        duration=int(times[0]);assert duration>0 and duration%30==0
        source.append((label,duration,c[1],c[2]))
        atoms.extend((len(source)-1,offset) for offset in range(0,duration,30))
    calendar=list(calendar_slots(ROOT,subject,year))
    slots=[(n,d) for n,ds,_,_ in calendar for d in ds]
    capacity=sum(d//30 for _,d in slots)
    assert len(atoms)<=capacity
    # DP: exact source minutes and ordered coverage are hard constraints.
    # Minimize mixed-source sessions, then cuts, then partially unused slots.
    # The last term puts reserve capacity near the end when otherwise equal.
    states={0:((0,0,0,0),[])};remaining=capacity
    for ix,(_,duration) in enumerate(slots):
        cap=duration//30;remaining-=cap;new={}
        for cursor,(cost,picks) in states.items():
            for take in range(cap+1):
                stop=cursor+take
                if stop>len(atoms) or len(atoms)-stop>remaining:continue
                chosen=atoms[cursor:stop]
                mixed=int(len({a[0] for a in chosen})>1)
                cut=int(take>0 and 0<stop<len(atoms) and atoms[stop-1][0]==atoms[stop][0])
                partial=int(0<take<cap)
                waste=(cap-take)*(len(slots)-ix)
                score=tuple(a+b for a,b in zip(cost,(mixed,cut,partial,waste),strict=True))
                if stop not in new or score<new[stop][0]:new[stop]=(score,picks+[take])
        states=new
    assert len(atoms) in states
    score,picks=states[len(atoms)]
    cursor=0;session=0;planned=[]
    for n,ds,available,pair in calendar:
        sessions=[]
        for duration in ds:
            take=picks[session];session+=1
            parts=[]
            for row,offset in atoms[cursor:cursor+take]:
                label,original,title,standards=source[row]
                if parts and parts[-1]["source_id"]==label:parts[-1]["to_minute"]+=30
                else:parts.append({"source_id":label,"from_minute":offset,"to_minute":offset+30,"original_minutes":original,"title":title,"standards":standards})
            cursor+=take
            sessions.append({"session":session,"minutes":duration,"source_parts":parts,"reserve_minutes":duration-take*30})
        planned.append({"week":n,"dates":pair,"available_days_by_state":available,"sessions":sessions})
    assert cursor==len(atoms)
    return planned,score

def mixed_count(weeks):
    return sum(len(s["source_parts"])>1 for w in weeks for s in w["sessions"])


def plan(subject,year):
    key=f"{subject}:{year}"
    path=document_path(subject,year,root=ROOT/"dlp")
    assert sha256(path.read_bytes()).hexdigest()==PINS[key]
    with fitz.open(path) as pdf:rows=extract(pdf)
    sources={};review=0
    for c,links in rows:
        m=re.match(r"Lesson\s+(\d+)\b",c[1][0])
        if m:label=f"L{int(m[1]):02d}"
        else:
            assert c[1][0].startswith("Review"),(key,c[1])
            review+=1;label=f"R{review:02d}"
        assert label not in sources
        sources[label]={"title":c[1],"standards":c[2],"learning_evidence":c[3],"textbook_reference":c[4]}
    baseline=build(subject,year,rows,ROOT)
    weeks,score=optimized_build(subject,year,rows)
    assert mixed_count(weeks)<=mixed_count(baseline)
    assert score[0]==mixed_count(weeks)
    expected=list(calendar_slots(ROOT,subject,year))
    assert len(weeks)==len(expected)==35
    counts=Counter(); totals=Counter();seen=Counter()
    for w,(n,slots,days,pair) in zip(weeks,expected,strict=True):
        assert w["week"]==n and w["dates"]==list(pair) or (w["week"]==n and tuple(w["dates"])==tuple(pair))
        assert [s["minutes"] for s in w["sessions"]]==slots
        for s in w["sessions"]:
            parts=s["source_parts"]
            assert sum(p["to_minute"]-p["from_minute"] for p in parts)+s["reserve_minutes"]==s["minutes"]
            for p in parts:
                label=p["source_id"];assert label in sources
                assert p["from_minute"]==totals[label],(key,label,p,totals[label])
                totals[label]+=p["to_minute"]-p["from_minute"]
                seen[label]+=1
                p.update(sources[label])
            if not parts:kind="RESERVE_PBD_REQUIRES_SPECIFIC_ACTIVITY"
            elif len(parts)>1:kind="COMBINED_SOURCE_REQUIRES_ACADEMIC_REVIEW"
            elif parts[0]["from_minute"] or parts[0]["to_minute"]!=parts[0]["original_minutes"]:kind="CONTINUATION_REQUIRES_DISTINCT_ACTIVITY"
            elif s["reserve_minutes"]:kind="EXTENSION_REQUIRES_SPECIFIC_ACTIVITY"
            else:kind="EXACT_SOURCE_SLOT_VERIFY_RPH"
            s["status"]=kind;counts[kind]+=1
    assert set(totals)==set(sources)
    for label,source in sources.items():
        m=re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(source["textbook_reference"]),re.I)
        assert len(m)==1 and totals[label]==int(m[0]),(key,label)
    minutes=sum(totals.values())
    assert minutes==(5760 if subject=="mathematics_dlp" else 2880 if year<=3 else 3840)
    return {"key":key,"baseline_mixed_sessions":mixed_count(baseline),"optimized_mixed_sessions":score[0],"source_boundary_cuts":score[1],"source_sha256":PINS[key],"source_rows":len(sources),"source_minutes":minutes,"teaching_weeks":len(weeks),"sessions":sum(counts.values()),"status_counts":dict(counts),"source_continuations":sum(v>1 for v in seen.values()),"release_ready":False,"weeks":weeks}

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    plans=[plan(*s) for s in SETS]
    assert len(plans)==7
    a.out.write_text(json.dumps({"release_ready":False,"plans":plans},ensure_ascii=False,indent=2)+"\n")
    for row in plans:print("DLP_FIXED_SLOT_PLAN",json.dumps({k:v for k,v in row.items() if k!="weeks"}),flush=True)

if __name__=="__main__":main()
