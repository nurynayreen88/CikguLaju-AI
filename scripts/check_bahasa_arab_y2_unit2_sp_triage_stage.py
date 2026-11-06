#!/usr/bin/env python3
"""Read-only, non-release check for Bahasa Arab Tahun2 Unit2 source-code triage."""
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
AUDIT = BASE / "audits/bahasa_arab_y2_unit2_pdp013_028_sp_mismatch_triage_20261106.json"
SOURCE = BASE / "audits/bahasa_arab_y2_unit2_pdp013_028_visual_audit_20261106.json"
CSV = BASE / "rpt_2027/bahasa_arab/year2_unit2_pdp013_028_DRAF.csv"
RPH = BASE / "rph_standalone/bahasa_arab/year2"

def main():
    doc = json.loads(AUDIT.read_text(encoding="utf-8"))
    upstream = json.loads(SOURCE.read_text(encoding="utf-8"))
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert doc["year"] == 2 and doc["unit"] == 2
    assert doc["candidate_total"] == 16 and doc["ready_count"] == 0
    assert doc["high_priority_count"] == 8 and doc["additional_review_count"] == 5
    assert doc["release_authorized"] is False
    assert all(doc[key] is False for key in ("production_db_touched","telegram_live_touched","web_live_touched"))
    assert len(doc["records"]) == len(upstream["items"]) == len(rows) == 16
    high,review=set(),set()
    ids=set()
    for item,orig,row in zip(doc["records"], upstream["items"], rows):
        n=item["pdp"]
        assert n not in ids
        ids.add(n)
        assert n==orig["pdp"]==row["pdp"]
        assert item["existing_candidate_sp"]==orig["sp_candidate"]==row["sp"]
        assert item["source_printed_page"]==orig["printed_page"]
        assert item["source_pdf_page_1based"]==orig["pdf_page_1_based"]==orig["printed_page"]+12
        assert not item["ready"] and not item["teacher_approved"]
        assert row["ready"]=="FALSE" and row["kelulusan_individu"]=="FALSE"
        assert (RPH/f"lesson_{n}.md").is_file()
        status=item["audit_status"]
        if status=="HIGH_PRIORITY_CODE_OR_SKILL_MISMATCH":
            high.add(n)
            assert item["issue"]
        elif status=="REQUIRES_FULL_PAGE_PEDAGOGIC_CHECK":
            review.add(n)
            assert item["issue"]
        else:
            assert status=="NO_HIGH_PRIORITY_FINDING_IN_SCREENING"
    assert ids=={f"{i:03d}" for i in range(13,29)}
    assert high=={"014","016","019","020","023","024","027","028"}
    assert review=={"018","021","022","025","026"}
    print("PASS: 16 Year2 Unit2 source candidates, 8 high priority + 5 review, 0 approved, no duplicate/orphan.")
    print("BLOCKED: printed SP verification / manual RPH correction before annual RPT and runtime release.")

if __name__=="__main__":
    main()
