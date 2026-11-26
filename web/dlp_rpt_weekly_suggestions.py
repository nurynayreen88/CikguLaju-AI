"""Source-locked DLP RPT weekly suggestions. No guessed RPH IDs."""
from collections import defaultdict
from datetime import date
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]/"rpt_2027"
CODES={"MATH_DLP":"mathematics_dlp","SCIENCE_DLP":"science_dlp"}
COUNTS={("MATH_DLP",2):(78,18),("MATH_DLP",3):(73,9),("MATH_DLP",4):(69,8),("MATH_DLP",5):(61,8),("MATH_DLP",6):(46,8),
        ("SCIENCE_DLP",2):(63,4),("SCIENCE_DLP",3):(52,4),("SCIENCE_DLP",4):(59,10),("SCIENCE_DLP",5):(60,10),("SCIENCE_DLP",6):(52,9)}
MONTH={name:i for i,name in enumerate(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"),1)}
DATE_RE=re.compile(r"([AB])\s*(\d{1,2})\s*([A-Za-z]{3})?\s*[-–—]\s*(\d{1,2})\s*([A-Za-z]{3})\b")

def date_ranges(lines):
    text=" ".join(lines)
    matches=list(DATE_RE.finditer(text))
    assert [m[1] for m in matches]==["A","B"],text
    return tuple((date(2027,MONTH[m[3] or m[5]],int(m[2])),date(2027,MONTH[m[5]],int(m[4]))) for m in matches)

@lru_cache(maxsize=10)
def published_weeks(code,year):
    import fitz
    from tools.build_rpt_dlp_native_20261126 import PINS,extract,document_path
    subject=CODES[code]
    path=document_path(subject,year,root=ROOT/"dlp")
    assert path and sha256(path.read_bytes()).hexdigest()==PINS[f"{subject}:{year}"]
    calendar=json.loads((ROOT/"pendidikan_moral/induk_minggu_2027_ab.json").read_text())["weeks"]
    dates=[tuple((date.fromisoformat(g["start"]),date.fromisoformat(g["end"])) for g in pair)
           for pair in zip(calendar["A"],calendar["B"],strict=True)]
    weeks=defaultdict(list);reserve=defaultdict(int);lesson=review=0
    with fitz.open(path) as pdf:rows=extract(pdf)
    from web.rpt_compact_pdf import dlp_whole_week_release
    if dlp_whole_week_release(ROOT):
        from tools.dlp_whole_lesson_calendar_20261126 import schedule
        rows,_=schedule(subject,year,rows,ROOT)
    for c,_ in rows:
        ranges=date_ranges(c[0])
        matching=[n for n,window in enumerate(dates,1) if all(a<=start<=end<=b for (start,end),(a,b) in zip(ranges,window))]
        assert len(matching)==1,(code,year,ranges)
        if c[1][0]=="Reinforcement / PBD follow-up":
            assert (code,year) in (("MATH_DLP",2),("SCIENCE_DLP",4))
            reserve[matching[0]]+=1
            weeks[matching[0]]  # Reserve only: never invent a numbered RPH ID.
            continue
        title=" ".join(c[1]);match=re.match(r"Lesson\s+(\d+)\b",title)
        if match:
            lesson+=1
            assert int(match[1])==lesson,(code,year,title)
            label=f"Lesson {lesson:02d}"
        else:
            assert title.startswith("Review"),title
            review+=1;label=f"Review {review:02d}"
        weeks[matching[0]].append(label)
    assert (lesson,review)==COUNTS[code,year]
    assert list(weeks)==sorted(weeks)
    return {n:{"labels":labels,"reserve_slots":reserve[n],"dates":[[a.isoformat(),b.isoformat()] for a,b in dates[n-1]]}
            for n,labels in weeks.items()}

def suggestion(code,year,target,group_a):
    if (code,year) not in COUNTS:return None
    try:
        from web import dlp_paired_science_rpt as paired
        if paired.enabled(CODES[code],year):
            return paired.suggestion(ROOT,year,target,group_a,CODES[code])
        weeks=published_weeks(code,year)
        for n,row in weeks.items():
            start,end=row["dates"][0 if group_a else 1]
            if start<=target.isoformat()<=end:
                return {"week":n,"group":"A" if group_a else "B",
                        "lessons":{"":[]},"dlp_labels":row["labels"],"dlp_reserve_slots":row["reserve_slots"]}
    except (OSError,ValueError,AssertionError,ImportError,KeyError):
        # Never recommend a different lesson if a source cannot be verified.
        return None
    return None
