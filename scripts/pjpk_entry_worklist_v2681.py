"""Read-only, entry-grouped PJPK source remediation worklist for all 12 scopes."""
import argparse
import collections
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.pjpk_source_gap_queue_v2679 import build_queue
from scripts.pjpk_12_scope_summary_v2680 import YEARS, SUBJECTS

def group_entries(queue):
    groups = {}
    for row in queue:
        year, subject, entry_id = row["year"], row["subject"], row["entry_id"]
        if year not in YEARS or subject not in SUBJECTS:
            raise ValueError("Unexpected PJPK scope")
        if row["record_type"] not in {"SP_SOURCE_REVIEW", "MISSING_SK_LINK"}:
            raise ValueError("Unexpected PJPK record type")
        key = (year, subject, entry_id)
        group = groups.setdefault(key, {"year": year, "subject": subject,
            "entry_id": entry_id, "topic": row["topic"], "sp_reviews": [],
            "missing_sk_link": False})
        if group["topic"] != row["topic"]:
            raise ValueError("Conflicting topic for same RPT entry")
        if row["record_type"] == "MISSING_SK_LINK":
            if group["missing_sk_link"]:
                raise ValueError("Duplicate missing SK flag")
            group["missing_sk_link"] = True
        else:
            group["sp_reviews"].append({"code": row["standard_code"],
                "rpt_text": row["rpt_text"], "status": row["evidence_status"],
                "source_document": row["source_document"],
                "direct_dskp_text": row["direct_dskp_text"],
                "action": row["action"]})
    output = []
    for year in YEARS:
        for subject in SUBJECTS:
            entries = [v for k,v in groups.items() if k[:2] == (year,subject)]
            entries.sort(key=lambda e: (not e["missing_sk_link"], -len(e["sp_reviews"]), str(e["entry_id"])))
            output.append({"year": year, "subject": subject, "unique_entries": len(entries),
                "review_rows": sum(len(e["sp_reviews"]) + int(e["missing_sk_link"]) for e in entries),
                "entries": entries})
    if sum(s["review_rows"] for s in output) != len(queue):
        raise ValueError("Worklist lost review rows")
    return {"read_only": True, "production_promoted": False, "scope_count": 12,
            "review_rows": len(queue), "unique_entries": len(groups), "scopes": output}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True)
    args=p.parse_args()
    print(json.dumps(group_entries(build_queue(args.db)),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
