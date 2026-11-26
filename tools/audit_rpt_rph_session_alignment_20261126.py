"""Read-only academic session reconciliation. No live curriculum writes or invented RPH IDs."""
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import json,re
import fitz
from tools.build_rpt_dlp_native_20261126 import PINS,extract,document_path

def slots(minutes):
    assert type(minutes) is int and minutes>0 and minutes%30==0,minutes
    return [60]*(minutes//60)+([30] if minutes%60 else [])

def arabic(root):
    index=json.loads((root/"web/rpt_weekly_suggestions_2027.json").read_text())
    for year in range(2,7):
        weeks=index[f"ARAB:{year}"]; result=[]; ids=[]
        for week,data in sorted(weeks.items(),key=lambda x:int(x[0])):
            sources=data[4][""]
            assert len(sources) in (1,2),(year,week,sources)
            ids.extend(sources)
            # One existing source: two separate candidate sessions; content
            # must be reviewed against actual RPH before approving either.
            sessions=[{"source_pdp":sources[0],"part":1,"minutes":60},
                      {"source_pdp":sources[-1],"part":2 if len(sources)==1 else 1,"minutes":30}]
            assert sum(s["minutes"] for s in sessions)==90
            result.append({"week":int(week),"dates":data[:4],"sessions":sessions})
        assert ids==list(range(1,59 if year==4 else 61))
        yield {"subject":"bahasa_arab","year":year,"source_ids":len(ids),
               "teaching_weeks":len(result),"source_minutes":None,
               "candidate_minutes":sum(s["minutes"] for w in result for s in w["sessions"]),
               "additional_sessions":2*len(result)-len(ids),"weeks":result,
               "status":"RPH_DURATION_AND_CONTENT_REVIEW_REQUIRED"}

def dlp(root):
    for key,pin in PINS.items():
        subject,year=key.split(":");year=int(year)
        path=document_path(subject,year,root=root/"rpt_2027/dlp")
        assert path is not None and sha256(path.read_bytes()).hexdigest()==pin,key
        with fitz.open(path) as pdf: rows=extract(pdf)
        grouped={};all_minutes=0;reviews=0;numbered=[];long=Counter()
        for source_row,(cells,links) in enumerate(rows,1):
            date,lesson,standard,evidence,reference=cells
            label=" ".join(lesson)
            match=re.match(r"Lesson\s+(\d+)\b",label)
            if match:
                numbered.append(int(match[1]))
                source_label=f"Lesson {int(match[1]):02d}"
            else:
                assert label.startswith("Review"),(key,label)
                reviews+=1;source_label=f"Review {reviews:02d}"
            times=re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(reference),re.I)
            assert len(times)==1,(key,source_label,reference)
            minutes=int(times[0]);all_minutes+=minutes
            if minutes>60:long[minutes]+=1
            date_key=tuple(date)
            grouped.setdefault(date_key,[])
            for part,n in enumerate(slots(minutes),1):
                grouped[date_key].append({"source_row":source_row,"source_label":source_label,
                    "part":part,"parts":len(slots(minutes)),"minutes":n,
                    "original_minutes":minutes})
        assert numbered==list(range(1,len(numbered)+1)),key
        weeks=[{"source_dates":list(d),"sessions":sessions,"minutes":sum(s["minutes"] for s in sessions)}
               for d,sessions in grouped.items()]
        assert sum(w["minutes"] for w in weeks)==all_minutes
        assert all(s["minutes"] in (30,60) for w in weeks for s in w["sessions"])
        yield {"subject":subject,"year":year,"source_sha256":pin,
               "source_lessons":len(numbered),"review_rows":reviews,"source_rows":len(rows),
               "source_minutes":all_minutes,"candidate_minutes":all_minutes,
               "candidate_sessions":sum(len(w["sessions"]) for w in weeks),
               "long_sessions":dict(long),"weekly_minutes_histogram":dict(Counter(w["minutes"] for w in weeks)),
               "weeks":weeks,"status":"RPH_CONTENT_AND_WEEKLY_CAPACITY_REVIEW_REQUIRED"}

def teaching_calendar(root):
    calendar=json.loads((root/"rpt_2027/pendidikan_moral/induk_minggu_2027_ab.json").read_text())["weeks"]
    assert len(calendar["A"])==len(calendar["B"])==44
    result=[]
    for n,(a,b) in enumerate(zip(calendar["A"],calendar["B"]),1):
        assert a["week"]==b["week"]==f"M{n:02d}"
        if n<=38 and n not in (6,18,19):
            result.append((n,[a["start"],a["end"],b["start"],b["end"]]))
    assert len(result)==35
    return result

def rebalance_dlp(plan,calendar):
    # Actual timetable slot, not a 150-minute RPH. A slot may contain two
    # different source components; that slot requires a reviewed combined RPH.
    math=plan["subject"]=="mathematics_dlp"
    normal=180 if math else 90 if plan["year"]<=3 else 120
    short=120 if math else 60 if plan["year"]<=3 else 90
    short_weeks={1,5,20,35}
    source_rows={}
    for week in plan["weeks"]:
        for s in week["sessions"]:
            n=s["source_row"]
            entry=source_rows.setdefault(n,{"source_row":n,"source_label":s["source_label"],"minutes":s["original_minutes"]})
            assert entry["minutes"]==s["original_minutes"]
    # Keep source lesson boundaries. Do not combine unrelated 30-minute
    # activities just to fill 60 minutes: existing short RPHs remain intact.
    # Split only the genuinely long source lessons into candidate parts.
    sessions=[]
    for r in source_rows.values():
        offset=0;parts=slots(r["minutes"])
        for part,minutes in enumerate(parts,1):
            sessions.append({"source_row":r["source_row"],"source_label":r["source_label"],
                "original_minutes":r["minutes"],"offset_minutes":offset,"part":part,
                "parts":len(parts),"minutes":minutes,
                "status":"RPH_MATCH_EXISTING" if len(parts)==1 else "DISTINCT_RPH_PART_REVIEW_REQUIRED"})
            offset+=minutes
        assert offset==r["minutes"]
    assert sum(s["minutes"] for s in sessions)==plan["source_minutes"]
    capacity=sum(short if n in short_weeks else normal for n,_ in calendar)
    assert capacity>=plan["source_minutes"],(plan["subject"],plan["year"],capacity)
    # Dynamic programming: preserve order and the source lesson identities.
    # Choose balanced teaching load while leaving unused time explicit.
    # No source sessions are merged. Permit an exceptional 60-min part to
    # become two 30-min parts only if otherwise impossible (reported separately).
    limits=[short if n in short_weeks else normal for n,_ in calendar]
    def allocate(items):
        states={0:(0,[])}
        total=sum(s["minutes"] for s in items)
        cap=0
        for limit in limits:
            cap+=limit;new={}
            target=total*cap/sum(limits)
            prefixes=[0]
            for s in items:prefixes.append(prefixes[-1]+s["minutes"])
            for start,(cost,counts) in states.items():
                for stop in range(start,len(items)+1):
                    used=prefixes[stop]-prefixes[start]
                    if used>limit:break
                    score=cost+(prefixes[stop]-target)**2+3*(limit-used)**2
                    if stop not in new or score<new[stop][0]:
                        new[stop]=(score,counts+[stop-start])
            states=new
        return states.get(len(items))
    answer=allocate(sessions)
    assert answer is not None,(plan["subject"],plan["year"],"source sessions cannot fit without extra split")
    _,counts=answer;new=[];cursor=0;buffer=0
    for (week,dates),limit,count in zip(calendar,limits,counts):
        items=[dict(s,candidate_session=i+1) for i,s in enumerate(sessions[cursor:cursor+count],cursor)]
        cursor+=count;used=sum(s["minutes"] for s in items)
        buffer+=limit-used
        for minutes in slots(limit-used) if limit>used else []:
            items.append({"minutes":minutes,"status":"FLEXIBLE_REINFORCEMENT_OR_REPLACEMENT_NO_RPH_ASSIGNED"})
        assert sum(s["minutes"] for s in items)==limit
        new.append({"week":week,"dates":dates,"planned_minutes":limit,"sessions":items})
    assert cursor==len(sessions) and capacity-buffer==plan["source_minutes"]
    assert [s["source_row"] for w in new for s in w["sessions"] if "candidate_session" in s]==[s["source_row"] for s in sessions]
    return {"subject":plan["subject"],"year":plan["year"],"normal_week_minutes":normal,
       "short_week_minutes":short,"short_weeks":sorted(short_weeks),
       "reserved_weeks":[6,18,19],"last_teaching_week":38,"source_minutes":plan["source_minutes"],
       "timetable_capacity_minutes":capacity,"flexible_minutes_unassigned":buffer,
       "candidate_teaching_sessions":len(sessions),
       "existing_short_rph_candidates":sum(s["parts"]==1 for s in sessions),
       "new_distinct_parts_requiring_review":sum(s["parts"]>1 for s in sessions),
       "combined_slots_requiring_review":0,
       "source_sha256":plan["source_sha256"],"source_rows":list(source_rows.values()),
       "weeks":new,"status":"CANDIDATE_ONLY_RPH_CONTENT_MAPPING_REQUIRED"}

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();root=Path(__file__).resolve().parents[1]
    plans=[*arabic(root),*dlp(root)]
    assert len(plans)==15
    calendar=teaching_calendar(root)
    for plan in plans:
        if plan["subject"]=="bahasa_arab":
            assert [(w["week"],w["dates"]) for w in plan["weeks"]]==calendar
    balanced=[rebalance_dlp(p,calendar) for p in plans if p["subject"]!="bahasa_arab"]
    assert len(balanced)==10
    args.out.write_text(json.dumps({"release_ready":False,"plans":plans,"balanced_dlp":balanced},ensure_ascii=False,indent=2))
    for p in balanced:
        print("BALANCED_DLP",json.dumps({k:v for k,v in p.items() if k not in ("weeks","source_rows")}),flush=True)
    for plan in plans:
        print("SESSION_AUDIT",json.dumps({k:v for k,v in plan.items() if k!="weeks"}),flush=True)

if __name__=="__main__":main()
