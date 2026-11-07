"""Repository-level triage for ALL CikguLaju RPH subjects.

This inventory is NOT a quality grade and NOT proof that a repository file is
served by the current Telegram/Web deployment. Run only against a staging
checkout; report missing/off-repository/DB-backed sources explicitly.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "rph80_all_subjects_20261107"
SUBJECTS = (
    "Sains", "Pendidikan Islam", "Matematik", "Bahasa Melayu",
    "Pendidikan Muzik", "Pendidikan Kesihatan", "Bahasa Arab",
    "Pendidikan Jasmani", "Reka Bentuk dan Teknologi", "Sejarah",
    "Pendidikan Seni Visual", "Pendidikan Moral", "Bahasa Inggeris",
)
PRIORITY = {subject: i for i, subject in enumerate(SUBJECTS)}
SOURCE = ROOT / "rph_standalone"
FIELDS = (
    "subjek", "source", "identity", "format", "source_lineage",
    "standard_code_present", "teacher_and_pupil_actions",
    "two_activities", "assessment_pbd", "closure", "book_reference",
    "draft_or_hold_marker", "structural_flags", "academic_quality_percent",
    "next_gate",
)

def subject_for_path(path: Path) -> str | None:
    s = str(path).lower().replace("\\", "/")
    if "pjpk" in s:
        if re.search(r"year[2-6]_pk|kesihatan", s):
            return "Pendidikan Kesihatan"
        if re.search(r"year[2-6]_pj|jasmani", s):
            return "Pendidikan Jasmani"
        return None
    clues = [
        ("english", "Bahasa Inggeris"),
        ("bahasa_arab", "Bahasa Arab"),
        ("pendidikan_moral", "Pendidikan Moral"),
        ("pendidikan_islam", "Pendidikan Islam"),
        ("pendidikan_muzik", "Pendidikan Muzik"),
        ("matematik", "Matematik"),
        ("bahasa_melayu", "Bahasa Melayu"),
        ("sejarah", "Sejarah"),
        ("sains", "Sains"),
        ("psv", "Pendidikan Seni Visual"),
        ("/rbt/", "Reka Bentuk dan Teknologi"),
    ]
    return next((label for token, label in clues if token in s), None)


def structural_clues(text: str) -> dict:
    t = str(text or "")
    lower = t.casefold()
    # Technical triage only: string presence does not verify actual SK/SP,
    # classroom suitability, page edition, or downloadable Word/PDF.
    return {
        "standard_code_present": bool(re.search(
            r"\b(?:sk|sp|ls|cs|learning standards?)\b", t, re.I)),
        "teacher_and_pupil_actions": bool(re.search(
            r"\b(?:guru|teacher)\b", t, re.I)) and bool(re.search(
            r"\b(?:murid|pupils?)\b", t, re.I)),
        "two_activities": bool(re.search(
            r"(?:aktiviti|activity)\s*1\b", t, re.I)) and bool(re.search(
            r"(?:aktiviti|activity)\s*2\b", t, re.I)),
        "assessment_pbd": any(x in lower for x in (
            "pbd", "pentaksiran", "penilaian", "assessment")),
        "closure": any(x in lower for x in ("penutup", "closure")),
        "book_reference": any(x in lower for x in (
            "buku teks", "student", "workbook", "sb p.", "wb p.", "tb p.")),
        "draft_or_hold_marker": any(x in lower for x in (
            "draf", "draft", "belum ready", "not ready", "hold")),
    }


def audit_markdown(path: Path, *, root: Path = ROOT) -> dict:
    text = path.read_text(encoding="utf-8")
    subject = subject_for_path(path)
    if not subject:
        raise ValueError("Unclassified RPH source " + str(path))
    checks = structural_clues(text)
    missing = [k for k, value in checks.items()
               if k != "draft_or_hold_marker" and not value]
    return {
        "subjek": subject,
        "source": str(path.relative_to(root)),
        "identity": path.stem,
        "format": "MARKDOWN",
        "source_lineage": "REPOSITORY_STAGING_NOT_VERIFIED_ACTIVE",
        **{k: str(v).upper() for k, v in checks.items()},
        "structural_flags": ";".join(missing),
        "academic_quality_percent": "",
        "next_gate": "CHECK_ACTIVE_SOURCE_DSKP_BOOK_PBD_WORD_PDF_AND_USER_FLOW",
    }


def audit_json(path: Path, *, root: Path = ROOT) -> list[dict]:
    subject = subject_for_path(path)
    if subject not in ("Sejarah", "Reka Bentuk dan Teknologi"):
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    lessons = raw if isinstance(raw, list) else (
        raw.get("lessons", raw.get("records", [])) if isinstance(raw, dict) else [])
    if not isinstance(lessons, list):
        return []
    rows = []
    for number, lesson in enumerate(lessons, 1):
        if not isinstance(lesson, dict):
            continue
        packed = " ".join(str(v) for v in lesson.values()
                          if isinstance(v, (str, int, float)))
        checks = structural_clues(packed)
        missing = [k for k, value in checks.items()
                   if k != "draft_or_hold_marker" and not value]
        rows.append({
            "subjek": subject,
            "source": str(path.relative_to(root)),
            "identity": str(lesson.get("pdp", lesson.get("id", number))),
            "format": "JSON_RECORD",
            "source_lineage": "REPOSITORY_STAGING_NOT_VERIFIED_ACTIVE",
            **{k: str(v).upper() for k, v in checks.items()},
            "structural_flags": ";".join(missing),
            "academic_quality_percent": "",
            "next_gate": "REVIEW_NESTED_ACTIVITIES_SOURCE_AND_NATIVE_RENDER",
        })
    return rows


def inventory(*, root: Path = ROOT) -> tuple[list[dict], dict]:
    source = root / "rph_standalone"
    rows = []
    if source.exists():
        for path in sorted(source.glob("**/lesson_[0-9][0-9][0-9].md")):
            if subject_for_path(path):
                rows.append(audit_markdown(path, root=root))
        for path in sorted(source.glob("**/*.json")):
            if subject_for_path(path) in (
                    "Sejarah", "Reka Bentuk dan Teknologi") and (
                    "rph" in path.name.lower()):
                rows.extend(audit_json(path, root=root))
    counts = Counter(r["subjek"] for r in rows)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["subjek"]].append(row)
    report = {
        "date": "2026-11-07",
        "source": "STAGING_REPO_FILES_ONLY_NOT_LIVE",
        "status": "TECHNICAL_TRIAGE_NOT_QUALITY_SCORE",
        "quality_scores_verified": 0,
        "quality_score_percent": None,
        "subjects": {
            name: {
                "scan_count": counts[name],
                "source_coverage": "PARTIAL_NOT_ACTIVE_VERIFIED" if counts[name] else "NO_SCANNABLE_INDIVIDUAL_RECORDS",
                "structural_flags_count": sum(bool(x["structural_flags"]) for x in grouped[name]),
                "quality_percent": None,
                "review_status": "HOLD_UNTIL_ACTUAL_ACTIVE_SOURCE_AUDIT",
            } for name in SUBJECTS
        },
        "note": (
            "Missing records in this branch are NOT proof the subject is absent "
            "from the runtime DB, Drive or another staging branch. None of these "
            "string checks can certify 80% pedagogy or active deployment."),
        "non_destructive": True,
    }
    return sorted(rows, key=lambda r: (
        PRIORITY[r["subjek"]], r["source"], r["identity"])), report


def main():
    rows, report = inventory()
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "RPH_SOURCE_TRIAGE_NOT_QUALITY.csv").open(
            "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "SUBJECT_COVERAGE_HOLD.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("RPH80_REPO_TRIAGE:", len(rows), "source records,",
          len(SUBJECTS), "subjects listed; 0 academic quality scores certified, HOLD")


if __name__ == "__main__":
    main()
