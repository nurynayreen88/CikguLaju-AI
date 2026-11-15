"""Block publication of legacy Sains v25.82/v26.00 SP code labels as KSSR2017.

Original PDFs were checked against independent KPM DSKP, not merely DB verified=1.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/"audits/sains_rpt2027_kssr2017_legacy_code_conflict_20261107.json"

def edition_conflict():
    audit=json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if audit.get("status")!="CRITICAL_KSSR2017_CURRICULUM_EDITION_MISMATCH_STAGING_HOLD":
        raise ValueError("Sains curriculum edition audit missing or not in HOLD state")
    samples=audit.get("conflict_samples")
    if not isinstance(samples,list) or len(samples)<6:
        raise ValueError("Sains year4-6 external DSKP mismatches not traceable")
    checks={(r["year"],r["legacy_sk"]):r for r in samples}
    if checks[(4,"3.3")]["kssr2017_sk"]!="2.3" or checks[(6,"3.2")]["kssr2017_sk"]!="2.2":
        raise ValueError("Known grade-year source code discrepancy was altered")
    if audit.get("academic_release_ready") is not False or audit.get("ready_for_web_telegram") is not False:
        raise ValueError("Legacy Sains source must remain blocked")
    return audit

def require_verified_kssr2017_sains(year:int):
    source=edition_conflict()
    if year in source["requires_full_reverification_years"]:
        raise ValueError(f"Sains Year {year} legacy v26 code differs from KSSR2017 source. Reconcile all SP and RPH first.")
    raise ValueError("Sains 2027 RPT academic signoff not independently evidenced for this year")

