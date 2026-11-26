"""Build reviewable distinct session activity drafts from actual source phases.

Never split activity text by minute, repeat a phase, invent an RPH identifier,
or publish candidate content. Report timing deviations and reserve/combined
sessions explicitly for academic review.
"""
from collections import defaultdict,Counter
from pathlib import Path
from functools import lru_cache
import argparse,json

def partition(phases,parts):
    targets=[p["to_minute"]-p["from_minute"] for p in parts]
    assert sum(targets)==sum(x["end"]-x["start"] for x in phases)
    # Each original complete phase goes to exactly one consecutive slot.
    # Prefer nonempty parts, then least overrun, then closest timing.
    @lru_cache(None)
    def solve(i,j):
        if i==len(targets):return ((0,0,0),()) if j==len(phases) else None
        best=None
        for stop in range(j,len(phases)+1):
            tail=solve(i+1,stop)
            if tail is None:continue
            used=sum(x["end"]-x["start"] for x in phases[j:stop])
            here=(int(stop==j),max(0,used-targets[i]),abs(used-targets[i]))
            score=tuple(a+b for a,b in zip(here,tail[0]))
            candidate=(score,(stop,*tail[1]))
            if best is None or candidate<best:best=candidate
        return best
    _,stops=solve(0,0)
    cursor=0
    for p,stop,target in zip(parts,stops,targets,strict=True):
        activities=phases[cursor:stop];cursor=stop
        p["candidate_activities"]=activities
        p["candidate_activity_minutes"]=sum(x["end"]-x["start"] for x in activities)
        p["allocated_source_minutes"]=target
        p["timing_delta_minutes"]=p["candidate_activity_minutes"]-target
    assert cursor==len(phases)
    assert [a for p in parts for a in p["candidate_activities"]]==phases

def create(plan):
    by_source=defaultdict(list);phases_by_source=defaultdict(dict)
    for w in plan["weeks"]:
        for s in w["sessions"]:
            for p in s["source_parts"]:
                label=p["source_id"];by_source[label].append(p)
                for phase in p["source_activity_matches"]:
                    phase={k:v for k,v in phase.items() if k!="whole_phase"}
                    old=phases_by_source[label].setdefault(phase["start"],phase)
                    assert old==phase
    assert not plan["rph_source_match"]["source_issues"]
    for label,parts in by_source.items():
        phases=sorted(phases_by_source[label].values(),key=lambda p:p["start"])
        assert phases[0]["start"]==0 and phases[-1]["end"]==parts[0]["original_minutes"]
        assert all(a["end"]==b["start"] for a,b in zip(phases,phases[1:]))
        partition(phases,parts)
    counts=Counter();drafts=[]
    for w in plan["weeks"]:
        for s in w["sessions"]:
            parts=s["source_parts"]
            activities=[]
            for p in parts:
                for phase in p["candidate_activities"]:
                    activities.append({"source_id":p["actual_rph_id"],"source_label":p["source_id"],**phase})
            total=sum(x["end"]-x["start"] for x in activities)
            issues=[]
            if not parts:issues.append("RESERVE_SPECIFIC_PBD_REQUIRED")
            if len(parts)>1:issues.append("COMBINED_OBJECTIVE_AND_PBD_REVIEW")
            if any(not p["candidate_activities"] for p in parts):issues.append("EMPTY_SOURCE_PART_REVIEW")
            if any(p["from_minute"] or p["to_minute"]!=p["original_minutes"] for p in parts):issues.append("CONTINUATION_OBJECTIVE_AND_CLOSURE_REVIEW")
            if total>s["minutes"]:issues.append("ACTIVITY_TIMING_REVIEW")
            if total<s["minutes"]:issues.append("UNALLOCATED_TIME_REVIEW")
            if any(p["timing_delta_minutes"] for p in parts):issues.append("SOURCE_BOUNDARY_TIMING_REVIEW")
            if not issues:issues.append("EXACT_SOURCE_RETAIN")
            counts.update(issues)
            drafts.append({"week":w["week"],"dates":w["dates"],"session":s["session"],"slot_minutes":s["minutes"],"source_ids":[p["actual_rph_id"] for p in parts],"source_standards":[p["standards"] for p in parts],"source_evidence":[p["learning_evidence"] for p in parts],"source_references":[p["textbook_reference"] for p in parts],"activities":activities,"original_activity_minutes":total,"review":issues})
    assert len(drafts)==plan["sessions"]
    assert sum(d["original_activity_minutes"] for d in drafts)==plan["source_minutes"]
    original=[(label,p["start"],p["end"],p["teacher"],p["pupils"]) for label,phases in phases_by_source.items() for p in phases.values()]
    actual=[(p["source_label"],p["start"],p["end"],p["teacher"],p["pupils"]) for d in drafts for p in d["activities"]]
    assert Counter(original)==Counter(actual)
    result={"key":plan["key"],"source_rows":len(by_source),"sessions":len(drafts),"original_phases_preserved":len(actual),"review_counts":dict(counts),"release_ready":False,"draft_sessions":drafts}
    print("DLP_DISTINCT_ACTIVITY_DRAFT",json.dumps({k:v for k,v in result.items() if k!="draft_sessions"}),flush=True)
    return result

def main():
    a=argparse.ArgumentParser();a.add_argument("--crosswalk",type=Path,required=True);a.add_argument("--out",type=Path,required=True);args=a.parse_args()
    data=json.loads(args.crosswalk.read_text())
    results=[create(plan) for plan in data["plans"]]
    assert len(results)==7 and sum(p["sessions"] for p in results)==614
    args.out.write_text(json.dumps({"release_ready":False,"sets":results},ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":main()
