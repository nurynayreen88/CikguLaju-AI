"""Read-only English RPH text audit: Years 1–6 inventory, Years 2–6 SOW QA.

This script does NOT import app.py, modify databases, enable RPH releases, or
prove book/audio or Telegram delivery. Year 1 remains separately subject to KP2027.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"rph_standalone"/"english"
SOW=ROOT/"audits"/"english_primary_2_6_official_sow_index_20261103.json"
OUTPUT=ROOT/"output"/"english_full_rph_text_audit_20261104.json"
LS=re.compile(r"(?<!\d)[1-5]\.\d\.\d(?!\d)")
GENERIC={
  "complete_lesson_activities":r"complete the lesson activities",
  "practise_both_skills":r"practise both skills",
  "complete_referenced_tasks":r"complete the referenced tasks",
  "revisit_common_errors":r"revisit common errors in the unit",
  "generic_exit_response":r"one accurate new sentence or fact",
  "generic_topic_question":r"what can you say about this topic",
}
PHASE_TIME=re.compile(r"(?im)^\s*(?:##\s*|\d+\.\s*(?:\*\*)?|\*\*)(?:set induction|activity\s*[1-9]|reinforcement|pbd|assessment|closure)[^\n]{0,120}?\((\d+)\s*(?:minutes|min)\)")
OBJ=re.compile(r"(?im)^\s*(?:\*\*)?(?:learning objectives?|objectives?|objektif)(?:\b|\s*\()")

def extract_phase(t,word):
    key={"start":r"set induction|set induksi","end":r"closure|penutup"}[word]
    m=re.search(r"(?im)^\s*(?:##\s*|\*\*)(?:"+key+r")\b[^\n]*",t)
    if not m:return ""
    s=t[m.end():]
    nxt=re.search(r"(?m)^\s*(?:##\s+|\*\*(?:Activity|PBD|Assessment|Reinforcement|Closure|Workbook|Differentiation))",s)
    text=s[:nxt.start()] if nxt else s[:340]
    return re.sub(r"\s+"," ",text).strip()[:280]

def inspect(y,n,body,record):
    first=body.splitlines()[0] if body.splitlines() else ""
    header=body[:min(1600,body.find("\n## ") if "\n## " in body else 1600)]
    codes=LS.findall(header)
    fixed=bool(record and not record["teacher_selected"])
    standards=[record["main_ls"],record["complementary_ls"]] if fixed else []
    matched=all(z in codes for z in standards)
    time=[int(m) for m in PHASE_TIME.findall(body)]
    total=sum(time) if len(time)>=4 else None
    generic=[key for key,pattern in GENERIC.items() if re.search(pattern,body,re.I)]
    title=bool(re.search(r"\bLesson\s+0*"+str(n)+r"\b",first,re.I))
    start=bool(re.search(r"\bset induction\b|\bset induksi\b",body,re.I))
    end=bool(re.search(r"\bclosure\b|\bpenutup\b",body,re.I))
    assessment=bool(re.search(r"\bPBD\b|\bassessment\b|\bpenilaian\b",body,re.I))
    hard=[]
    if not title:hard.append("wrong_lesson_title")
    if fixed and not matched:hard.append("sow_header_pair_mismatch")
    if not (start and end and assessment):hard.append("missing_teaching_phase")
    if total is not None and total!=60:hard.append("timing_not_60_minutes")
    if record and record["teacher_selected"] and not re.search(r"pilihan guru|teacher.selected|teacher choice|selected by the teacher|selection to teacher|teacher selects|teacher chooses|selected from pupils",header,re.I):hard.append("teacher_choice_not_labelled")
    quality=[]
    if not OBJ.search(body):quality.append("missing_explicit_objective_header")
    if not re.search(r"\bteacher\b",body,re.I):quality.append("teacher_actions_not_identified")
    if not re.search(r"\bpupils?\b|\bmurid\b",body,re.I):quality.append("pupil_actions_not_identified")
    if re.search(r"(?i)\*\*(?:Main|Complementary)\s+SK/SP[^\n]*SOW verification pending",header):quality.append("stale_sow_verification_pending_header")
    if generic:quality.append("generic_instruction")
    if total is None:quality.append("phase_minutes_not_extractable")
    if len(body)<1000:quality.append("source_under_1000_chars")
    return {
        "lesson":n,"length":len(body),"fixed_sow":fixed,
        "teacher_choice":bool(record and record["teacher_selected"]),
        "sow_expected":standards,"sow_header_pair_match":matched if fixed else None,
        "phase_minutes":time,"phase_minute_sum":total,
        "objective_header":bool(OBJ.search(body)),
        "book_reference":bool(re.search(r"student.s book|pupil.s book|teacher.s book|\b(?:SB|PB|TB)\s*p",body,re.I)),
        "workbook_reference":bool(re.search(r"workbook|activity book",body,re.I)),
        "audio_reference":bool(re.search(r"\b(?:CD\s*[1-3]|track\s*\d+|audio|WMA|MP3)\b",body,re.I)),
        "internal_review_notes_in_source":bool(re.search(r"\b(?:QA|NOT READY|DRAF|DRAFT)\b",body,re.I)),
        "generic_signals":generic,"hard_issues":hard,"quality_flags":quality,
        "opening":extract_phase(body,"start"),"closure":extract_phase(body,"end")
    }

def audit():
    index=json.loads(SOW.read_text(encoding="utf-8"))["lessons"]
    report={"audit":"English Years 1–6 RPH source text 2026-11-04",
            "scope":"Year1 inventory only; Year2–6 cross-check against 800-row SOW index",
            "final_pedagogy_verified":False,"real_telegram_delivery_verified":False,
            "spoken_audio_verified":False,"years":{}}
    hard_total=0
    for y in range(1,7):
        folder=SRC/f"year{y}"
        missing=[];entries=[]
        for n in range(1,161):
            path=folder/f"lesson_{n:03d}.md"
            if not path.is_file():missing.append(n);continue
            record=index[f"{y}/{n}"] if y>=2 else None
            entries.append(inspect(y,n,path.read_text(encoding="utf-8-sig"),record))
        unexpected=sorted(p.name for p in folder.glob("lesson_*.md") if not re.fullmatch(r"lesson_\d{3}\.md",p.name))
        hard=defaultdict(list);quality=defaultdict(list);opens=defaultdict(list);ends=defaultdict(list)
        for row in entries:
            for issue in row["hard_issues"]:hard[issue].append(row["lesson"])
            for issue in row["quality_flags"]:quality[issue].append(row["lesson"])
            if row["opening"]:opens[row["opening"]].append(row["lesson"])
            if row["closure"]:ends[row["closure"]].append(row["lesson"])
        dup_start=sorted((v for v in opens.values() if len(v)>=3),key=lambda x:-len(x))[:10]
        dup_end=sorted((v for v in ends.values() if len(v)>=3),key=lambda x:-len(x))[:10]
        summary={
          "files":len(entries),"missing":missing,"unexpected_filenames":unexpected,
          "fixed_sow":sum(x["fixed_sow"] for x in entries),
          "sow_matched":sum(x["sow_header_pair_match"] is True for x in entries),
          "teacher_choice":sum(x["teacher_choice"] for x in entries),
          "objective_headers":sum(x["objective_header"] for x in entries),
          "book_refs":sum(x["book_reference"] for x in entries),
          "workbook_refs":sum(x["workbook_reference"] for x in entries),
          "audio_refs":sum(x["audio_reference"] for x in entries),
          "internal_notes_in_sources":sum(x["internal_review_notes_in_source"] for x in entries),
          "timing60":sum(x["phase_minute_sum"]==60 for x in entries),
          "timing_not_extractable":sum(x["phase_minute_sum"] is None for x in entries),
          "hard_issue_lessons":dict(hard),"quality_flag_lessons":dict(quality),
          "duplicate_opening_groups":dup_start,"duplicate_closure_groups":dup_end,
          "shortest_sources":sorted(({"n":x["lesson"],"chars":x["length"]} for x in entries),key=lambda z:z["chars"])[:8],
        }
        if y>=2: hard_total+=len(missing)+len(unexpected)+sum(map(len,hard.values()))  # Year 1 inventory is KP2027-exempt
        report["years"][str(y)]={"summary":summary,"lessons":entries}
        print(f"YEAR{y} files={len(entries)}/160 fixed={summary['fixed_sow']} matched={summary['sow_matched']} choice={summary['teacher_choice']} objectives={summary['objective_headers']} books={summary['book_refs']} WB={summary['workbook_refs']} audio={summary['audio_refs']} timed60={summary['timing60']}")
        for label,groups in (("HARD",hard),("QUALITY",quality)):
            for name,ids in groups.items():print(f"  {label} {name}: {len(ids)} Lessons {ids[:35]}")
        for label,groups in (("dup_open",dup_start),("dup_close",dup_end)):
            if groups:print(f"  {label}: {len(groups)} groups, examples={groups[:4]}")
    report["total_year2_6"]=sum(report["years"][str(y)]["summary"]["files"] for y in range(2,7))
    report["total_year1"]=report["years"]["1"]["summary"]["files"]
    report["hard_issue_occurrences"]=hard_total
    print(f"TOTAL Year2-6={report['total_year2_6']} Year1={report['total_year1']} structural_issues={hard_total}")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--strict",action="store_true")
    options=parser.parse_args()
    result=audit()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    sys.exit(1 if options.strict and result["hard_issue_occurrences"] else 0)
