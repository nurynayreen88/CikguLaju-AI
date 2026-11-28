"""Auditable RPT 2027 release gaps; a passing audit does not approve release.

This is the single staging-only blocker report for 56 structured RPT previews.
It never reads users or writes to any DB, Telegram/Web, payment, or live output.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from scripts.build_rpt_2027_standard_preview import rbt_records
from scripts.build_rpt_2027_remaining_four_subjects_staging import arabic_records, pi_records
from rpt_2027.common.sains_kssr2017_edition_release_guard import edition_conflict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "staging/rpt_2027_seragam_2026/release_gap_audit_20261107_DRAF.json"
ARAB_EXPECTED = {2: 60, 3: 60, 4: 58, 5: 60, 6: 60}
PI_EXPECTED = {2: 112, 3: 147, 4: 151, 5: 143, 6: 143}
SAINS_SOURCE = {2: 51, 3: 45, 4: 79, 5: 83, 6: 84}

def build_audit():
    arab_years = {}
    islam_years = {}
    rbt_years = {}
    for year in range(2, 7):
        rows = arabic_records(year)
        if len(rows) != ARAB_EXPECTED[year]:
            raise ValueError(f"Arabic T{year} source count changed")
        arab_years[str(year)] = {
            "pdp": len(rows),
            # A PDF-derived candidate sentence can now be displayed in staging.
            # It is NOT a full official DSKP statement until academic signoff.
            # Use explicit signoff flags, never display-placeholder wording.
            "not_full_sk": sum(r.get("source_sk_full_text_signoff") is not True for r in rows),
            "not_full_sp": sum(r.get("source_sp_dskp_text_signoff") is not True for r in rows),
            "with_candidate_sp_text": sum(
                "belum dipadankan" not in r["sp_display"].lower()
                and r.get("source_sp_dskp_text_signoff") is False for r in rows
            ),
            "without_calendar_week": sum(not r.get("week") for r in rows),
            "with_source_sp_pdf_page": sum(isinstance(r.get("source_sp_dskp_pdf_page"), int) for r in rows),
        }
        p = pi_records(year)
        if len(p) != PI_EXPECTED[year]:
            raise ValueError(f"PI T{year} source count changed")
        held = [r["id"] for r in p if r["source_held"]]
        sourced=[r for r in p if r["source_held"] and r.get("held_source_proposal")]
        if len(sourced)!=len(held):
            raise ValueError(f"PI T{year} held source recovery coverage changed")
        islam_years[str(year)] = {
            "source_records": len(p),
            "withheld_count": len(held),
            "withheld_ids": held,
            "held_rpt_provisional_source_found": len(sourced),
            "held_rpt_source_conflicts": sum("KONFLIK" in r["topic"] for r in sourced),
            "held_rpt_sourced_week_candidates": sum(bool(r["week"]) for r in sourced),
        }
    for year in (4, 5, 6):
        rows = rbt_records(year)
        if len(rows) != 32:
            raise ValueError(f"RBT T{year} PdP count changed")
        rbt_years[str(year)] = {
            "pdp": len(rows),
            "without_sourced_week": sum(not r["week"] for r in rows),
            "without_sourced_a_dates": sum(not r["a_start"] or not r["a_end"] for r in rows),
            "without_sourced_b_dates": sum(not r["b_start"] or not r["b_end"] for r in rows),
        }
    arab_total = sum(v["pdp"] for v in arab_years.values())
    held_total = sum(v["withheld_count"] for v in islam_years.values())
    rbt_total = sum(v["pdp"] for v in rbt_years.values())
    source = json.loads((ROOT / "audits/rbt_t4_t6_rpt2026_23_sp_week_block_source_evidence_20261107.json").read_text("utf-8"))
    if source.get("status") != "SOURCE_2026_WEEK_BLOCK_EVIDENCE_ONLY_NOT_2027_SCHEDULE" or source["listed_year_sp_codes"] != 23:
        raise ValueError("RBT calendar-reference source changed or was prematurely approved")
    kssr2017=edition_conflict()
    result = {
        "date": "2026-11-07",
        "status": "STAGING_ONLY_BLOCKED_NOT_RELEASE_READY",
        "is_release_ready": False,
        "does_not_validate_runtime": True,
        "scope": "56 RPT Year2-6 formatted previews; not KP2027 Year1/secondary",
        "arabic": {
            "years": arab_years,
            "pdp_total": arab_total,
            "without_full_sk_text": sum(v["not_full_sk"] for v in arab_years.values()),
            # Legacy output keys retained for downstream QA; both counts now
            # mean *without academically approved full DSKP wording*.
            "without_full_sp_text": sum(v["not_full_sp"] for v in arab_years.values()),
            "candidate_sp_text_present_not_approved": sum(
                v["with_candidate_sp_text"] for v in arab_years.values()
            ),
            "without_sourced_calendar_week": sum(v["without_calendar_week"] for v in arab_years.values()),
            "source_sp_page_anchors": sum(v["with_source_sp_pdf_page"] for v in arab_years.values()),
            "reason": "117 unique SP codes linked to original PDF pages. Source-derived SP sentence candidates are present but have no independent academic/visual signoff; SK thematic openings are not full approved SK statements.",
        },
        "pendidikan_islam": {
            "years": islam_years,
            "total_source_records": sum(v["source_records"] for v in islam_years.values()),
            "withheld_count": held_total,
            "reason": "All six held V5 RPH have RPT-source candidates: five optional tasmi blocks without official SK/SP and one contradictory Ibadah SK; all six remain withheld.",
        },
        "rbt": {
            "years": rbt_years,
            "total_pdp": rbt_total,
            "without_sourced_2027_week": sum(v["without_sourced_week"] for v in rbt_years.values()),
            "source_2026_sp_block_entries": source["listed_year_sp_codes"],
            "reason": "2026 RPT sources group several SP across several weeks. Its dates are not school-specific 2027 slots.",
        },
        "sains": {
            "source_snapshot_v2582_pdp": SAINS_SOURCE,
            "partial_pdp": sum(SAINS_SOURCE.values()),
            "snapshot_status": "LEGACY_INTERNAL_CODES_NOT_CURRENT_KSSR_VERIFIED",
            "kssr2017_original_dskp_edition_conflict": True,
            "verified_flag_from_database_is_insufficient": True,
            "external_evidence_conflicts": len(kssr2017["conflict_samples"]),
            "years_requiring_full_code_text_remap": kssr2017["requires_full_reverification_years"],
            "source_audit_reference": "audits/sains_rpt2027_kssr2017_legacy_code_conflict_20261107.json",
            "ready_for_web_telegram": False,
            "reason": "342 v25.82 historical PdP and 422 v26 internal SP are NOT verified against independent KPM KSSR Semakan 2017. External documents show code/topic conflicts in Years4–6; 80 legacy code gaps and 10 drafted proposals are forensic only.",
        },
        "remaining_releases": [
            "Independent DSKP full Arabic sentence transcription/visual signoff",
            "Six independent PI lesson/source recovery or expressly omitted with approved plan",
            "Sains Years4–6: replace legacy curriculum code mapping with independent original KPM KSSR2017 DSKP before topic/RPH/scheduling audit",
            "RBT subject week allocations based on school teaching frequency/cuti and 2026 source rhythm",
            "All subject page/activity signoff and A/B state holiday/teacher timetable check",
            "Authenticated Telegram/Web same source and end-to-end Word/PDF download test",
        ],
        "protect_production": True,
        "change_users_db": False,
    }
    if (arab_total != 298 or result["arabic"]["without_full_sk_text"] != 298
        or result["arabic"]["without_full_sp_text"] != 298
        or result["arabic"]["source_sp_page_anchors"] != 298
        or held_total != 6 or rbt_total != 96
        or result["rbt"]["without_sourced_2027_week"] != 96
        or result["sains"]["partial_pdp"] != 342):
        raise ValueError("Release-gap counts differ from independently validated source state")
    return result

def write_audit(destination=OUT):
    info = build_audit()
    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output

if __name__ == "__main__":
    path = write_audit()
    print(f"RPT2027 RELEASE_GATE=BLOCKED (source-faithful): {path}")
