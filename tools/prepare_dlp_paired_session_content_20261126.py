"""Prepare matching native RPH/RPT review data, not a production release.

The source activities remain verbatim and appear exactly once. The objective
and evidence are the concrete pupil task in the selected activity rather
than a repeated whole-parent objective. Standards are source references
until the continuation scope has been academically verified.
"""
from pathlib import Path
from collections import Counter
import argparse,json,re

def clean(s):
    return " ".join(s.split())

def label_phase(s):
    return re.sub(r"\s*·\s*\d+\s*min(?:it)?$","",s)

def prepare(crosswalk,drafts):
    by_key={p["key"]:p for p in crosswalk["plans"]};output=[]
    for dataset in drafts["sets"]:
        key=dataset["key"];original=by_key[key]
        lookup={};parts_by_slot={}
        for week in original["weeks"]:
            for s in week["sessions"]:
                parts_by_slot[s["session"]]=s["source_parts"]
                for p in s["source_parts"]:
                    lookup[p["source_id"]]=p
        sessions=[]
        for d in dataset["draft_sessions"]:
            parts=parts_by_slot[d["session"]]
            reinforcement=d["targeted_reinforcement"]
            sources=list(dict.fromkeys([p["source_id"] for p in parts]+([reinforcement["source_label"]] if reinforcement else [])))
            records=[lookup[l] for l in sources]
            assert records,(key,d["session"])
            actions=[{"source_label":p["source_label"],"phase":label_phase(p["phase"]),"teacher":p["teacher"],"pupils":p["pupils"]} for p in d["activities"]]
            if reinforcement:
                item={k:reinforcement[k] for k in ("source_label","phase","teacher","pupils")}
                # Reinforcement comes before the closure of its own lesson;
                # otherwise append it after the retained source phases.
                i=len(actions)
                if actions and actions[-1]["source_label"]==item["source_label"] and "closure" in actions[-1]["phase"].lower():i-=1
                actions.insert(i,item)
            assert actions,(key,d["session"],"no activity")
            # Source-specific objective/evidence: select each source's own
            # assessment or last substantive pupil task in this session.
            objectives=[];evidence=[]
            for label in sources:
                subset=[x for x in actions if x["source_label"]==label]
                if not subset:continue
                assessment=[x for x in subset if "assessment" in x["phase"].lower() or "reinforcement" in x["phase"].lower() or "pbd" in x["phase"].lower()]
                substantive=[x for x in subset if "induction" not in x["phase"].lower() and "closure" not in x["phase"].lower()]
                selected=assessment or substantive[-1:] or subset[-1:]
                for x in selected:
                    task=clean(x["pupils"])
                    if task not in objectives:objectives.append(task);evidence.append(task)
            assert objectives
            units=[];titles=[];standards=[];references=[]
            for p in records:
                titles.append(p["source_id"]+": "+clean(" ".join(p["title"])))
                standards.append(p["standards"])
                references.extend(x for x in p["textbook_reference"] if not re.fullmatch(r"\d+\s*min(?:utes)?",x.strip(),re.I))
                units.extend(x for x in p["title"] if x.startswith("Unit "))
            review=list(d["review"])
            # A complete original induction and closure may be reused, but
            # a continuation requires its own reviewed opening/exit task.
            # Do not silently invent or duplicate activities to force them.
            if "induction" not in actions[0]["phase"].lower():review.append("SESSION_OPENING_REVIEW")
            if "closure" not in actions[-1]["phase"].lower():review.append("SESSION_EXIT_REVIEW")
            sessions.append({"session":d["session"],"week":d["week"],"dates":d["dates"],"slot_minutes":d["slot_minutes"],"source_ids":[p["actual_rph_id"] for p in records],"source_labels":sources,"titles":titles,"standards":standards,"references":list(dict.fromkeys(references)),"objective":objectives,"evidence":evidence,"activities":actions,"review":list(dict.fromkeys(review))})
        assert len(sessions)==dataset["sessions"]
        counts=Counter(x for s in sessions for x in s["review"])
        output.append({"key":key,"sessions":sessions,"review_counts":dict(counts),"release_ready":False})
        print("PAIRED_RPT_RPH_CONTENT",key,len(sessions),"specific_objectives",sum(len(s["objective"]) for s in sessions),"review_counts",dict(counts),flush=True)
    assert sum(len(s["sessions"]) for s in output)==614
    return {"release_ready":False,"sets":output}

def main():
    a=argparse.ArgumentParser();a.add_argument("--crosswalk",type=Path,required=True);a.add_argument("--drafts",type=Path,required=True);a.add_argument("--out",type=Path,required=True);args=a.parse_args()
    result=prepare(json.loads(args.crosswalk.read_text()),json.loads(args.drafts.read_text()))
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":main()
