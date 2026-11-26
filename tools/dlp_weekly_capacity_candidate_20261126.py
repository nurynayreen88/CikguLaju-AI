"""Source-locked candidate allocation, shared by future RPT and RPH Pantas.
Never active in production: continuation activities require phase review.
"""
from collections import defaultdict
from datetime import date
import json,re
from pathlib import Path
from hashlib import sha256

def candidate_weeks(subject,year,rows,root):
    root=Path(root)
    path=root/"dlp/audit_weekly_capacity_candidate_20261126.json"
    raw=path.read_bytes()
    plan=json.loads(raw)
    assert plan["status"]=="candidate_not_live"
    p=plan["sets"][f"{subject}:{year}"]
    calendar=json.loads((root/"pendidikan_moral/induk_minggu_2027_ab.json").read_text())["weeks"]
    dates={i:pair for i,pair in enumerate(zip(calendar["A"],calendar["B"],strict=True),1) if i<=38 and i not in (6,18,19)}
    def label(c,review):
        m=re.match(r"Lesson\s+(\d+)\b",c[1][0])
        if m:return f"L{int(m[1]):02d}",review
        assert c[1][0].startswith("Review")
        return f"R{review+1:02d}",review+1
    sources={};review=0
    for c,links in rows:
        key,review=label(c,review)
        duration=re.findall(r"\b(\d+)\s*min(?:utes)?\b"," ".join(c[4]),re.I)
        assert len(duration)==1 and key not in sources
        sources[key]=(c,links,int(duration[0]))
    assert len(sources)==p["source_lessons"]
    assert sum(v[2] for v in sources.values())==p["annual_minutes"]
    assert [w["week"] for w in p["weeks"]]==list(dates)
    parts=defaultdict(list)
    for w in p["weeks"]:
        for l in w["lessons"]:parts[l["id"]].append(l)
    assert list(parts)==list(sources)
    for key,segments in parts.items():
        duration=sources[key][2];cursor=0
        for l in segments:
            assert l["original_minutes"]==duration and l["from_minute"]==cursor
            assert l["minutes"]==l["to_minute"]-cursor>0 and l["minutes"]%30==0
            cursor=l["to_minute"]
        assert cursor==duration
    assert sum(len(v)>1 for v in parts.values())==p["split_lessons"]
    result=[];index=defaultdict(int)
    for w in p["weeks"]:
        n=w["week"];normal=180 if subject=="mathematics_dlp" else 90 if year<=3 else 120
        cap=(120 if subject=="mathematics_dlp" else 60 if year<=3 else 90) if n in (1,5,20,35) else normal
        assert sum(l["minutes"] for l in w["lessons"])==w["minutes"]<=w["capacity"]==cap
        items=[]
        for l in w["lessons"]:
            key=l["id"];c,links,_=sources[key];index[key]+=1
            title=f"{'Lesson' if key.startswith('L') else 'Review'} {key[1:]}"
            part=index[key];count=len(parts[key])
            items.append({**l,"label":title,"display_label":title+(f" (Part {part}/{count})" if count>1 else ""),
                "part":part,"parts":count,"source_cells":c,"source_links":links,
                "requires_activity_review":count>1})
        result.append({"week":n,"dates":dates[n],"capacity":cap,"minutes":w["minutes"],"lessons":items})
    return result,sha256(raw).hexdigest()

def verify():
    import fitz
    from tools.build_rpt_dlp_native_20261126 import ROOT,PINS,extract,document_path
    seen=0;split=0
    for key in PINS:
        subject,y=key.split(":");year=int(y)
        with fitz.open(document_path(subject,year,root=ROOT/"dlp")) as pdf:rows=extract(pdf)
        weeks,digest=candidate_weeks(subject,year,rows,ROOT)
        unique={l["id"] for w in weeks for l in w["lessons"]}
        pending={l["id"] for w in weeks for l in w["lessons"] if l["requires_activity_review"]}
        seen+=len(unique);split+=len(pending)
        print("CAPACITY_SOURCE_OK",key,"unique",len(unique),"phase_review",len(pending),"max_minutes",max(w["minutes"] for w in weeks),flush=True)
    assert seen==701
    print("CAPACITY_GATE",seen,"phase_review",split,"ready_for_release",False,flush=True)
if __name__=="__main__":verify()
