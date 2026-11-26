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
    boundary_bank=json.loads(Path(__file__).with_name("dlp_science_continuation_open_exit_20261126.json").read_text())["sets"]
    boundary_bank.update(json.loads(Path(__file__).with_name("dlp_mathematics_continuation_open_exit_20261126.json").read_text())["sets"])
    for dataset in drafts["sets"]:
        key=dataset["key"];original=by_key[key]
        lookup={};parts_by_slot={}
        for week in original["weeks"]:
            for s in week["sessions"]:
                parts_by_slot[s["session"]]=s["source_parts"]
                for p in s["source_parts"]:
                    lookup[p["source_id"]]=p
        sessions=[];used_boundary=set();boundary=boundary_bank.get(key,{})
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
            need_open="induction" not in actions[0]["phase"].lower()
            need_exit="closure" not in actions[-1]["phase"].lower()
            entry=boundary.get(str(d["session"]),{})
            if key in boundary_bank:
                assert set(entry)==({"O"} if need_open else set())|({"C"} if need_exit else set()),(key,d["session"],entry,need_open,need_exit)
            if need_open:
                if "O" in entry:
                    teacher,pupils=entry["O"];actions.insert(0,{"source_label":actions[0]["source_label"],"phase":"Set induction","teacher":teacher,"pupils":pupils});used_boundary.add((str(d["session"]),"O"));review.append("AUTHORED_OPENING_DURATION_REVIEW")
                else:review.append("SESSION_OPENING_REVIEW")
            if need_exit:
                if "C" in entry:
                    teacher,pupils=entry["C"];actions.append({"source_label":actions[-1]["source_label"],"phase":"Closure","teacher":teacher,"pupils":pupils});used_boundary.add((str(d["session"]),"C"));review.append("AUTHORED_EXIT_DURATION_REVIEW")
                else:review.append("SESSION_EXIT_REVIEW")
            # Explicit academic workload adaptation for the two most crowded
            # Year 6 Mathematics slots. Retain both original source IDs and
            # the required assessment evidence; shorten redundant examples.
            # These are still teacher-review candidates, not release approval.
            if key=="mathematics_dlp:6" and d["session"] in (52,101):
                if d["session"]==52:
                    assert sources==["L26","L27"],sources
                    actions=[
                        {"source_label":"L26","phase":"Set induction","teacher":"Display two fictional protection cards for insurance and takaful.","pupils":"Identify their shared protective purpose."},
                        {"source_label":"L26","phase":"Practice and assessment","teacher":"Provide one comparison table and two cases: travel medical and house fire. Ask pupils to complete it independently.","pupils":"Distinguish risk transfer from mutual assistance; match each case to suitable coverage and explain one benefit and one coverage limit."},
                        {"source_label":"L26","phase":"Closure","teacher":"Ask pupils to identify a coverage detail to check before relying on a benefit.","pupils":"Name a relevant coverage limit and explain why it matters."},
                        {"source_label":"L27","phase":"Set induction","teacher":"Show a fictional supplier quote with item cost and service charge.","pupils":"Identify both amounts needed for a complete comparison."},
                        {"source_label":"L27","phase":"Modelling","teacher":"Model one worked comparison of two offers including stated charges, hypothetical tax and a later rebate. Distinguish immediate outlay from effective cost.","pupils":"Record and compare both totals with a stated budget and explain the effect of the rebate."},
                        {"source_label":"L27","phase":"Closure","teacher":"Show two fictional complete offers within a RM100 budget.","pupils":"Compare the remaining balances and justify one choice."},
                    ]
                    session_minutes=[3,20,3,3,27,4]
                    objectives=[actions[1]["pupils"],actions[4]["pupils"]]
                else:
                    assert sources==["R08"],sources
                    actions=[
                        {"source_label":"R08","phase":"Set induction","teacher":"Display a 40-response chart with sectors 180°, 90°, 45° and 45°.","pupils":"Check that the angles total 360°."},
                        {"source_label":"R08","phase":"Practice and assessment","teacher":"Set the four-count interpretation task and compare category A with all remaining responses combined.","pupils":"Calculate all four counts and use them to explain the relative likelihood of selecting each category."},
                        {"source_label":"R08","phase":"Targeted reinforcement / PBD","teacher":"Provide a second chart of 24 survey responses with sectors 180°, 90°, 45° and 45°.","pupils":"Interpret the sector counts and justify one likely outcome without treating it as certain."},
                        {"source_label":"R08","phase":"Closure","teacher":"Ask which pair of categories has equal likelihood in the second chart.","pupils":"Identify the equal pair and justify using its counts."},
                    ]
                    session_minutes=[5,30,20,5]
                    objectives=[actions[1]["pupils"],actions[2]["pupils"]]
                evidence=list(objectives)
                assert sum(session_minutes)==d["slot_minutes"]
                for activity,minutes in zip(actions,session_minutes,strict=True):activity["suggested_minutes"]=minutes
            # Science Y2: tighten the scope of actual source tasks, not just
            # the numerical LS mapping. Retain source labels and boundaries.
            if key=="science_dlp:2" and d["session"] in (12,24,25,33,39,46,47):
                corrections={
                    12:(("L11","Main activity","Model measuring hand length from the wrist line to the longest fingertip. Give pairs dated records of two same-age children at two ages and their matching hand outlines.","Measure the outlines, compare the recorded changes in height of both children and conclude that individuals grow differently."),),
                    24:(("L23","Main activity","Guide groups to observe real seeds and seedlings planted earlier. Demonstrate measuring from the support surface to the shoot tip; use the dated germination records and record today's height and leaf count.","Observe the real seeds and seedlings, measure and count leaves, record today's date and findings and compare them with the earlier germination records."),),
                    25:(("L23","Practice and assessment","Return the dated observations of real plants, including germination and today's measurement. Ask each pupil to complete the record and describe the changes.","Record the dates, heights and leaf counts of the observed plants and describe their changes since germination."),),
                    33:(("L31","Main activity","Model a simple shadow guessing game. Give pairs pre-cut card shapes, a torch and a screen; ask them to design two rounds, agree a scoring rule, test and improve the game.","Create a two-round shadow guessing game, agree a scoring rule, play with a partner and improve one unclear silhouette."),),
                    39:(("L37","Main activity","Use a dry-cell circuit with the switch open; remove the switch and demonstrate clipping each of four samples across its position. Supervise each test and reconnect the switch afterward.","Replace the switch with each sample in turn, record whether the bulb lights and restore the original circuit after testing."),),
                    46:(("L43","Main activity","Prepare safe warm and room-temperature water with equal volumes and equal sugar masses. Keep grain size and stirring constant, time both trials and compare the results.","Record the dissolving times and use the results to explain which water temperature makes sugar dissolve faster."),),
                    47:(("L44","Main activity","Keep water temperature, volume and salt mass the same. Stir one cup steadily and leave the other still. Ask groups to observe at the same intervals and compare the recorded outcomes.","Record the visible grains at the same times and explain from the results whether stirring makes salt dissolve faster."),),
                }
                for label,phase,new_teacher,new_pupils in corrections[d["session"]]:
                    matching=[x for x in actions if x["source_label"]==label and x["phase"]==phase]
                    assert len(matching)==1,(key,d["session"],label,phase)
                    activity=matching[0];old=clean(activity["pupils"])
                    activity.update(teacher=new_teacher,pupils=new_pupils)
                    objectives=[new_pupils if x==old else x for x in objectives]
                    evidence=[new_pupils if x==old else x for x in evidence]
                review.append("SCIENCE_Y2_LS_SCOPE_REVISED")
            # Candidate pacing only: preserve all tasks, allocate whole minutes,
            # and explicitly retain review flags for real classroom feasibility.
            # Existing source durations are weights, not a mandate to overrun.
            if not all("suggested_minutes" in x for x in actions):
                original_minutes={(x["source_label"],label_phase(x["phase"]),x["teacher"],x["pupils"]):x["end"]-x["start"] for x in d["activities"]}
                weights=[];minimum=[]
                for x in actions:
                    phase=x["phase"].lower()
                    boundary_phase="induction" in phase or "closure" in phase
                    key4=(x["source_label"],x["phase"],x["teacher"],x["pupils"])
                    old=original_minutes.get(key4)
                    if old is None and reinforcement and x["phase"]==reinforcement["phase"]:old=reinforcement["planned_minutes"]
                    weights.append(max(1,old if old is not None else (5 if boundary_phase else 15)))
                    minimum.append(3 if boundary_phase else 5)
                budget=d["slot_minutes"]-sum(minimum)
                assert budget>=0,(key,d["session"],minimum)
                # Distribute whole minutes by largest remainder, respecting minima.
                adjusted=[max(0,w-m) for w,m in zip(weights,minimum)]
                if not any(adjusted):adjusted=[1]*len(actions)
                denominator=sum(adjusted)
                allocation=[m+budget*w//denominator for m,w in zip(minimum,adjusted)]
                order=sorted(range(len(actions)),key=lambda j:(-(budget*adjusted[j]%denominator),j))
                for j in order[:d["slot_minutes"]-sum(allocation)]:allocation[j]+=1
                for activity,minutes in zip(actions,allocation,strict=True):activity["suggested_minutes"]=minutes
                if sum(weights)>d["slot_minutes"]:review.append("COMPRESSED_ACTIVITY_SCOPE_REVIEW")
            assert sum(x["suggested_minutes"] for x in actions)==d["slot_minutes"],(key,d["session"])
            assert all(x["suggested_minutes"]>0 for x in actions)
            review.append("PACING_CANDIDATE_NOT_ACADEMIC_APPROVAL")
            sessions.append({"session":d["session"],"week":d["week"],"dates":d["dates"],"slot_minutes":d["slot_minutes"],"source_ids":[p["actual_rph_id"] for p in records],"source_labels":sources,"titles":titles,"standards":standards,"references":list(dict.fromkeys(references)),"objective":objectives,"evidence":evidence,"activities":actions,"review":list(dict.fromkeys(review))})
        assert used_boundary=={(n,k) for n,values in boundary.items() for k in values}
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
