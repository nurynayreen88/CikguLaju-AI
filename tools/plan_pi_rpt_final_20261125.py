"""Reconcile all final native PI PdP against existing A/B date windows.
Provisional 60-minute slots only; missing per-row durations are never claimed verified.
No published RPT files or live Web suggestions are altered.
"""
from pathlib import Path
import json
from collections import Counter
from datetime import date

SOURCE=Path("qa/pi-rpt-final-source/records.json")
PRIOR=Path("staging/pendidikan_islam/rpt_2027_prior_calendar_reference_20261125.json")
OUT=Path("qa/pi-rpt-final-source/weekly_candidate.json")
SHORT={1,5,10,20,30,33,35}
CLOSED={6,18,19}
COUNTS={2:112,3:148,4:152,5:144,6:142}

def allocate(records,prior,year):
    windows=sorted((int(w),v) for w,v in prior["weeks"].items())
    assert not ({w for w,v in windows}&CLOSED)
    assert max(w for w,v in windows)<=38
    separate={int(w) for w,m in prior["minutes"].items() if year==2 and m["tasmik"]==60}
    if year==2:
        assert len(separate)==32
    # Provisional plan: one 60-minute slot per native PdP. T2 retains separate
    # additional Tasmik slots from previous candidate; T3–6 native recitation
    # sessions are counted as Tasmik, not twice.
    dp={0:(0,[])}
    target=0
    for w,window in windows:
        old=len(window[4][""])
        target+=old
        cap=4 if w in SHORT else 5
        available=cap-int(w in separate)
        nxt={}
        for start,(cost,plan) in dp.items():
            for count in range(min(available,len(records)-start)+1):
                end=start+count
                if count==0 and w in separate:
                    continue
                newcost=cost+abs(end-target)+3*abs(count-old)
                if end not in nxt or newcost<nxt[end][0]:
                    nxt[end]=(newcost,plan+[count])
        dp=nxt
    if len(records) not in dp:
        raise ValueError(f"T{year} does not fit provisional caps; do not publish")
    result={}
    cursor=0
    for (w,window),count in zip(windows,dp[len(records)][1]):
        batch=records[cursor:cursor+count]
        cursor+=count
        tasmik_ids=[x["pdp"] for x in batch if x["recitation"] and year!=2]
        teaching=[x["pdp"] for x in batch if x["pdp"] not in tasmik_ids]
        tasmik=60*(len(tasmik_ids)+int(w in separate))
        pi=60*len(teaching)
        assert pi+tasmik <= (240 if w in SHORT else 300)
        assert all(date.fromisoformat(d).year==2027 for d in window[:4])
        result[str(w)]={"dates":window[:4],"pdp":[x["pdp"] for x in batch],"teaching_pdp":teaching,"tasmik_pdp":tasmik_ids,"teaching_minutes_provisional":pi,"tasmik_minutes_provisional":tasmik,"separate_tasmik_provisional":w in separate}
    assert [n for r in result.values() for n in r["pdp"]]==list(range(1,COUNTS[year]+1))
    teaching=sum(r["teaching_minutes_provisional"] for r in result.values())
    tasmik=sum(r["tasmik_minutes_provisional"] for r in result.values())
    assert teaching>=96*60 and tasmik>=32*60
    return {"weekly":result,"teaching_minutes_provisional":teaching,"tasmik_minutes_provisional":tasmik,"count":cursor,"last_week":max(int(w) for w,r in result.items() if r["pdp"]),"max_combined_minutes":max(r["teaching_minutes_provisional"]+r["tasmik_minutes_provisional"] for r in result.values())}

def main():
    src=json.loads(SOURCE.read_text(encoding="utf8"))
    prior=json.loads(PRIOR.read_text(encoding="utf8"))
    out={"status":"PROVISIONAL_DURATION_NOT_FOR_PUBLICATION","source_commit":src["source_commit"],"calendar_reference":prior["source"],"duration_assumption":"60 minutes per native PdP until exact previous source duration identity is checked; T2 extra 32 Tasmik slots retained; T3–6 native recitation counted separately.","years":{}}
    for year,count in COUNTS.items():
        rows=[x for x in src["records"] if x["year"]==year]
        assert len(rows)==count
        data=allocate(rows,prior["years"][f"PI:{year}"],year)
        out["years"][str(year)]=data
        print("PI_RPT_CANDIDATE",year,json.dumps({k:v for k,v in data.items() if k!="weekly"}),flush=True)
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    # Teacher-facing projection: date windows and PdP identities only.
    # Keep provisional capacity assumptions in the separate internal report.
    public={"status":"RPT_DISPLAY_CANDIDATE_NOT_PUBLISHED","source_commit":src["source_commit"],"years":{}}
    for year,data in out["years"].items():
        public["years"][year]={"count":data["count"],"weeks":{w:{"dates":v["dates"],"pdp":v["pdp"],"tasmik_pdp":v["tasmik_pdp"],"separate_tasmik":v["separate_tasmik_provisional"]} for w,v in data["weekly"].items()}}
    (OUT.parent/"teacher_schedule.json").write_text(json.dumps(public,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("PI_RPT_CANDIDATE_TOTAL",sum(x["count"] for x in out["years"].values()),flush=True)

if __name__=="__main__":
    main()
