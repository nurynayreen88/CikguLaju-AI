"""Validate the non-destructive T5 PK evidence overlay. Does not modify original inventory/DB.

Run: python scripts/pjpk_t5_evidence_overlay.py docs/pjpk/T5_PK_3_VERIFIED_EVIDENCE_OVERLAY_20261024.csv
"""
import csv
import sys

EXPECTED = {"2259": ("6.1", {"6.1.1", "6.1.2"}, "88-89"),
            "2260": ("7.1", {"7.1.1", "7.1.2", "7.1.3"}, "90-92"),
            "2261": ("8.1", {"8.1.1", "8.1.2", "8.1.3"}, "96-100")}
REQUIRED = {"entry_id", "year_label", "subject", "dskp_sk", "dskp_sp",
            "verified_textbook_printed_pages", "dskp_verified", "textbook_verified",
            "rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified",
            "production_ready"}

def audit(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = REQUIRED - set(reader.fieldnames or ())
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        rows = list(reader)
    errors = []
    ids = [r["entry_id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate entry_id")
    if set(ids) != set(EXPECTED):
        errors.append("Expected exactly the three verified T5 PK IDs")
    for r in rows:
        ident = r["entry_id"]
        if ident not in EXPECTED:
            continue
        sk, sp, pages = EXPECTED[ident]
        if (r["year_label"], r["subject"]) != ("Tahun 5", "Pendidikan Kesihatan"):
            errors.append(f"{ident}: wrong year/subject")
        if r["dskp_sk"] != sk or set(r["dskp_sp"].split(";")) != sp:
            errors.append(f"{ident}: DSKP mismatch")
        if r["verified_textbook_printed_pages"] != pages:
            errors.append(f"{ident}: textbook page mismatch")
        flags = ("dskp_verified", "textbook_verified", "rpt_exact_slot_verified",
                 "rph_runtime_verified", "a4_review_verified", "production_ready")
        if any(r[k] not in {"0", "1"} for k in flags):
            errors.append(f"{ident}: invalid gate flag")
            continue
        if r["dskp_verified"] != "1" or r["textbook_verified"] != "1":
            errors.append(f"{ident}: missing verified primary source")
        if r["production_ready"] == "1" and any(r[k] != "1" for k in flags[:-1]):
            errors.append(f"{ident}: premature production promotion")
    return rows, errors

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/pjpk_t5_evidence_overlay.py OVERLAY.csv")
    rows, errors = audit(sys.argv[1])
    print(f"Evidence rows: {len(rows)}; production-ready: {sum(r['production_ready'] == '1' for r in rows)}")
    for error in errors:
        print("BLOCK:", error, file=sys.stderr)
    if errors:
        raise SystemExit(1)
    if not all(r["production_ready"] == "1" for r in rows):
        print("BLOCK: RPT/runtime/A4 release gates pending", file=sys.stderr)
        raise SystemExit(2)
    print("Evidence overlay gate passed; teacher review and deployment approval remain separate.")
