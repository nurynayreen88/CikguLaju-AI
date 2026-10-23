"""Build an actionable, read-only PJPK DSKP/RPT source-gap queue.

This does not edit curriculum records or promote any RPH. It emits only exact
same-year/same-subject SP links whose source evidence needs human reconciliation,
plus entries missing a linked SK. Output can be redirected to a review CSV/JSON.
"""
import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pjpk_dskp_evidence_v2676 import load_evidence, reconcile_sp_text


def build_queue(db_path):
    root = Path(__file__).resolve().parents[1]
    evidence = load_evidence(root)
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as con:
        con.row_factory = sqlite3.Row
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError("Candidate DB integrity_check failed: " + integrity)
        required = {"rpt_entries", "rpt_entry_standards"}
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not required.issubset(tables):
            raise RuntimeError("Candidate DB lacks RPT tables; refusing to guess schema")
        entries = con.execute("""
            SELECT e.id, e.year_label, e.subject, e.unit_title, e.topic
            FROM rpt_entries e
            WHERE e.subject IN ('Pendidikan Jasmani','Pendidikan Kesihatan')
            ORDER BY e.year_label,e.subject,e.id
        """).fetchall()
        links = con.execute("""
            SELECT e.id,e.year_label,e.subject,e.unit_title,e.topic,
                   s.standard_type,s.standard_code,s.standard_text
            FROM rpt_entries e
            JOIN rpt_entry_standards s ON s.rpt_entry_id=e.id
            WHERE e.subject IN ('Pendidikan Jasmani','Pendidikan Kesihatan')
            ORDER BY e.year_label,e.subject,e.id,s.sequence_no
        """).fetchall()
        by_entry = {}
        queue = []
        for row in links:
            by_entry.setdefault(row["id"], set()).add(row["standard_type"])
            if row["standard_type"] != "SP":
                continue
            result = reconcile_sp_text(row["year_label"], row["subject"],
                                       row["standard_code"], row["standard_text"], evidence)
            if result["status"] != "EXACT_TEXT_MATCH":
                queue.append({
                    "record_type": "SP_SOURCE_REVIEW",
                    "entry_id": row["id"], "year": row["year_label"],
                    "subject": row["subject"], "week": "",
                    "topic": (row["unit_title"] or "") + ((" — " + row["topic"]) if row["topic"] else ""), "standard_code": row["standard_code"] or "",
                    "rpt_text": row["standard_text"] or "",
                    "evidence_status": result["status"],
                    "direct_dskp_text": result.get("dskp_text", ""),
                    "source_document": result.get("source_document", ""),
                    "action": {
                        "NO_DIRECT_DSKP_TEXT": "TRANSCRIBE_FROM_EXACT_YEAR_SUBJECT_DSKP",
                        "CONFLICT_REVIEW": "RESOLVE_SOURCE_CONFLICT_BEFORE_RELEASE",
                        "TEXT_DIFF_REVIEW": "COMPARE_RPT_AND_DSKP_WORDING",
                    }.get(result["status"], "MANUAL_SOURCE_REVIEW"),
                })
        for entry in entries:
            if "SK" not in by_entry.get(entry["id"], set()):
                queue.append({
                    "record_type": "MISSING_SK_LINK", "entry_id": entry["id"],
                    "year": entry["year_label"], "subject": entry["subject"],
                    "week": "", "topic": (entry["unit_title"] or "") + ((" — " + entry["topic"]) if entry["topic"] else ""),
                    "standard_code": "", "rpt_text": "", "evidence_status": "MISSING_SK_LINK",
                    "direct_dskp_text": "", "source_document": "",
                    "action": "LOCATE_AND_VERIFY_EXACT_SK_SOURCE; DO_NOT_INFER",
                })
        return queue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to isolated PJPK candidate SQLite DB")
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    args = parser.parse_args()
    queue = build_queue(args.db)
    if args.format == "json":
        print(json.dumps({"read_only": True, "production_promoted": False,
                          "queue_count": len(queue), "items": queue},
                         ensure_ascii=False, indent=2))
    else:
        fields = ["record_type","entry_id","year","subject","week","topic",
                  "standard_code","rpt_text","evidence_status","direct_dskp_text",
                  "source_document","action"]
        writer = csv.DictWriter(sys.stdout, fieldnames=fields)
        writer.writeheader()
        writer.writerows(queue)


if __name__ == "__main__":
    main()
