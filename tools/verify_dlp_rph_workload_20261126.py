"""Verify actual DLP RPH source workloads and display text without altering approved activities."""
from collections import Counter
import re
from dlp_year2_rph import catalog, year3_science_catalog, _rph_display_rows
from staging.dlp.year2.science_flexible_delivery import SCIENCE_SHORT_PREPARATION
from staging.dlp.year2.downloads import BY_SUBJECT
from staging.dlp.year3 import render_mathematics as m3
from staging.dlp.year4 import render_mathematics as m4, render_science as s4
from staging.dlp.year5 import render_mathematics as m5, render_science as s5
from staging.dlp.year6 import render_mathematics as m6, render_science as s6

TIME=re.compile(r"(?: · |\n)(\d+) min(?:it)?$")
EXPECTED={
 ("math",2):(96,5760),("science",2):(67,2880),
 ("math",3):(82,5760),("science",3):(56,2880),
 ("math",4):(77,5760),("science",4):(69,3840),
 ("math",5):(69,5760),("science",5):(70,3840),
 ("math",6):(54,5760),("science",6):(61,3840),
}

def phase_rows(phases):
    return [(f"{p['phase']} · {p['minutes']} min",p["teacher"],p["pupils"]) if isinstance(p,dict) else tuple(p) for p in phases]

def minutes(phases):
    return sum(int(TIME.search(p[0])[1]) for p in phase_rows(phases))

def plans():
    for code,sub in (("MATH_DLP","math"),("SCIENCE_DLP","science")):
        yield (sub,2),[(x["id"],x["numbered_label"],x["phases"],x["minutes"]) for u in BY_SUBJECT[code].units for x in u["lessons"]]
    yield ("science",3),[(x["id"],x["numbered_label"],x["phases"],x["minutes"]) for u in year3_science_catalog() for x in u["lessons"]]
    yield ("math",3),[(i,label,phases,int(duration.split()[0])) for i,_,_,label,_,duration,_,phases in m3.verify_drafts()]
    yield ("math",4),[(i,label,phases,int(details["Duration"].split()[0])) for i,_,_,label,details,phases in m4.verify_drafts()]
    yield ("science",4),[(p["id"],p["label"],p["phases"],p["minutes"]) for p in s4.load_plans()]
    for key,module in ((("math",5),m5),(("science",5),s5),(("math",6),m6),(("science",6),s6)):
        _,data=module.load_plans()
        yield key,[(p["id"],p["label"],p["phases"],p["minutes"]) for p in data]

def verify():
    from io import BytesIO
    from docx import Document
    import fitz
    original={l['id']:l for u in catalog()['SCIENCE_DLP'] for l in u['lessons']}
    seen_short=set()
    for unit in BY_SUBJECT['SCIENCE_DLP'].units:
        for lesson in unit['lessons']:
            if lesson['id'] not in original or lesson['minutes']!=30:continue
            old=original[lesson['id']];number=str(int(lesson['numbered_label'].split()[-1]));seen_short.add(number)
            assert lesson['objective']==old['objective'] and lesson['standards']==old['standards']
            assert all(a[2]==b[2] for a,b in zip(lesson['phases'],old['phases'],strict=True))
            assert all(a[1].endswith(b[1]) for a,b in zip(lesson['phases'],old['phases'],strict=True))
            teacher={'class':'2 Bestari','time':'08:00 - 08:30','date':'2027-01-12','students':'25'}
            pdf=BY_SUBJECT['SCIENCE_DLP'].render_download(lesson,'pdf',teacher)
            word=BY_SUBJECT['SCIENCE_DLP'].render_download(lesson,'word',teacher)
            with fitz.open(stream=pdf,filetype='pdf') as doc:
                assert len(doc)==1,(number,'PDF pagination')
            assert len(Document(BytesIO(word)).tables)==4,(number,'Word layout')
    assert seen_short==set(SCIENCE_SHORT_PREPARATION) and len(seen_short)==34
    print('SCIENCE_Y2_34_ADAPTATIONS_RENDERED',flush=True)
    seen=set(); blockers=[]
    for key,rows in plans():
        seen.add(key)
        assert (len(rows),sum(p[3] for p in rows))==EXPECTED[key],key
        assert len({p[0] for p in rows})==len(rows),key
        counts=Counter()
        for identifier,label,phases,duration in rows:
            phases=phase_rows(phases)
            original_phase_minutes=minutes(phases)
            if original_phase_minutes!=duration:
                blockers.append((key,identifier,duration,original_phase_minutes))
            assert all(p[1].strip() and p[2].strip() for p in phases),(key,identifier)
            fields,display=_rph_display_rows([("Lesson / PdP",label),("Time","08:00 - 09:00")],[("Phase","Teacher","Pupils"),*phases])
            assert fields[1]==("Time","08:00 - 09:00")
            assert not TIME.search(fields[0][1])
            assert [p[1:] for p in display[1:]]==[p[1:] for p in phases]
            assert all(not TIME.search(p[0]) for p in display)
            if duration==150:assert len(phases)>=5,(key,identifier)
            counts[duration]+=1
        print("DLP_RPH_SOURCE_OK",key,len(rows),dict(counts),flush=True)
    assert seen==set(EXPECTED)
    for item in blockers:
        print("DLP_WORKLOAD_REVIEW_REQUIRED",item,flush=True)
    print("DLP_WORKLOAD_AUDIT",{"source_sets":len(seen),"phase_mismatch_count":len(blockers),"release_ready":not blockers},flush=True)
    # Audit inventory can succeed with explicit academic review blockers.
    # Do not use this workflow as a curriculum release approval.

if __name__=="__main__":verify()
