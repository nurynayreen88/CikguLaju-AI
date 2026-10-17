"""Read-only audit of RPT-derived page references against PJ candidate entries."""
import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pjpk_rpt_page_evidence_v2677 import lookup_page_evidence


def audit(db_path):
    root = Path(__file__).resolve().parents[1]
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as con:
        con.row_factory = sqlite3.Row
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Candidate DB integrity failure")
        entries = con.execute(
            "SELECT id,year_label,subject,unit_title,topic FROM rpt_entries "
            "WHERE subject='Pendidikan Jasmani' ORDER BY year_label,id"
        ).fetchall()
        by_scope = defaultdict(Counter)
        details = []
        for entry in entries:
            result = lookup_page_evidence(
                entry["year_label"], entry["subject"], entry["unit_title"], entry["topic"], root
            )
            db_codes = {
                row[0] for row in con.execute(
                    "SELECT standard_code FROM rpt_entry_standards "
                    "WHERE rpt_entry_id=? AND standard_type='SP' AND trim(coalesce(standard_code,''))<>''",
                    (entry["id"],)
                )
            }
            rpt_codes = set(result.get("rpt_sp_codes") or [])
            if result.get("pages"):
                status = "PAGE_FOUND"
                if rpt_codes and rpt_codes == db_codes:
                    status = "PAGE_FOUND_AND_SP_SET_MATCH"
                elif rpt_codes and rpt_codes != db_codes:
                    status = "PAGE_FOUND_SP_SET_MISMATCH"
            else:
                status = result["status"]
            by_scope[entry["year_label"]][status] += 1
            details.append({
                "entry_id": entry["id"], "year": entry["year_label"],
                "unit": entry["unit_title"], "topic": entry["topic"],
                "status": status, "pages": result.get("pages", []),
                "rpt_sp_codes": sorted(rpt_codes), "db_sp_codes": sorted(db_codes),
                "source_file": result.get("source_file", ""),
            })
        return {
            "db_integrity": "ok",
            "pj_entries_audited": len(entries),
            "by_year": {year: dict(counts) for year, counts in sorted(by_scope.items())},
            "totals": dict(Counter(d["status"] for d in details)),
            "notes": [
                "Page references are transcribed from the RPT source; this is not an independent textbook-PDF verification.",
                "This audit is read-only and never promotes production readiness."
            ],
            "entries": details,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="pjpk_candidate.db")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    report = audit(args.db)
    if args.summary_only:
        report.pop("entries", None)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
