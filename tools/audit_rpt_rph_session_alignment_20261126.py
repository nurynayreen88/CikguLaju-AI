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
    # Latest owner decision: durations are INTERNAL workload guides, not
    # printed lesson durations or mandatory new RPH IDs. Keep every source's
    # entire teaching time. Prefer keeping a source together; permit it to
    # continue across weeks only where needed. Never combine unrelated sources.
    atoms=[(r["source_row"],offset) for r in source_rows.values()
           for offset in range(0,r["minutes"],30)]
    limits=[short if n in short_weeks else normal for n,_ in calendar]
    capacity=sum(limits)
    assert len(atoms)*30==plan["source_minutes"]<=capacity
    # Optimize weekly load and penalize cutting an existing lesson boundary.
    # Work in 30-minute units; the original RPH remains the parent identity.
    states={0:(0,[])};cap=0
    for limit in limits:
        cap+=limit;new={}
        target=len(atoms)*cap/capacity
        for start,(cost,counts) in states.items():
            for stop in range(start,min(len(atoms),start+limit//30)+1):
                cut=0<stop<len(atoms) and atoms[stop-1][0]==atoms[stop][0]
                score=cost+(stop-target)**2+3*(limit//30-(stop-start))**2+100*cut
                if stop not in new or score<new[stop][0]:
                    new[stop]=(score,counts+[stop-start])
        states=new
    assert len(atoms) in states,(plan["subject"],plan["year"])
    _,counts=states[len(atoms)]
    new=[];cursor=0;buffer=0;source_totals=Counter();source_weeks=defaultdict(set)
    for (week,dates),limit,count in zip(calendar,limits,counts):
        picked=atoms[cursor:cursor+count];cursor+=count
        items=[]
        for row,offset in picked:
            source=source_rows[row]
            if items and items[-1]["source_row"]==row:
                items[-1]["internal_minutes"]+=30
            else:
                items.append({"source_row":row,"source_label":source["source_label"],
                              "original_minutes":source["minutes"],"offset_minutes":offset,
                              "internal_minutes":30,"status":"RPH_SOURCE_MATCH_REQUIRED"})
            source_totals[row]+=30;source_weeks[row].add(week)
        used=count*30;buffer+=limit-used
        new.append({"week":week,"dates":dates,"internal_capacity_minutes":limit,
                    "internal_teaching_minutes":used,"flexible_unassigned_minutes":limit-used,
                    "lesson_blocks":items})
    assert cursor==len(atoms) and capacity-buffer==plan["source_minutes"]
    assert dict(source_totals)=={k:v["minutes"] for k,v in source_rows.items()}
    split={row for row,weeks in source_weeks.items() if len(weeks)>1}
    for w in new:
        for item in w["lesson_blocks"]:
            row=item["source_row"]
            if row in split:
                item["status"]="CONTINUATION_REQUIRES_DISTINCT_ACTIVITY_REVIEW"
            elif item["internal_minutes"]>60:
                item["status"]="LONG_LESSON_REVIEW_FOR_ACTUAL_TIMETABLE_SESSIONS"
            else:
                item["status"]="RETAIN_EXISTING_RPH_IF_CONTENT_MATCHES"
    return {"subject":plan["subject"],"year":plan["year"],"normal_week_minutes":normal,
       "short_week_minutes":short,"short_weeks":sorted(short_weeks),
       "reserved_weeks":[6,18,19],"last_teaching_week":38,"source_minutes":plan["source_minutes"],
       "timetable_capacity_minutes":capacity,"flexible_minutes_unassigned":buffer,
       "source_lessons_preserved":len(source_rows),
       "source_lessons_spanning_weeks":len(split),
       "long_source_lessons_needing_activity_review":sum(r["minutes"]>60 for r in source_rows.values()),
       "source_sha256":plan["source_sha256"],"source_rows":list(source_rows.values()),
       "weeks":new,"status":"INTERNAL_GUIDE_ONLY_RPH_CONTENT_MAPPING_REQUIRED"}

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
