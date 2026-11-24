"""Audit and prepare source-grounded activity candidates, without publishing.
Run against checksum-verified v26 master and the actual active native generator.
No production accounts, DB writes, credit use, or 696 archive.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
from hashlib import sha256
import re
import sqlite3
import unicodedata
from tools.bm_native_v26_navigation_audit import database
from web.pi_jawi_english_terms_20261122 import normalize_english_terms
from web.rph_pi_jawi_numerals_20261124 import jawi_display_digits
from web.pi_navigation import is_pi_recitation_session

MARKER = re.compile(r"(?<!\S)([1-9])\.\s*(?=[\u0600-\u08ff])")
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

def normalized(text):
    text = unicodedata.normalize("NFC", str(text or "")).translate(DIGITS)
    return " ".join(text.split())

def source_steps(text):
    text = normalized(normalize_english_terms(text))
    markers = list(MARKER.finditer(text))
    if not 2 <= len(markers) <= 8 or markers[0].start() != 0:
        return []
    if [int(m.group(1)) for m in markers] != list(range(1,len(markers)+1)):
        return []
    steps = [text[m.end():markers[i+1].start() if i+1<len(markers) else len(text)].strip()
             for i,m in enumerate(markers)]
    if any(len(s)<12 or not re.search(r"[\u0600-\u08ff]",s) for s in steps):
        return []
    return steps

def inspect(rows, note):
    main = str(rows.get("AKTIVITI UTAMA") or "")
    all_text = normalized(" ".join(str(x) for x in rows.values()))
    plain_main = normalized(main)
    steps = source_steps(note)
    missing = [i for i,s in enumerate(steps,1) if normalized(s) not in all_text]
    present = [i for i,s in enumerate(steps,1) if normalized(s) in plain_main]
    duplicate = [i for i,s in enumerate(steps,1) if plain_main.count(normalized(s)) > 1]
    return {"main_chars":len(plain_main), "source_steps":len(steps), "missing":missing,
            "present_main":present, "duplicate":duplicate,
            "teacher_explicit":bool(re.search(r"(?:ݢورو|ڬورو|گورو|guru)", main,re.I)),
            "pupil_explicit":bool(re.search(r"(?:موريد|murid)",main,re.I))}

def candidate(rows,note,metrics):
    """QA-only proposal: restore exact missing teaching steps, not generic filler.
    Require at least one complete source step in current main activity, and
    only propose missing full steps (not a blind replacement of existing text).
    A human must review semantic duplication and real A4 output before adoption.
    """
    if not metrics["present_main"] or not metrics["missing"]:
        return None
    steps = source_steps(note)
    # Rebuild an editorial candidate in the source order, rather than
    # appending all missing steps under the last (assessment) heading.
    # Existing specific material outside the source must be reviewed before
    # adopting any candidate. This is never a runtime transformation.
    buckets = [[steps[0]], steps[1:-1], [steps[-1]]] if len(steps)>=3 else [[steps[0]], [steps[-1]]]
    blocks = []
    for index, group in enumerate(buckets, 1):
        heading = jawi_display_digits(f"اکتيۏيتي {index}")
        blocks.append(heading+"\n"+"\n".join(jawi_display_digits(f"{i}. {step}") for i,step in enumerate(group,1)))
    return "\n".join(blocks)

def main():
    from tools import run_telegram_with_curriculum_api as running
    from web.telegram_verified_rpt_rph_bridge import _native_state,_native_text
    from web.pi_navigation import pi_navigation_unit
    runtime=running.telegram_runtime
    tmp,db=database()
    report={"status":"QA_ONLY_NOT_READY","source":"active v26 PI T2–6","years":{},"records":[]}
    examples=defaultdict(list)
    shared_lines=defaultdict(list)
    shared_main=defaultdict(list)
    shared_candidate=defaultdict(list)
    candidate_bank=[]
    residual_review=[]
    source_specific_recitation=[]
    registry=json.loads(Path("staging/pendidikan_islam/active_activity_source_registry_20261125.json").read_text(encoding="utf8"))
    source_registry={entry["year"]:entry for entry in registry["years"]}
    page_evidence=json.loads(Path("staging/pendidikan_islam/active_dskp_text_page_evidence_20261125.json").read_text(encoding="utf8"))
    dskp_pages={entry["year"]:entry.get("code_page_candidates",{}) for entry in page_evidence["years"]}
    try:
        runtime.DB_PATH=str(db)
        runtime.CIKGULAJU_DB_V2600_ACTIVE=True
        with sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True) as con:
            con.row_factory=sqlite3.Row
            con.execute("PRAGMA query_only=ON")
            assert con.execute("PRAGMA quick_check").fetchone()[0]=="ok"
            source=[dict(r) for r in con.execute("""
                SELECT * FROM rpt_entries WHERE subject='Pendidikan Islam' AND verified=1
                AND year_label IN ('Tahun 2','Tahun 3','Tahun 4','Tahun 5','Tahun 6')
                AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                ORDER BY year_label,sequence_no,id""")]
        teacher={"class":"","date":"","time":"","students":"","reflection":""}
        for row in source:
            year=int(row["year_label"].split()[-1])
            unit=pi_navigation_unit(row)
            key=str(year)
            stats=report["years"].setdefault(key,Counter())
            stats["source"]+=1
            try:
                state=_native_state(runtime,{"year":year,"subject":"PI","unit":unit,
                    "lesson":int(row["id"])},teacher.copy())
                text=_native_text(runtime,state)
                rows=runtime._rph_rows(state,text)
                if not isinstance(rows,dict):
                    raise TypeError("unexpected native row structure")
                m=inspect(rows,row["activity_note"])
                stats["rendered"]+=1
                for k,v in (("numbered_source",m["source_steps"]),
                            ("missing_exact_source_step",m["missing"]),
                            ("duplicate_source_step",m["duplicate"]),
                            ("short_main_under_150_chars",m["main_chars"]<150),
                            ("no_explicit_teacher",not m["teacher_explicit"]),
                            ("no_explicit_pupil",not m["pupil_explicit"])):
                    if v: stats[k]+=1
                proposed=candidate(rows,row["activity_note"],m)
                if proposed is not None: stats["candidate"]+=1
                record={"year":year,"pdp":row["sequence_no"],"id":row["id"],"unit":unit,
                    "topic":row.get("topic"),**m,"candidate_available":proposed is not None}
                identity={"year":year,"pdp":row["sequence_no"],"id":row["id"],"unit":unit}
                objective=normalized(rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"))
                main_text=normalized(rows.get("AKTIVITI UTAMA"))
                shared_main[sha256(main_text.encode()).hexdigest()].append({**identity,"objective":objective})
                # Compare complete activity instruction lines, not shared headings
                # or short conventional phrases. Legitimate repeated recitation
                # routines are review flags, not automatic failures.
                for line in set(normalized(x) for x in str(rows.get("AKTIVITI UTAMA") or "").splitlines()):
                    line=re.sub(r"^[1-9]\.\s*","",line)
                    if len(line)>=70 and not line.startswith("اکتيۏيتي"):
                        shared_lines[line].append({**identity,"objective":objective})
                if proposed:
                    shared_candidate[normalized(proposed)].append({**identity,"objective":objective})
                if proposed:
                    source_row=state.get("_quick_selected_rpt_row_v2388") or {}
                    # Store every candidate, not just representative examples.
                    # Source references are claims from DB, not verified page evidence.
                    candidate_bank.append({**identity,"source_recitation_only":bool(is_pi_recitation_session(source_row)),"status":"QA_HOLD_SOURCE_PAGE_REVIEW",
                        "topic":row.get("topic"),"objective":rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"),
                        "sk_codes":state.get("grouped_sk_codes",[]), "sp_codes":state.get("grouped_sp_codes",[]),
                        "sk_texts":state.get("grouped_sk_texts",[]), "sp_texts":state.get("grouped_sp_texts",[]),
                        "textbook_unit_claim":state.get("textbook_unit"),"textbook_pages_claim":state.get("textbook_pages"),
                        "dskp_drive_id":source_registry[year]["dskp"],"textbook_drive_id":source_registry[year]["textbook"],
                        "source_note":row["activity_note"],"source_note_sha256":sha256(row["activity_note"].encode()).hexdigest(),
                        "source_steps":source_steps(row["activity_note"]),"current_main":rows.get("AKTIVITI UTAMA"),
                        "candidate_main":proposed,"candidate_missing_source_steps":[i for i,step in enumerate(source_steps(row["activity_note"]),1) if normalized(step) not in normalized(proposed)],
                        "dskp_page_checked":False,"textbook_page_checked":False,"jawi_editor_approved":False,"native_output_approved":False,"ready":False})
                if proposed is None:
                    residual_review.append({**identity,"topic":row.get("topic"),"objective":rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"),"source_note":row["activity_note"],"current_main":rows.get("AKTIVITI UTAMA"),"source_steps":source_steps(row["activity_note"]),"metrics":m,"reason":"UNNUMBERED_OR_UNPARSED_SOURCE" if not m["source_steps"] else "NO_EXACT_STEP_IN_MAIN" if not m["present_main"] else "ALL_PARSED_STEPS_PRESENT_REVIEW_QUALITY","ready":False})
                report["records"].append(record)
                # At most two diagnostic examples per field/year: actual
                # source, current output and candidate, not invented content.
                bucket=(year,str(unit))
                if len(examples[bucket])<2 and (proposed or m["duplicate"] or m["main_chars"]<150 or not m["teacher_explicit"] or not m["pupil_explicit"]):
                    examples[bucket].append({**record,"source_note":row["activity_note"],
                        "objective":rows.get("OBJEKTIF PEMBELAJARAN") or rows.get("OBJEKTIF"),
                        "current_main":rows.get("AKTIVITI UTAMA"),"candidate_main":proposed})
            except Exception as exc:
                stats["errors"]+=1
                report["records"].append({"year":year,"id":row["id"],"pdp":row["sequence_no"],
                    "error":type(exc).__name__})
        report["examples"]=[e for v in examples.values() for e in v]
        def clusters(items):
            return sorted(({"text":line,"count":len(entries),"distinct_objectives":len({e["objective"] for e in entries}),"records":entries}
                           for line,entries in items.items() if len(entries)>1),key=lambda x:(-x["count"],x["text"]))
        report["repeated_instruction_clusters"]=clusters(shared_lines)
        report["identical_main_clusters"]=clusters(shared_main)
        report["identical_candidate_clusters"]=clusters(shared_candidate)
        print("PI_ACTIVITY_REUSE",json.dumps({"repeated_instruction_clusters":len(report["repeated_instruction_clusters"]),
            "identical_main_clusters":len(report["identical_main_clusters"]),
            "identical_candidate_clusters":len(report["identical_candidate_clusters"]),
            "top_repeated_lines":[{k:v for k,v in x.items() if k!="records"} for x in report["repeated_instruction_clusters"][:12]]},ensure_ascii=False),flush=True)
        out=Path("qa/pi-activity-quality")
        out.mkdir(parents=True,exist_ok=True)
        (out/"audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        repeated={x["text"] for x in report["identical_candidate_clusters"]}
        for item in candidate_bank:
            item["same_candidate_as_another_pdp"]=normalized(item["candidate_main"]) in repeated
            codes=[str(code).translate(DIGITS) for code in item["sp_codes"]]
            item["dskp_text_layer_pages_by_sp"]={code:dskp_pages[item["year"]].get(code,[]) for code in codes}
            item["dskp_code_page_candidates_complete"]=bool(codes) and all(item["dskp_text_layer_pages_by_sp"].values())
            item["reference_review_type"]=("MUSHAF_TASMIK" if item["source_recitation_only"] and not item["textbook_pages_claim"] else
                "TEXTBOOK_PAGE_CLAIM_REVIEW" if item["textbook_pages_claim"] else "TEXTBOOK_PAGE_MISSING_REVIEW")
            item["dskp_visual_check_required"]=True
            assert not item["candidate_missing_source_steps"], item["id"]
            assert not item["ready"]
        assert len({x["id"] for x in candidate_bank})==len(candidate_bank)
        assert len(candidate_bank)==sum(s["candidate"] for s in report["years"].values())
        (out/"all_activity_candidates.json").write_text(json.dumps({"status":"QA_HOLD_NOT_FOR_RUNTIME","records":candidate_bank},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        # Preserve all non-candidate lessons, rather than silently dropping them.
        assert len(candidate_bank)+len(residual_review)==698
        (out/"residual_42_editorial_review.json").write_text(json.dumps({"status":"QA_HOLD_NOT_FOR_RUNTIME","records":residual_review},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        priority=[x for x in candidate_bank if x["same_candidate_as_another_pdp"] or x["reference_review_type"]=="TEXTBOOK_PAGE_MISSING_REVIEW"]
        (out/"priority_duplicate_or_missing_reference.json").write_text(json.dumps({"status":"QA_HOLD_NOT_FOR_RUNTIME","records":priority},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("PI_RESIDUAL_REVIEW",json.dumps({"total":len(residual_review),"by_reason":dict(Counter(x["reason"] for x in residual_review)),"by_year":dict(Counter(x["year"] for x in residual_review)),"priority_duplicate_or_missing_reference":len(priority),"ready":0}),flush=True)
        # Produce source-specific recitation candidates only when the objective
        # gives an explicit surah + numbered verse range. Keep exact original
        # source notes and existing candidates for comparison; never invent verses.
        from tools.pi_active_recitation_candidate_20261125 import specialize_recitation
        for item in candidate_bank:
            if item["unit"]!="Al-Quran": continue
            special=specialize_recitation(item)
            if special: source_specific_recitation.append(special)
        (out/"recitation_specific_candidates.json").write_text(json.dumps({"status":"QA_HOLD_NOT_FOR_RUNTIME","records":source_specific_recitation},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("PI_RECITATION_SPECIFIC",json.dumps({"total":len(source_specific_recitation),"years":dict(Counter(x["year"] for x in source_specific_recitation)), "distinct_activity_texts":len({normalized(x["specific_main"]) for x in source_specific_recitation}),"source_recitation_only_without_textbook_page":sum(x["source_recitation_only"] and not x["textbook_pages_claim"] for x in candidate_bank),"ready":0}),flush=True)
        print("PI_FULL_CANDIDATE_BANK",json.dumps({"total":len(candidate_bank),"years":dict(Counter(x["year"] for x in candidate_bank)),
            "same_candidate_review":sum(x["same_candidate_as_another_pdp"] for x in candidate_bank),
            "textbook_reference_claim_available":sum(bool(x["textbook_pages_claim"]) for x in candidate_bank),
            "reference_review_types":dict(Counter(x["reference_review_type"] for x in candidate_bank)),
            "dskp_text_page_candidate_complete":sum(x["dskp_code_page_candidates_complete"] for x in candidate_bank),
            "ready":0}),flush=True)
        print("PI_ACTIVITY_QUALITY",json.dumps(report["years"],ensure_ascii=False),flush=True)
        for e in report["examples"]:
            print("PI_ACTIVITY_EXAMPLE",json.dumps(e,ensure_ascii=False),flush=True)
        assert sum(s["source"] for s in report["years"].values())==698
        assert sum(s["rendered"] for s in report["years"].values())==698
    finally:
        tmp.cleanup()

if __name__=="__main__":
    main()
