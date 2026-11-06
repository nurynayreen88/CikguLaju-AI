"""Measured quality gate for *text/structure evidence* in Music 2027 staging.

A 90% pass here is not 90% verified pedagogical accuracy, score/music approval,
audio licensing, real runtime parity, or authorization to deploy.
No network/DB access, files changed only in optional /tmp report.
"""
import csv
import json
import os
from pathlib import Path

from native_layout_preview_staging import build_staging_preview

ROOT = Path(__file__).resolve().parent
YEARS = range(2, 7)
COUNT = 35
TARGET = 0.90


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit():
    printed_codes = json.loads(
        (ROOT / "DSKP_SP_CODE_PRESENCE_175_20261106.json").read_text(encoding="utf-8")
    )
    overlay = json.loads(
        (ROOT / "SUCCESS_CRITERIA_DRAFT_20261106.json").read_text(encoding="utf-8")
    )
    crosswalk = {r["pdp_id"]: r for r in printed_codes["records"]}
    require(len(crosswalk) == 175, "DSKP code records must cover exactly 175 PdP")
    require(len(overlay) == 81, "Review all 81 draft success-criteria overlays")

    per_year = {}
    covered = set()
    criteria = set()
    rendered_preview = set()
    source_code_present = set()
    unofficial = set()
    score_visual = set()
    zero_candidate_days = set()
    overlay_used = set()
    all_ids = set()
    rpt_count = 0
    for year in YEARS:
        folder = ROOT / f"year{year}"
        manifest = json.loads((folder / "pdp_manifest.json").read_text(encoding="utf-8"))
        rows = manifest["pdps"]
        require(len(rows) == COUNT, f"Year {year}: missing PdP")
        for field in ("textbook_verified", "audio_verified", "rph_word_pdf_verified"):
            require(manifest[field] is False, f"Year {year}: premature release flag {field}")
        per_year[year] = {"rph": len(rows), "book_text_or_page_checked": 0}
        with (folder / f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            rpt_rows = list(csv.DictReader(stream))
        require(len(rpt_rows) == COUNT, f"Year {year}: RPT row count mismatch")
        rpt_ids = {r["PdP ID"] for r in rpt_rows}
        require(len(rpt_ids) == COUNT, f"Year {year}: duplicate RPT IDs")
        rpt_count += 1
        for pdp, row in enumerate(rows, 1):
            ident = f"MZ-Y{year}-{pdp:02d}"
            require(row["pdp"] == pdp and row["pdp_id"] == ident, f"Identity mismatch {ident}")
            require(ident not in all_ids and ident in rpt_ids, f"Missing or duplicate RPT {ident}")
            all_ids.add(ident)
            preview = build_staging_preview(ROOT, year, pdp)
            require(preview["source_pdp_id"] == ident, f"Preview mismatch {ident}")
            require(preview["approved_for_live"] is False, f"Premature approval {ident}")
            phases = preview["layout"]["phases"]
            require(len(phases) == 3, f"RPH phase structure missing {ident}")
            for key in ("induction", "act1", "act2", "assessment", "closure", "materials", "objective"):
                require(bool(preview["phase_text"].get(key, "").strip()), f"Missing {key} {ident}")
            rendered_preview.add(ident)
            header = {item["label"]: item["value"] for item in preview["layout"]["header"]}
            require(header["KRITERIA KEJAYAAN"].strip() not in ("", "—"), f"No criterion {ident}")
            criteria.add(ident)
            if ident in overlay:
                overlay_used.add(ident)
                require(
                    overlay[ident]["approval"] == "CIKGULAJU_EDITORIAL_TEXT_REVIEW_PASSED",
                    f"Unreviewed text criterion {ident}",
                )
                require("EDITORIAL_TEXT_REVIEW_PASSED_SCORE_PENDING" in preview["warnings"],
                        f"Lost score pending warning {ident}")
            dskp = crosswalk.get(ident)
            require(dskp is not None and dskp["manifest_sp"] == row["sp"],
                    f"Unverified printed code link {ident}")
            require(dskp["official_approval"] is False, f"Unfounded KPM approval {ident}")
            require(not dskp["sp_not_found_in_source"], f"SP missing in DSKP text {ident}")
            source_code_present.add(ident)
            has_book = (
                row.get("source_book_text_crosscheck") is True
                or row.get("source_book_content_page_checked") is True
            )
            if has_book:
                covered.add(ident)
                per_year[year]["book_text_or_page_checked"] += 1
            if row.get("pdp_kind") == "CADANGAN_PENGUKUHAN_BUKAN_PROJEK_RASMI":
                unofficial.add(ident)
                require(not has_book and row.get("page") is None,
                        f"Nonofficial unit incorrectly claims book page {ident}")
            warning = "TEXTBOOK_NOT_FULLY_CROSSCHECKED_OR_NONOFFICIAL"
            require((warning in preview["warnings"]) is (not has_book),
                    f"Incorrect teacher-facing book evidence warning {ident}")
            if row.get("source_book_score_visual_checked") is True:
                score_visual.add(ident)
            require(row.get("source_book_audio_file_verified", False) is False,
                    f"Audio activated without rights {ident}")
            if row.get("rpt2027_day_audit"):
                zero_candidate_days.add(ident)

    require(len(all_ids) == 175, "Scope mismatch")
    require(len(covered) == 167, "Source check regression or count drift")
    require(len(unofficial) == 8, "Nonofficial reinforcement count drift")
    require(len(overlay_used) == 81, "Success-criteria overlay used incorrectly")
    require(
        zero_candidate_days == {
            f"MZ-Y{year}-{pdp:02d}" for year in YEARS for pdp in (6, 19)
        },
        "Flexible calendar slots drifted",
    )
    require(score_visual == {"MZ-Y4-21", "MZ-Y4-24"},
            "Visual score review evidence differs from documented 2-PdP scope")
    metrics = {
        "source_text_or_page_check_coverage": len(covered) / 175,
        "rph_preview_structure_coverage": len(rendered_preview) / 175,
        "criterion_present_and_text_reviewed_coverage": len(criteria) / 175,
        "printed_dskp_code_presence_coverage": len(source_code_present) / 175,
        "rpt_2027_coverage": rpt_count / 5,
    }
    pass_90 = all(v >= TARGET for v in metrics.values())
    report = {
        "scope": "MUSIC_2027_STAGING_TEXT_AND_STRUCTURE_ONLY",
        "threshold": TARGET,
        "threshold_met": pass_90,
        "metric_ratios": metrics,
        "per_year": per_year,
        "rph": 175,
        "rpt": 5,
        "text_or_page_source_checked": len(covered),
        "nonofficial_reinforcement": len(unofficial),
        "criteria_editorial_overlays_text_only": len(overlay_used),
        "score_visual_reviewed_only": len(score_visual),
        "audio_files_rights_verified": 0,
        "teacher_dates_zero_candidate_school_days": len(zero_candidate_days),
        "full_runtime_telegram_web_parity_verified": False,
        "approved_for_live": False,
        "final_ready": False,
        "limitations": [
            "Crosscheck is partial text/page evidence, not 90% pedagogical validity.",
            "Only 2 music-score PdP have documented visual inspection.",
            "No rights to distribute official audio confirmed.",
            "Word/PDF native-function smoke tests are separate from runtime Telegram/Web.",
            "No KPM sign-off or teacher-specific day assignment is implied.",
        ],
    }
    output = Path(os.getenv("MUSIC_QUALITY_REPORT", "/tmp/music_quality_90_text_report.json"))
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    require(pass_90, "Staging text/structure quality coverage has fallen below 90%")
    return report


if __name__ == "__main__":
    audit()
