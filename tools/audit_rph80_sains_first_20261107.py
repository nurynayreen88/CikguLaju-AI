"""Read-only RPH 80% quality audit queue — start with Sains, 7 Nov 2026.

Works only on the existing staging Sains 342-PdP inventory after its source
CSV is generated. No Telegram/Web/DB writes, no automatic release approvals.
A technical pass is NEVER interpreted as an academic quality pass.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "rph80_sains_20261107"
EXPECTED = {2: 51, 3: 45, 4: 79, 5: 83, 6: 84}
WEIGHTS = {
    "sk_sp": 25,
    "buku_teks_rpt": 25,
    "aktiviti_pbd": 25,
    "word_pdf": 15,
    "telegram_web": 10,
}
# Do not call these percentages "quality" while academic evidence is missing.
BASELINE_EVIDENCE = {
    "science_pdp_identified": 342,
    "year3_standalone_draft_word_pdf_ci": 45,
    "other_years_missing_individual_standalone_qa": 297,
    "academically_signed_off": 0,
}
PRIORITY = {6: 0, 5: 1, 4: 2, 2: 3, 3: 4}
COLS = (
    "priority", "tahun", "pdp_code", "pdp_number", "unit", "sp", "tajuk",
    "source_status", "quality_percent", "dskp_check", "textbook_check",
    "activities_pbd_check", "word_pdf_check", "telegram_web_check",
    "teacher_signoff", "blocking_issues", "next_action"
)


def grade_from_evidence(scores, evidence):
    """Return an academic score only when all five criteria have signed proof.

    Scores are never inferred from file existence, a GitHub CI green tick,
    a 'DRAF' label, a SOW token or past percentage estimates.
    """
    if not isinstance(scores, dict) or not isinstance(evidence, dict):
        return None
    required = ("reviewer", "review_date", "dskp", "textbook_pages",
                "specific_activities_pbd", "rendered_word_pdf", "runtime_parity")
    if any(not str(evidence.get(k) or "").strip() for k in required):
        return None
    if not evidence.get("review_is_for_exact_source_sha"):
        return None
    if set(scores) != set(WEIGHTS):
        return None
    for item, weight in WEIGHTS.items():
        score = scores[item]
        if type(score) is not int or score < 0 or score > weight:
            return None
    # A numeric total cannot waive critical curriculum, pedagogy or source failures.
    # Every dimension must meet its minimum before this source can be certified.
    minima={"sk_sp":20, "buku_teks_rpt":20, "aktiviti_pbd":20,
            "word_pdf":10, "telegram_web":8}
    if any(scores[item] < minimum for item,minimum in minima.items()):
        return None
    return sum(scores.values())


def build_queue(rows, generated=None):
    """Build the per-PdP edit/review queue; preserve all original SK/SP/title."""
    if not isinstance(rows, list) or len(rows) != 342:
        raise ValueError("Expected immutable 342 source PdP rows")
    generated = generated or {}
    seen = set()
    counts = Counter()
    results = []
    for row in rows:
        y = row["tahun"]
        code = row["pdp_code"]
        if type(y) is not int or y not in EXPECTED:
            raise ValueError("Unexpected grade")
        if (not re.fullmatch(r"SCI-Y[2-6]-PDP-\d{3}", code)
                or code != f"SCI-Y{y}-PDP-{int(row['pdp_number']):03d}"):
            raise ValueError("Unexpected source code " + str(code))
        if code in seen or row["keputusan"] != "HOLD":
            raise ValueError("Duplicate/approved source in HOLD ledger: " + code)
        if not row["unit"] or not row["sp"] or not row["tajuk"]:
            raise ValueError("Incomplete source identity: " + code)
        seen.add(code)
        counts[y] += 1
        has_staged_doc = code in generated.get(y, set())
        if has_staged_doc:
            status = "STAGING_STANDALONE_DOCX_PDF_A4_PASS__ACADEMIC_HOLD"
            action = ("Sahkan Buku Teks asal secara visual, audit tugasan guru/murid "
                      "dan PBD, dapatkan semakan akademik, kemudian uji akses Telegram-Web")
        elif y == 3:
            status = "EXISTING_45_DRAFTS_NEED_INDIVIDUAL_ACADEMIC_QA"
            action = ("Semak tugasan guru/murid, bukti PBD dan 23 sempadan PdP; "
                      "sahkan halaman buku secara visual dan uji Word/PDF serta Web")
        elif y == 6:
            status = "NO_INDIVIDUALLY_AUDITED_STANDALONE_RPH"
            action = ("Sahkan DSKP asal Tahun 6 dan edisi Buku Teks dahulu; "
                      "bina RPH khusus SP, KPS, aktiviti dan PBD; uji A4")
        elif y == 4:
            status = "NO_INDIVIDUALLY_AUDITED_STANDALONE_RPH"
            action = ("Buka buku teks asal/edisi tepat secara visual; "
                      "bina RPH khusus SP, KPS, aktiviti dan PBD; uji A4")
        else:
            status = "NO_INDIVIDUALLY_AUDITED_STANDALONE_RPH"
            action = ("Sahkan halaman sebenar buku teks dan SP; bina RPH khusus "
                      "tanpa pengulangan aktiviti generik, uji A4 dan akses sebenar")
        results.append({
            "priority": PRIORITY[y],
            "tahun": y,
            "pdp_code": code,
            "pdp_number": row["pdp_number"],
            "unit": row["unit"],
            "sp": row["sp"],
            "tajuk": row["tajuk"],
            "source_status": status,
            "quality_percent": "",  # deliberately NOT measured yet
            "dskp_check": "TOKEN_ONLY" if y != 6 else "MIRROR_ONLY",
            "textbook_check": "VISUAL_PENDING",
            "activities_pbd_check": ("SOURCE_SPECIFIC_DRAFT_ACADEMIC_QA_PENDING"
                if has_staged_doc else "DRAFT_YEAR3" if y == 3 else "UNVERIFIED"),
            "word_pdf_check": ("WORD_AND_PDF_SINGLE_A4_STAGING_PASS"
                if has_staged_doc else "YEAR3_45_CI_ONLY" if y == 3 else "UNVERIFIED"),
            "telegram_web_check": "NOT_E2E_TESTED",
            "teacher_signoff": "MISSING",
            "blocking_issues": row["isu"],
            "next_action": action,
        })
    if dict(counts) != EXPECTED:
        raise ValueError("PdP coverage changed or year missing")
    if sum(r["tahun"] != 3 for r in results) != 297:
        raise ValueError("Wrong number of records requiring standalone RPH")
    results.sort(key=lambda r: (r["priority"], int(r["pdp_number"])))
    return results


def validated_staging_drafts():
    """Claim only verified CI-generated Word/PDF sources from the exact staging run.

    Year 3 remains prior-stage source with separate CI checks. New Year2/4/5/6
    files must have manifest + pagination evidence and an intact source set.
    """
    specifications = [
        (2, 51, ROOT/"build/sains_y2_51_rph_DRAF_20261107",
         "RPH_Y2_51_MANIFEST_DRAF.csv", "WORD_PRINT_PAGINATION_QA.json",
         "one_page", "pdp_code", "SAINS_T2_PDP_"),
        (4, 79, ROOT/"build/sains_y4_79_rph_DRAF_20261107",
         "SAINS_Y4_79_MANIFEST_DRAF.csv", "WORD_PRINT_QA.json",
         "one_page_pass", "pdp_code", "SAINS_T4_PDP_"),
        (5, 83, ROOT/"build/sains_y5_83_rph_DRAF_20261107",
         "SAINS_Y5_83_MANIFEST_DRAF.csv", "WORD_PRINT_QA.json",
         "one_page_pass", "pdp_code", "SAINS_T5_PDP_"),
        (6, 84, ROOT/"build/sains_y6_84_rph_DRAF_20261107",
         "SAINS_Y6_84_MANIFEST_DRAF.csv", "WORD_PRINT_QA.json",
         "one_page_pass", "pdp_code", "SAINS_T6_PDP_"),
    ]
    validated={}
    for year, count, folder, ledger_name, qa_name, pass_key, code_key, stem in specifications:
        ledger=folder/ledger_name
        qa_path=folder/qa_name
        if not ledger.is_file() or not qa_path.is_file():
            raise RuntimeError(f"Year{year} draft manifest/Word print QA is missing")
        with ledger.open(encoding="utf-8-sig",newline="") as file:
            rows=list(csv.DictReader(file))
        codes={r[code_key] for r in rows}
        expected_codes={f"SCI-Y{year}-PDP-{i:03d}" for i in range(1,count+1)}
        if len(rows)!=count or codes!=expected_codes:
            raise RuntimeError(f"Year{year} manifest is incomplete or duplicated")
        for i in range(1,count+1):
            for ext in (".docx",".pdf",".md"):
                if not (folder/(stem+f"{i:03d}_DRAF"+ext)).is_file():
                    raise RuntimeError(f"Year{year} staging RPH file missing {i} {ext}")
        qa=json.loads(qa_path.read_text(encoding="utf-8"))
        if qa.get("year")!=year or qa.get(pass_key)!=count or qa.get("overflow"):
            raise RuntimeError(f"Year{year} print QA failed or is unproven")
        validated[year]=codes
    return validated


def main():
    # Generated from the staged v25.82 immutable source, not a production DB.
    from tools.audit_sains_342_pdp_release_gate_20261106 import analyze
    rows, source = analyze()
    generated=validated_staging_drafts()
    queue = build_queue(rows, generated=generated)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "SAINS_342_QUALITY_REVIEW_QUEUE.csv").open(
            "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLS)
        writer.writeheader()
        writer.writerows(queue)
    summary = {
        "date": "2026-11-07",
        "scope": "SAINS_Y2_Y6_STAGING_SOURCE_NOT_PRODUCTION",
        "priority_order_years": [6, 5, 4, 2, 3],
        "rubric_percent": WEIGHTS,
        "target_quality_percent": 80,
        "quality_scores_verified": 0,
        "quality_score_percent": None,
        "unverified_quality_must_not_be_assigned": True,
        "reviewed_source_ids": len(queue),
        "year_counts": {str(k): EXPECTED[k] for k in EXPECTED},
        "existing_year3_draft": 45,
        "new_year2_word_pdf_a4_draft": len(generated[2]),
        "new_year4_word_pdf_a4_draft": len(generated[4]),
        "new_year5_word_pdf_a4_draft": len(generated[5]),
        "new_year6_word_pdf_a4_draft": len(generated[6]),
        "total_year2_to_year6_staging_draft": (
            45+len(generated[2])+len(generated[4])+len(generated[5])+len(generated[6])
        ),
        "standalone_drafts_not_yet_built_year6": 0,
        "all_year2_to_year6_academic_signoff_missing": 342,
        "historical_original_297_standalone_unverified": 297,
        "standalone_not_built": 0,
        "academic_ready": 0,
        "year1": "OUT_OF_SCOPE_KP2027_ALAM_DAN_MANUSIA",
        "decision": "HOLD",
        "source_release_decision": source["decision"],
        "required_for_80": [
            "Per-PdP exact DSKP and textbook-page check",
            "Specific teacher and pupil actions, science process skills and individual PBD",
            "Native one-page A4 Word and PDF visual smoke tests",
            "Actual authenticated Telegram and Web source-parity tests",
            "Human-reviewed rubric, evidence and per-lesson sign-off",
        ],
        "no_db_or_runtime_write": True,
    }
    (OUT / "SUMMARY_UNSCORED_HOLD.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("SAINS_RPH80_STAGING: 342 source PdP; Y2=51 Y3=45 Y4=79 Y5=83 "
          "Y6=84 technical A4 DRAF; 342/342 staged, "
          "0 academic quality percentages certified; HOLD")


if __name__ == "__main__":
    main()
