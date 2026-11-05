"""Run a safe schema-only audit of an explicitly supplied SQLite snapshot.

Usage:
    python -m web.audit_rph_candidates /path/to/snapshot.sqlite

No row data, personal identifiers, or RPH text is printed. This does not
approve any records or enable the public generator.
"""
import json
import sys
from web.audit_rph_schema import inspect_schema

TERMS = ("rph", "standalone", "lesson", "rpt", "approved", "approval",
         "content", "verified", "status", "pdp")


def candidate_report(path: str) -> dict:
    schema = inspect_schema(path)
    candidates = []
    for table, columns in schema["tables"].items():
        matching = [col["name"] for col in columns
                    if any(term in col["name"].lower() for term in TERMS)]
        if any(term in table.lower() for term in TERMS) or matching:
            candidates.append({
                "table": table,
                "matching_columns": matching,
                "all_columns": [col["name"] for col in columns],
            })
    return {
        "integrity": schema["integrity"],
        "candidates": candidates,
        "warning": (
            "Schema candidates only. Manual approval mapping is mandatory. "
            "Never infer RPH approval from rpt_entries.verified alone."
        ),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m web.audit_rph_candidates SNAPSHOT.sqlite")
    print(json.dumps(candidate_report(sys.argv[1]), ensure_ascii=False, indent=2))
