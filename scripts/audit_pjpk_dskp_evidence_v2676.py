"""Read-only source reconciliation audit for the PJPK candidate DB."""
import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pjpk_dskp_evidence_v2676 import load_evidence, reconcile_sp_text


def audit(db_path):
    evidence = load_evidence(Path(__file__).resolve().parents[1])
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as con:
        con.row_factory = sqlite3.Row
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError("PJPK candidate DB integrity failure: " + str(integrity))
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"rpt_entries", "rpt_entry_standards", "pjpk_v40_page_sp_crosswalk"}
        if not required.issubset(tables):
            raise RuntimeError("PJPK candidate DB missing required audit tables")
        entries = con.execute(
            "SELECT id,year_label,subject,topic FROM rpt_entries "
            "WHERE subject IN ('Pendidikan Jasmani','Pendidikan Kesihatan')"
        ).fetchall()
        per_entry = defaultdict(set)
        links = con.execute(
            "SELECT e.id,e.year_label,e.subject,s.standard_type,s.standard_code,s.standard_text "
            "FROM rpt_entries e JOIN rpt_entry_standards s ON s.rpt_entry_id=e.id "
            "WHERE e.subject IN ('Pendidikan Jasmani','Pendidikan Kesihatan') "
            "ORDER BY e.year_label,e.subject,e.id,s.sequence_no"
        ).fetchall()
        counts = Counter()
        by_scope = defaultdict(Counter)
        for link in links:
            scope = (link["year_label"], link["subject"])
            kind = link["standard_type"]
            per_entry[link["id"]].add(kind)
            if kind == "SP":
                result = reconcile_sp_text(
                    link["year_label"], link["subject"], link["standard_code"],
                    link["standard_text"], evidence
                )
                counts[result["status"]] += 1
                by_scope[scope][result["status"]] += 1
            counts["links_total"] += 1
        pages = con.execute("SELECT COUNT(*) FROM pjpk_v40_page_sp_crosswalk").fetchone()[0]
        rows = []
        for year in range(1, 7):
            for subject in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
                scope = (f"Tahun {year}", subject)
                n_entries = sum(1 for e in entries if (e["year_label"],e["subject"]) == scope)
                rows.append({
                    "year": scope[0], "subject": subject, "rpt_entries": n_entries,
                    "sp_links": sum(by_scope[scope].values()),
                    "dskp_exact_text_match": by_scope[scope]["EXACT_TEXT_MATCH"],
                    "dskp_text_diff_review": by_scope[scope]["TEXT_DIFF_REVIEW"],
                    "dskp_conflict_review": by_scope[scope]["CONFLICT_REVIEW"],
                    "no_direct_dskp_text": by_scope[scope]["NO_DIRECT_DSKP_TEXT"],
                })
        report = {
            "db_integrity": integrity,
            "source_evidence_exact_keys": len(evidence),
            "source_evidence_conflict_keys": sum(
                1 for rows_ in evidence.values()
                if len({r["sp_text"] for r in rows_}) > 1 or any(r["source_status"] != "DIRECT_DSKP_TEXT_TRANSCRIBED" for r in rows_)
            ),
            "pjpk_rpt_entries": len(entries),
            "pjpk_entries_with_sk_and_sp_links": sum(1 for kinds in per_entry.values() if {"SK","SP"}.issubset(kinds)),
            "pjpk_entries_missing_sk_link": sum(1 for kinds in per_entry.values() if "SK" not in kinds),
            "pjpk_textbook_page_crosswalk_rows": pages,
            "sp_links": {key: counts[key] for key in ("EXACT_TEXT_MATCH","TEXT_DIFF_REVIEW","CONFLICT_REVIEW","NO_DIRECT_DSKP_TEXT")},
            "by_year_subject": rows,
            "release_gate": "UNCHANGED — this audit never promotes production readiness",
        }
        return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="pjpk_candidate.db")
    args = parser.parse_args()
    print(json.dumps(audit(args.db), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
