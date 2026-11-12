"""Build a REVIEW-ONLY 56-PDF RPT package with 23 Week01 + 5 Music fixes.

Never writes to the Web's published PDF catalog, manifest, or database.
Caller must pass a separate checkout of the existing Web production branch.
Source is the independently tested RPT staging tree; annual SK/SP checks and
teacher timetable authorization remain separate release gates.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory

import fitz

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.week1_owner_plan_20261110 import allocate_rbt_weeks
from scripts.build_rpt_2027_remaining_four_subjects_staging import (
    build_all as build_remaining, week1_proposed_records,
    bm_records, pi_records, arabic_records,
)
from scripts.build_rpt_2027_standard_preview import (
    build_all as build_standard, rbt_records,
)
from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    build_all as build_science, source_records,
)

SUBJECT_YEARS = {
    "bahasa_melayu": range(2, 7),
    "pendidikan_islam": range(2, 7),
    "bahasa_arab": range(2, 7),
    "rbt": range(4, 7),
    "sains": range(2, 7),
}
SUBJECT_LABELS = {
    "bahasa_melayu": "BAHASA MELAYU",
    "pendidikan_islam": "PENDIDIKAN ISLAM",
    "bahasa_arab": "BAHASA ARAB",
    "rbt": "REKA BENTUK DAN TEKNOLOGI",
    "sains": "SAINS",
    "muzik": "PENDIDIKAN MUZIK",
}
TARGET = {f"{sub}:{y}" for sub, years in SUBJECT_YEARS.items() for y in years}
assert len(TARGET) == 23
MUSIC_TARGET = {f"muzik:{year}" for year in range(2, 7)}
REPLACEMENT_TARGET = TARGET | MUSIC_TARGET
assert len(MUSIC_TARGET) == 5 and len(REPLACEMENT_TARGET) == 28
COVER_KEYS = ("RANCANGAN PENGAJARAN TAHUNAN 2027",
              "LOGO SEKOLAH", "NAMA SEKOLAH", "NAMA GURU")
EXPECTED_FIRST = {"bahasa_melayu": 3, "pendidikan_islam": 2,
                  "bahasa_arab": 1, "rbt": 1}
WEEK_REGEX = re.compile(r"(?<![A-Za-z0-9])M\s*01(?![0-9])", re.I)

# These are **printed developer qualifiers**, not the legitimate curricular
# expression "menulis draf karangan". Scan ALL 56 packaged teacher PDFs,
# including all baseline copies preserved in the 56-file candidate.
TEACHER_PDF_REVIEW_MARKERS = {
    "DRAFT_PARENTHESES": re.compile(r"\(\s*draf\s*\)", re.I),
    "DRAFT_RPT_STATUS": re.compile(
        r"(?i)\b(?:RPT|kandungan\s+buku)\b[^.\n]{0,80}\bmasih\s+draf\b"
    ),
    "BM_UNVERIFIED_CROSSWALK": re.compile(
        r"(?i)\bHOLD\s+(?:padanan|tajuk|SP|rujukan|kod)\b"
    ),
    "INTERNAL_STAGING_STATUS": re.compile(
        r"(?i)(?:\bHOLD\s*:|\bSTAGING\b|\bJANGAN\s+MERGE\b|"
        r"\bBUKAN\s+UNTUK\s+GURU\b|\bBELUM\s+READY\b)"
    ),
    "MISSING_MUSIC_NOTATION": re.compile(
        r"(?i)\bSimbol\s*/\s*skor\s+tidak\s+penuh\s+dalam\s+teks\b"
    ),
    "EDITOR_SOURCE_NUMBERING_NOTE": re.compile(
        r"(?i)\bDSKP\s+T[2-6]\s+cetak\s+SK\b[^.]{0,150}\bsusun\s+RPT\b"
    ),
}


def teacher_pdf_review_markers(pages):
    """Flag obvious internal wording without deleting original lesson data.

    The resulting evidence is a release hold, NOT an automatic text-edit pass.
    In particular, never erase valid SK/SP words such as 'menulis draf'.
    """
    findings = []
    for page_no, value in enumerate(pages, 1):
        text = re.sub(r"\s+", " ", value)
        for kind, pattern in TEACHER_PDF_REVIEW_MARKERS.items():
            matches = list(pattern.finditer(text))
            if matches:
                findings.append({"page": page_no, "rule": kind,
                                 "count": len(matches),
                                 "example": matches[0].group(0)})
    return findings


HIDDEN_AUDIT_NOTES = re.compile(
    # A pedagogical instruction such as "menulis draf karangan" is valid.
    # Reject release-status labels, not the legitimate word "draf" in DSKP.
    r"(?i)(?:\bDRAF(?=\s*[:/_-]|\s+(?:SEMAKAN|UNTUK\s+SEMAKAN|TERKAWAL))|"
    r"\bSTATUS\s*[:：]?\s*DRAF\b|DRAF\s+PKJR|MASIH\s+DRAF|"
    r"CALON\s+BUKAN\s+VISUAL|BELUM\s+READY|\bSTAGING\b|SEBELUM READY|JANGAN MERGE|"
    r"\bdeveloper\b|ACADEMIC SIGNOFF|REKOD DITAHAN|\bHOLD\s*:)"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_text(path: Path):
    with fitz.open(path) as d:
        return "\n".join(p.get_text("text") for p in d)


def sourced_week_assertions():
    """Fail closed on changed curriculum identity or source week-one counts."""
    first = {}
    for subject, reader in (("bahasa_melayu", bm_records),
                            ("pendidikan_islam", pi_records),
                            ("bahasa_arab", arabic_records)):
        for year in range(2, 7):
            old = reader(year)
            candidate = week1_proposed_records(subject, year, reader)
            count = sum(r.get("week") == "M01" for r in candidate)
            if count != EXPECTED_FIRST[subject]:
                raise ValueError(f"{subject}:{year}: wrong Week01 allocation")
            for before, after in zip(old, candidate):
                for key in ("id", "sk", "sp", "unit", "topic", "sk_display", "sp_display"):
                    if before.get(key) != after.get(key):
                        raise ValueError(f"{subject}:{year}: mutated {key}")
            first[f"{subject}:{year}"] = count
    for year in range(4, 7):
        old = rbt_records(year)
        candidate = allocate_rbt_weeks(old, year=year)
        if candidate[0]["week"] != "M01" or len(candidate) != 32:
            raise ValueError("RBT Week01 missing")
        for before, after in zip(old, candidate):
            if any(before.get(k) != after.get(k) for k in ("id", "sk", "sp", "unit", "topic")):
                raise ValueError("RBT SK/SP/topic changed")
        first[f"rbt:{year}"] = 1
    science = source_records()
    for year in range(2, 7):
        rows = science[year]
        if not rows or rows[0]["week"] != "M01" or rows[0]["id"] != "001":
            raise ValueError("Sains Week01 not source-backed")
        first[f"sains:{year}"] = sum(r.get("week") == "M01" for r in rows)
    if set(first) != TARGET:
        raise ValueError("Incomplete targeted Week01 inventory")
    return first


def build_preview_files(destination: Path):
    stage = destination / "source_pdfs"
    remaining = build_remaining(stage / "bm_pi_arabic_music")
    standard = build_standard(stage / "psv_rbt_moral")
    science = build_science(stage / "sains")
    if len(remaining) != 20 or len(standard) != 13 or len(science) != 5:
        raise ValueError("Staging source year sets incomplete")
    paths = {f"{sub}:{year}": Path(path)
             for sub, year, _, path in remaining + standard}
    paths.update({f"sains:{year}": Path(path)
                  for year, count, approved, path in science})
    if set(paths) & REPLACEMENT_TARGET != REPLACEMENT_TARGET:
        raise ValueError("Missing proposed Week01/Music PDF")
    return paths


def candidate_package(web_root: Path, output: Path):
    baseline = Path(web_root) / "rpt_2027" / "web_2027_pdfs"
    original = json.loads((baseline / "manifest.json").read_text("utf-8"))
    if len(original["files"]) != 56 or REPLACEMENT_TARGET - set(original["files"]):
        raise ValueError("Unexpected published RPT PDF manifest")
    if original.get("academic_final_approved") is not False:
        raise ValueError("Never promote unapproved files under an approved manifest")
    calendar = load_calendar_weeks()
    if (calendar["A"]["M01"], calendar["B"]["M01"]) != (
        ("2027-01-04", "2027-01-07"), ("2027-01-04", "2027-01-08")
    ):
        raise ValueError("Week 01 calendar changed")
    first = sourced_week_assertions()
    with TemporaryDirectory(prefix="cikgulaju_rpt2027_preview_") as tmp:
        source_paths = build_preview_files(Path(tmp))
        package = Path(output) / "rpt_2027" / "web_2027_pdfs"
        package.mkdir(parents=True, exist_ok=True)
        candidate = deepcopy(original)
        candidate["source"] = "Week01+Music staging: 23 Week01 PDFs, 5 Music clean PDFs, 28 original PDFs retained"
        candidate["academic_final_approved"] = False
        # Source Web catalog may expose DRAFT PDFs. This independent package
        # is not approved and must NEVER inherit the live-catalog-ready flag.
        candidate["source_ready_for_web_catalog"] = original["ready_for_web_catalog"]
        candidate["ready_for_web_catalog"] = False
        candidate["release_candidate_only"] = True
        candidate["requires_teacher_calendar_and_academic_signoff"] = True
        observations = []
        for identity, src in sorted(original["files"].items()):
            old = baseline / src["path"]
            old_data = old.read_bytes()
            if sha256(old_data) != src["sha256"] or len(old_data) != src["bytes"]:
                raise ValueError(f"{identity}: Web baseline SHA/bytes invalid")
            target = package / src["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if identity not in REPLACEMENT_TARGET:
                shutil.copyfile(old, target)
                entry = dict(src)
            else:
                sub, year_string = identity.split(":")
                year = int(year_string)
                preview = source_paths[identity]
                # Remove internal *metadata* from the teacher artifact, but
                # retain original teaching table and internal review ledger.
                with fitz.open(preview) as doc:
                    meta = dict(doc.metadata or {})
                    meta["title"] = f"RPT {SUBJECT_LABELS[sub]} Tahun {year} 2027"
                    meta["subject"] = "Rancangan Pengajaran Tahunan 2027"
                    meta["keywords"] = ""
                    doc.set_metadata(meta)
                    doc.save(target, garbage=3, deflate=True)
                with fitz.open(target) as d:
                    page_count = len(d)
                    if page_count < 2 or any(
                        p.rect.width <= p.rect.height for p in d
                    ):
                        raise ValueError(f"{identity}: not 2+ A4-landscape pages")
                    cover = d[0].get_text()
                    if any(k not in cover for k in COVER_KEYS):
                        raise ValueError(f"{identity}: Web cover slots missing")
                    teaching = "\n".join(page.get_text("text") for page in list(d)[1:])
                    found = HIDDEN_AUDIT_NOTES.search(teaching)
                    if found:
                        snippet = teaching[max(0, found.start()-65):found.end()+65]
                        raise ValueError(f"{identity}: internal author status in teacher PDF: {snippet!r}")
                    if identity in TARGET and sub not in ("pendidikan_islam", "bahasa_arab") and not WEEK_REGEX.search(teaching):
                        raise ValueError(f"{identity}: Week01 not printed")
                    if sub in ("bahasa_arab", "pendidikan_islam") and not re.search(r"2027", teaching):
                        raise ValueError(f"{identity}: RTL table or dates missing")
                    if any("DRAF" in str(x).upper() for x in d.metadata.values()
                           if isinstance(x, str)):
                        raise ValueError(f"{identity}: DRAF PDF metadata")
                    entry = dict(src)
                    entry["pages"] = page_count
                data = target.read_bytes()
                entry["sha256"], entry["bytes"] = sha256(data), len(data)
                entry["status"] = src["status"]  # internal release flag unchanged
            candidate["files"][identity] = entry
            data = target.read_bytes()
            if sha256(data) != entry["sha256"] or len(data) != entry["bytes"]:
                raise ValueError(f"{identity}: packaged PDF SHA mismatch")
            with fitz.open(target) as doc:
                if len(doc) != entry["pages"]:
                    raise ValueError(f"{identity}: packaged PDF page count mismatch")
            observation = {"subject_year": identity,
                           "changed": identity in REPLACEMENT_TARGET,
                           "change_reason": (
                               "week01_allocation" if identity in TARGET else
                               "music_teacher_text_cleanup" if identity in MUSIC_TARGET else
                               "original_bytes_retained"),
                           "old_pages": src["pages"], "new_pages": entry["pages"],
                           "old_sha256": src["sha256"], "new_sha256": entry["sha256"]}
            # Scan all 56 teacher-facing PDF bodies, including retained originals.
            # A clean layout is required; this NEVER grants academic signoff.
            with fitz.open(target) as check:
                printed = [page.get_text("text") or "" for page in list(check)[1:]]
            leaks = teacher_pdf_review_markers(printed)
            observation["teacher_pdf_review_marker_count"] = sum(
                item["count"] for item in leaks)
            if leaks:
                observation["teacher_pdf_review_markers"] = leaks[:10]
                raise ValueError(f"{identity}: printed developer notes remain in candidate PDF")
            if identity in MUSIC_TARGET:
                with fitz.open(old) as baseline_pdf:
                    old_printed = [page.get_text("text") or "" for page in list(baseline_pdf)[1:]]
                old_leaks = teacher_pdf_review_markers(old_printed)
                observation["baseline_music_editorial_note_count"] = sum(
                    item["count"] for item in old_leaks)
                if not old_leaks:
                    raise ValueError(f"{identity}: expected old Music editor notes absent, inspect source drift")
            if identity in TARGET:
                observation["week01_sourced_pdp"] = first[identity]
                old_text = pdf_text(old)
                new_text = pdf_text(target)
                observation["text_similarity_diagnostic"] = round(
                    SequenceMatcher(None, old_text.splitlines(), new_text.splitlines(), autojunk=False).ratio(), 4)
                observation["week01_extracted_ltr"] = bool(WEEK_REGEX.search(new_text))
            observations.append(observation)
        if sum(item["changed"] for item in observations) != 28:
            raise ValueError("Only exactly 23 Week01 + 5 Music PDFs may change")
        if any(item["old_sha256"] != item["new_sha256"]
               for item in observations if not item["changed"]):
            raise ValueError("One of the other 28 unchanged PDF bytes changed")
        candidate["pages"] = sum(e["pages"] for e in candidate["files"].values())
        leaked = [r for r in observations if r["teacher_pdf_review_marker_count"]]
        music_before = {r["subject_year"]: r["baseline_music_editorial_note_count"]
                        for r in observations if r["subject_year"] in MUSIC_TARGET}
        if set(music_before) != MUSIC_TARGET or any(n <= 0 for n in music_before.values()):
            raise ValueError("All five Music legacy PDFs must have proven notes to remove")
        candidate["printed_internal_note_finding_count"] = sum(
            r["teacher_pdf_review_marker_count"] for r in leaked)
        candidate["printed_internal_note_affected_files"] = [
            r["subject_year"] for r in leaked]
        candidate["teacher_release_blocked"] = True
        candidate["music_legacy_editorial_notes_removed"] = sum(music_before.values())
        candidate["music_teacher_note_affected_source_files"] = list(sorted(MUSIC_TARGET))
        candidate["candidate_replaced_files"] = 28
        candidate["candidate_unchanged_files"] = 28
        (package / "manifest.json").write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", "utf-8")
        report = {
            "status": "REVIEW_ONLY_NOT_PRODUCTION_RELEASE",
            "source_year1_transition_changed": False,
            "published_web_files_modified": False,
            "academic_signoff": False,
            "ready_for_web_catalog": False,
            "teacher_release_blocked": True,
            "printed_internal_note_affected_files": [
                r["subject_year"] for r in leaked],
            "printed_internal_note_finding_count": sum(
                r["teacher_pdf_review_marker_count"] for r in leaked),
            "music_legacy_editorial_notes_removed": sum(music_before.values()),
            "music_legacy_editorial_counts": music_before,
            "total": 56,
            "target_week01_fixes": 23,
            "target_music_teacher_pdf_fixes": 5,
            "changed": 28,
            "unchanged": 28,
            "source_week01_counts": first,
            "files": observations,
        }
        (Path(output) / "week01_candidate_review.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
        print("WEEK01_CANDIDATE_PACKAGE_56", json.dumps(
            {"changed": 28, "unchanged": 28,
             "total_pages": candidate["pages"],
             "week01_counts": first}, ensure_ascii=False, sort_keys=True),
            flush=True)
        return report


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--web-checkout", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    candidate_package(args.web_checkout, args.output)
