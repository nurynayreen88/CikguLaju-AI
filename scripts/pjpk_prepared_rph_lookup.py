"""Fail-closed prepared PJPK RPH lookup; no application hook or DB mutation.

A prepared RPH can only be retrieved for delivery when the evidence overlay,
structured record and caller's verified ready row all agree. Current T5 entries
are deliberately blocked until all source/runtime/A4 approvals are recorded.
"""
from scripts.pjpk_t5_complete_rph_audit import audit, OVERLAY_PATH
import csv

REQUIRED = ("dskp_verified", "textbook_verified", "rpt_exact_slot_verified",
            "rph_runtime_verified", "a4_review_verified", "production_ready")

def prepared_rph(entry_id, verified_ready_row=None):
    if not isinstance(entry_id, int) or isinstance(entry_id, bool):
        return None
    if not isinstance(verified_ready_row, dict) or verified_ready_row.get("id") != entry_id:
        return None
    if not all(verified_ready_row.get(key) == 1 for key in
               ("content_verified", "sequence_verified", "schedule_verified")):
        return None
    rows, errors = audit()
    if errors:
        return None
    with OVERLAY_PATH.open(newline="", encoding="utf-8-sig") as fh:
        source = {int(row["entry_id"]): row for row in csv.DictReader(fh)}
    record = next((row for row in rows if row["id"] == entry_id), None)
    evidence = source.get(entry_id)
    if record is None or evidence is None:
        return None
    if not all(evidence.get(key) == "1" for key in REQUIRED):
        return None
    if record.get("production_ready") is not True:
        return None
    if any(record.get(key) is not True for key in
           ("rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified")):
        return None
    standards = verified_ready_row.get("_std")
    if not isinstance(standards, list) or not standards:
        return None
    verified_sk = {str(item.get("standard_code", "")).strip() for item in standards
                   if isinstance(item, dict) and item.get("standard_type") == "SK"
                   and item.get("verified") in (1, True)}
    verified_sp = {str(item.get("standard_code", "")).strip() for item in standards
                   if isinstance(item, dict) and item.get("standard_type") == "SP"
                   and item.get("verified") in (1, True)}
    if record["sk"] not in verified_sk or set(record["sp"]) != verified_sp:
        return None
    if (record.get("year") != verified_ready_row.get("year_label")
        or record.get("subject") != verified_ready_row.get("subject")
        or record.get("topic") != verified_ready_row.get("topic")):
        return None
    return record
