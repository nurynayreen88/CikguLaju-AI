"""Read-only 12-scope PJPK remediation summary; no curriculum promotion."""
import argparse
import collections
import json
from scripts.pjpk_source_gap_queue_v2679 import build_queue

SUBJECTS = ("Pendidikan Jasmani", "Pendidikan Kesihatan")
YEARS = tuple(f"Tahun {n}" for n in range(1, 7))

def summarize(queue):
    matrix = {(year, subject): collections.Counter() for year in YEARS for subject in SUBJECTS}
    for row in queue:
        key = (row["year"], row["subject"])
        if key not in matrix:
            raise ValueError(f"Unexpected curriculum scope: {key!r}")
        matrix[key][row["record_type"]] += 1
        matrix[key]["TOTAL"] += 1
    scopes = [{"year": year, "subject": subject,
               "sp_source_review": matrix[(year, subject)]["SP_SOURCE_REVIEW"],
               "missing_sk_link": matrix[(year, subject)]["MISSING_SK_LINK"],
               "review_rows": matrix[(year, subject)]["TOTAL"]}
              for year in YEARS for subject in SUBJECTS]
    return {"read_only": True, "production_promoted": False,
            "scope_count": len(scopes), "review_rows": len(queue),
            "sp_source_review": sum(x["sp_source_review"] for x in scopes),
            "missing_sk_link": sum(x["missing_sk_link"] for x in scopes),
            "scopes": scopes}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Existing isolated candidate DB; opened read-only")
    args = parser.parse_args()
    print(json.dumps(summarize(build_queue(args.db)), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
