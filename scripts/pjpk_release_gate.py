"""Fail-closed PJPK release gate. Run: python scripts/pjpk_release_gate.py PATH_TO_SOURCE_GATE.csv

This checker is deliberately independent of production database and does not write files.
"""
import csv
import sys
from collections import Counter

YEARS = {f"Tahun {i}" for i in range(1, 7)}
SUBJECTS = {"Pendidikan Jasmani", "Pendidikan Kesihatan"}
REQUIRED = {"entry_id", "year_label", "subject", "entry_kind", "sp_links",
            "dskp_text_matches", "dskp_text_mismatches", "dskp_text_missing",
            "book_exact_match", "conflict", "production_ready"}
def audit(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError("Duplicate CSV column headers")
        missing = REQUIRED - set(headers)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
        rows = list(reader)
    ids = [r["entry_id"] for r in rows]
    errors = []
    if not rows:
        errors.append("Empty source inventory")
    if any(not ident.strip() or not ident.isdecimal() or int(ident) <= 0 for ident in ids):
        errors.append("Entry IDs must be positive decimal integers")
    if any(None in row for row in rows):
        errors.append("CSV row contains extra unlabelled fields")
    if any(any(value is None for value in row.values()) for row in rows):
        errors.append("CSV row has missing trailing fields")
    if len(ids) != len(set(ids)):
        errors.append("Duplicate entry IDs")
    for r in rows:
        ident = r["entry_id"]
        if r["production_ready"] not in ("0", "1"):
            errors.append(f"{ident}: production_ready must be explicitly 0 or 1")
        if r["year_label"] not in YEARS or r["subject"] not in SUBJECTS:
            errors.append(f"{ident}: invalid year or subject")
        if r["entry_kind"] != "PDP_CANDIDATE" and r["production_ready"] == "1":
            errors.append(f"{ident}: reference-only record marked ready")
        if r["production_ready"] == "1":
            try:
                linked = int(r["sp_links"]); matched = int(r["dskp_text_matches"])
                missing_sp = int(r["dskp_text_missing"]); mismatch = int(r["dskp_text_mismatches"])
                safe = (linked > 0 and matched == linked and missing_sp == 0 and mismatch == 0
                        and r["conflict"] == "0" and r["book_exact_match"] == "1")
            except ValueError:
                safe = False
            if not safe:
                errors.append(f"{ident}: unsafe production_ready flag")
    counts = Counter((r["year_label"], r["subject"], r["entry_kind"]) for r in rows)
    return rows, counts, errors

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/pjpk_release_gate.py SOURCE_GATE.csv")
    rows, counts, errors = audit(sys.argv[1])
    print(f"Records: {len(rows)}; ready: {sum(r['production_ready'] == '1' for r in rows)}")
    for key, value in sorted(counts.items()):
        print(*key, value, sep=" | ")
    for error in errors:
        print("BLOCK:", error, file=sys.stderr)
    if errors:
        raise SystemExit(1)
    if not any(r["production_ready"] == "1" for r in rows):
        print("BLOCK: no release-ready records; inventory validation only", file=sys.stderr)
        raise SystemExit(2)
    print("Source-gate checks passed. Additional RPH and runtime QA still required.")
