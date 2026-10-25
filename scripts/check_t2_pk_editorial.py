"""Read-only editorial QA for the 18 T2 PK staging records; never authorizes release."""
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "docs/pjpk/T2_PK_11_REMAINING_EDITORIAL_STAGING_20261024.json",
    ROOT / "docs/pjpk/T2_PK_7_COMPLETE_RPH_EDITORIAL_STAGING_20261024.json",
]
REQUIRED = ("id", "year", "subject", "topic", "objective", "materials",
            "induction", "activities", "reinforcement", "closure", "assessment",
            "teacher_fields", "status", "production_ready")
LOCKS = ("textbook_verified",
         "rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified")
TEACHER = ("date", "day", "class", "time", "duration_minutes", "reflection")
CANDIDATE_IDS = {2249, 2250, 2251, 2344, 2345, 2346, 2347, 2348, 2349, 2350, 2354}
EDITORIAL_SP = {2232: ["8.1.1"], 2252: ["8.1.2"], 2351: ["7.1.1", "7.1.2", "7.1.3"],
                2352: ["8.1.1"], 2353: ["8.1.2"], 2355: ["9.1.1"],
                2356: ["9.1.2", "9.1.3"]}
EXPECTED_IDS = CANDIDATE_IDS | set(EDITORIAL_SP)
FOCUS_MATRIX = ROOT / "docs/pjpk/T2_PK_11_SP_EDITORIAL_FOCUS_MATRIX_20261024.json"
CHECKPOINT = ROOT / "docs/pjpk/T2_PK_18_EDITORIAL_QA_CHECKPOINT_20261024.json"
EXPECTED_FOCUS_SP = {
    2249: ["1.1.1", "1.1.3"], 2344: ["1.1.2"], 2250: ["1.2.1", "1.2.2"],
    2345: ["1.2.3"], 2251: ["2.1.1", "2.1.2"], 2346: ["2.1.3"],
    2347: ["3.1.1", "3.1.2", "3.1.3"],
    2348: ["4.1.1", "4.1.2", "4.1.3"],
    2349: ["5.1.1", "5.1.2", "5.1.3"],
    2350: ["6.1.1", "6.1.2", "6.1.3"], 2354: ["8.1.3"],
}

def audit():
    errors, records = [], []
    for path in FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("records")
        if not isinstance(rows, list):
            errors.append(f"{path.name}: records must be a list")
            continue
        records.extend(rows)
    matrix = json.loads(FOCUS_MATRIX.read_text(encoding="utf-8"))
    candidates = matrix.get("candidates", [])
    candidate_ids = [row.get("id") for row in candidates]
    if matrix.get("status") != "candidate_only_do_not_activate" or matrix.get("production_ready") is not False:
        errors.append("Candidate focus matrix release lock changed")
    if len(candidate_ids) != 11 or len(set(candidate_ids)) != 11 or set(candidate_ids) != CANDIDATE_IDS:
        errors.append("Candidate focus matrix identity mismatch")
    if any(row.get("sp") != EXPECTED_FOCUS_SP.get(row.get("id")) for row in candidates):
        errors.append("Candidate focus matrix SP coverage changed; editorial/source re-audit required")
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    if checkpoint.get("status") != "static_editorial_qa_pass_not_production_gate" or checkpoint.get("production_ready") != 0:
        errors.append("Editorial checkpoint release status changed")
    if checkpoint.get("checks", {}).get("total_records") != 18 or checkpoint.get("checks", {}).get("unique_ids") != 18:
        errors.append("Editorial checkpoint counts changed")
    documented_sources = {row.get("path"): row for row in checkpoint.get("source_files", [])}
    if set(documented_sources) != {str(path.relative_to(ROOT)) for path in FILES}:
        errors.append("Editorial checkpoint source inventory mismatch")
    for path in FILES:
        rel = str(path.relative_to(ROOT))
        raw = path.read_bytes()
        actual_sha = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + bytes([0]) + raw).hexdigest()
        recorded = documented_sources.get(rel, {})
        if recorded.get("blob_sha") != actual_sha:
            errors.append(f"{rel}: checkpoint source blob SHA stale")
        if recorded.get("count") != len(json.loads(raw)["records"]):
            errors.append(f"{rel}: checkpoint source count mismatch")
    ids = [r.get("id") for r in records]
    if len(records) != 18:
        errors.append(f"Expected 18 records, got {len(records)}")
    if len(set(ids)) != len(ids):
        errors.append("Duplicate IDs")
    if set(ids) != EXPECTED_IDS:
        errors.append(f"Unexpected/missing IDs: {sorted(set(ids) ^ EXPECTED_IDS)}")
    for r in records:
        ident = r.get("id", "?")
        for key in REQUIRED:
            if key not in r or r[key] is None or (isinstance(r[key], str) and not r[key].strip()):
                errors.append(f"{ident}: missing {key}")
        if r.get("year") != "Tahun 2" or r.get("subject") != "Pendidikan Kesihatan":
            errors.append(f"{ident}: unexpected subject/year")
        acts = r.get("activities")
        if not isinstance(acts, list) or len(acts) != 2 or any(
            not isinstance(a, dict) or not str(a.get("heading", "")).strip()
            or not str(a.get("body", "")).strip() for a in acts
        ):
            errors.append(f"{ident}: incomplete activity pair")
        fields = r.get("teacher_fields")
        if not isinstance(fields, dict) or any(k not in fields for k in TEACHER):
            errors.append(f"{ident}: teacher fields missing")
        if r.get("status") != "editorial_staging_only" or r.get("production_ready") is not False:
            errors.append(f"{ident}: unsafe release state")
        if any(r.get(k) is not False for k in LOCKS):
            errors.append(f"{ident}: verification lock not false")
        if r.get("sk_text_verified") is not True or r.get("sp_text_verified") is not True:
            errors.append(f"{ident}: DSKP verification incomplete")
        if r.get("sk") != str(r.get("sp", [""])[0]).rsplit(".", 1)[0]:
            errors.append(f"{ident}: SK/SP mismatch")
        if not isinstance(r.get("sp"), list) or not r["sp"]:
            errors.append(f"{ident}: SP mapping missing")
        elif ident in CANDIDATE_IDS and r["sp"] != EXPECTED_FOCUS_SP[ident]:
            errors.append(f"{ident}: candidate SP differs from DSKP focus mapping")
        elif ident in EDITORIAL_SP and r["sp"] != EDITORIAL_SP[ident]:
            errors.append(f"{ident}: editorial SP changed without source review")
    return errors, len(records), len(set(ids))

if __name__ == "__main__":
    errors, count, unique = audit()
    print(f"T2 PK editorial records: {count}; unique IDs: {unique}; errors: {len(errors)}")
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    if errors:
        raise SystemExit(1)
    print("PASS: static editorial checks only. RPT, source, bot runtime and A4 release gates remain blocked.")
