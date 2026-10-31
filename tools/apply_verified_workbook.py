"""Replace Assessment/PBD activities with verified English Workbook tasks.

Dry-run by default. Use --apply only after checking the review CSV and backups.
Other RPH sections are preserved verbatim.
"""
import argparse
import csv
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english"
ASSESSMENT = re.compile(r"(?m)^## (?:Assessment / PBD|PBD / Reinforcement)[^\n]*\n")
PAGE_REF = re.compile(r"\b(?:Workbook|Activity Book)\s*(?:p\.|page)\s*\d+", re.I)


def verified_rows(csv_file):
    seen = set()
    with Path(csv_file).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"year", "lesson", "verified_workbook_page",
                    "verified_activity", "source_evidence"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Review CSV missing required columns")
        for index, row in enumerate(reader, 2):
            year, lesson = int(row["year"]), int(row["lesson"])
            if year not in (2, 3) or lesson not in range(1, 161):
                raise ValueError(f"Row {index}: invalid year/lesson")
            if (year, lesson) in seen:
                raise ValueError(f"Row {index}: duplicate lesson")
            seen.add((year, lesson))
            page = (row["verified_workbook_page"] or "").strip()
            activity = (row["verified_activity"] or "").strip()
            evidence = (row["source_evidence"] or "").strip()
            if not (page or activity or evidence):
                continue
            if not (page.isdigit() and int(page) > 0 and activity and evidence):
                raise ValueError(f"Row {index}: incomplete verified mapping")
            if not re.fullmatch(r"[A-Za-z0-9 ,./()\-]+", activity):
                raise ValueError(f"Row {index}: unsafe activity label")
            yield year, lesson, int(page), activity


def prepare(source, page, activity):
    if re.search(r"\b(?:Workbook|Activity Book)\b", source, re.I):
        return None, "existing_workbook_reference"
    match = ASSESSMENT.search(source)
    if not match:
        return None, "assessment_heading_missing"
    end = re.search(r"(?m)^## |^\*\*QA", source[match.end():])
    section_end = match.end() + end.start() if end else len(source)
    replacement = (
        f"**Teacher:** Direct pupils to Workbook p.{page}, {activity}; "
        "explain the task, check individual responses and record achievement "
        "against the lesson objectives.\n"
        f"**Pupils:** Complete Workbook p.{page}, {activity}.\n\n"
    )
    return source[:match.end()] + replacement + source[section_end:], "ready"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("review_csv")
    parser.add_argument("--apply", action="store_true", help="Write changes after review; default is dry-run")
    args = parser.parse_args()
    changes = []
    missing_files = []
    for year, lesson, page, activity in verified_rows(args.review_csv):
        file = ROOT / f"year{year}" / f"lesson_{lesson:03d}.md"
        if not file.is_file():
            print(f"SKIP {year}/{lesson}: missing_file")
            missing_files.append(file)
            continue
        original = file.read_text(encoding="utf-8")
        updated, reason = prepare(original, page, activity)
        if updated is None:
            print(f"SKIP {year}/{lesson}: {reason}")
            continue
        changes.append((file, updated, hashlib.sha256(original.encode('utf-8')).hexdigest()))
        print(f"{'APPLY' if args.apply else 'DRY-RUN'} {year}/{lesson}: Workbook p.{page}, {activity}")
    if args.apply and not changes:
        raise RuntimeError("No verified Workbook changes eligible; refusing empty apply")
    if args.apply:
        if missing_files:
            raise RuntimeError(f"Missing {len(missing_files)} lesson file(s); no files written")
        for file, updated, expected_hash in changes:
            original = file.read_text(encoding="utf-8")
            current_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
            if current_hash != expected_hash:
                raise RuntimeError(f"Lesson changed since review; no files written: {file}")
        for file, updated, _ in changes:
            file.write_text(updated, encoding="utf-8")
    print(f"Eligible changes: {len(changes)}; written: {len(changes) if args.apply else 0}")


if __name__ == "__main__":
    main()
