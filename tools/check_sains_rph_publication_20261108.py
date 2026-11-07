"""Independent read-only quality-release preflight for new authored Science RPH."""
from __future__ import annotations
import ast
import json
from pathlib import Path

from tools.audit_rph80_sains_first_20261107 import EXPECTED
from web.sains_rph_quality_release_gate_20261108 import approved_count

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"build/sains_rph_quality_release_20261108"
MAIN_LAUNCH=ROOT/"tools/run_telegram_with_curriculum_api.py"
STAGED_MODULES={
    "sains_y2_51_activities_draf_20261107",
    "sains_y3_rph_activity_preview_20261106",
    "sains_y4_79_activity_bank_draf_20261107",
    "sains_y6_84_activity_bank_draf_20261107",
}

def audit():
    source=MAIN_LAUNCH.read_text(encoding="utf-8")
    ast.parse(source,filename=str(MAIN_LAUNCH))
    if any(name in source for name in STAGED_MODULES):
        raise ValueError("Unapproved new Science bank referenced in production launcher")
    marker='if _sains_review_env.environ.get("CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW") == "1":'
    if marker not in source:
        raise ValueError("Year5 staging source is no longer guarded by opt-in")
    from web.sains_y5_83_staging_shared_runtime_20261108 import (
        STAGING_FLAG,STAGING_CONTEXT,ALLOWED_CONTEXT,PRODUCTION_RENDER_SERVICES,
    )
    if (STAGING_FLAG!="CIKGULAJU_SAINS_Y5_83_INTERNAL_REVIEW"
        or STAGING_CONTEXT!="CIKGULAJU_CURRICULUM_DEPLOYMENT"
        or ALLOWED_CONTEXT!="staging"
        or "srv-dbm5go8u01pc738f40cg" not in PRODUCTION_RENDER_SERVICES
        or "srv-dah3b8lbedkc738ugqt0" not in PRODUCTION_RENDER_SERVICES):
        raise ValueError("Year5 protected staging gate weakened")
    count=approved_count()
    if count>sum(EXPECTED.values()):
        raise ValueError("More Science approvals than authored lessons")
    return {
        "scope":"Sains Tahun 2–6",
        "new_source_total":sum(EXPECTED.values()),
        "source_count_per_year":{str(y):EXPECTED[y] for y in EXPECTED},
        "academically_signed_off":count,
        "not_yet_certified":sum(EXPECTED.values())-count,
        "minimum_release_quality_percent":80,
        "critical_quality_criteria":[
            "Official exact SK/SP",
            "Edition-correct textbook and RPT alignment",
            "Distinct teacher-pupil KPS/PBD, individual evidence and safety",
            "Physical one-page A4 Word/PDF",
            "Authenticated Telegram-Web parity and downloads",
            "Per-PdP reviewer signoff and identical source SHA-256",
        ],
        "new_science_public_sources_auto_activated":False,
        "existing_user_rph_paths_mutated":False,
        "all_noncertified_new_rph_are_hold":True,
        "requires_teacher_panitia_per_lesson":True,
        "decision":"HOLD_NEW_RPH_UNTIL_INDIVIDUAL_CERTIFICATION",
    }

def main():
    summary=audit()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"SAINS_342_PUBLIC_RELEASE_QUALITY_HOLD.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SAINS_QUALITY_PUBLICATION_GATE:",
          summary["academically_signed_off"],"/",
          summary["new_source_total"],"approved for new live source; "
          "existing live generation unchanged; fail-closed")

if __name__=="__main__":
    main()
