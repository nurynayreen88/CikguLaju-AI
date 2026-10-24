"""Generate a fail-closed evidence workqueue for all 18 T2 PK editorial RPH.

Only copies recorded evidence; never promotes editorial drafts to production.
Run: python -m scripts.pjpk_t2_pk_evidence_queue OUTPUT.csv
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "docs/pjpk/T2_PK_7_COMPLETE_RPH_EDITORIAL_STAGING_20261024.json",
    ROOT / "docs/pjpk/T2_PK_11_REMAINING_EDITORIAL_STAGING_20261024.json",
)
FOCUS = ROOT / "docs/pjpk/T2_PK_11_SP_EDITORIAL_FOCUS_MATRIX_20261024.json"
FIELDS = ("entry_id", "topic", "recorded_sp_codes", "candidate_sp_codes_not_verified", "sk_text_verified", "sp_text_verified",
          "textbook_verified", "rpt_exact_slot_verified", "rph_runtime_verified",
          "a4_review_verified", "production_ready", "required_next_evidence")


def build():
    records = [r for path in SOURCES for r in json.loads(path.read_text(encoding="utf-8"))["records"]]
    ids = [r["id"] for r in records]
    if len(ids) != 18 or len(set(ids)) != 18:
        raise ValueError("Expected exactly 18 unique T2 PK entries")
    matrix = json.loads(FOCUS.read_text(encoding="utf-8"))
    if matrix.get("status") != "candidate_only_do_not_activate" or matrix.get("production_ready") is not False:
        raise ValueError("Candidate focus matrix must remain blocked")
    candidates = {row["id"]: row["sp"] for row in matrix["candidates"]}
    if len(candidates) != 11 or set(candidates) != {r["id"] for r in records if not r.get("sp")}:
        raise ValueError("Candidate focus matrix does not match eleven empty-SP records")
    output = []
    for r in sorted(records, key=lambda item: item["id"]):
        if r.get("status") != "editorial_staging_only" or r.get("production_ready") is not False:
            raise ValueError(f"{r['id']}: unexpected production state")
        flags = ("sk_text_verified", "sp_text_verified", "textbook_verified",
                 "rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified")
        if any(r.get(flag) is not False for flag in flags):
            raise ValueError(f"{r['id']}: evidence flag changed; re-audit source first")
        needs = ["DSKP SK code and verbatim text", "DSKP SP code and verbatim text",
                 "textbook exact page and content", "RPT exact PdP slot",
                 "runtime generation test", "human A4 review"]
        output.append(dict(entry_id=r["id"], topic=r["topic"],
                           recorded_sp_codes=";".join(r.get("sp") or []),
                           candidate_sp_codes_not_verified=";".join(candidates.get(r["id"], [])),
                           **{flag: str(r[flag]).lower() for flag in flags},
                           production_ready="false", required_next_evidence="; ".join(needs)))
    return output


def write(path):
    rows = build()
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.pjpk_t2_pk_evidence_queue OUTPUT.csv")
    print(f"Wrote {write(sys.argv[1])} blocked T2 PK evidence tasks")
