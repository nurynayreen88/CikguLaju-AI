"""Read-only pre-deployment audit for Matematik Tahun 4 standalone RPH.

This tool NEVER writes to a database, overwrites RPH, or loads the bot runtime.
Usage: python tools/check_matematik_t4_package.py path/to/package.zip
Return status 2 for unsafe/incomplete packages (not production READY).
"""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path

from docx import Document

EXPECTED_IDS = {f"{n:02d}" for n in range(1, 82) if n != 11} | {"11A", "11B", "11C"}
FILE_PATTERN = re.compile(r"^RPH_T4_(\d{2}|11[A-C])_PRA_READY\.docx$")
REQUIRED_SECTIONS = ("set induksi", "aktiviti", "pentaksiran", "penutup", "bbm")
A4_MM = (210, 297)


def audit_zip(path: str | Path) -> dict:
    """Return a JSON-serializable audit; input archive stays unchanged."""
    source = Path(path)
    names: dict[str, str] = {}
    findings = []
    counts = {
        "documents": 0,
        "a4": 0,
        "preready_marked": 0,
        "rpt2026_mentioned": 0,
        "rpt2027_pending": 0,
        "activity_book_pending": 0,
        "required_sections": 0,
    }
    with zipfile.ZipFile(source) as archive:
        for entry in archive.infolist():
            # Reading Word files only; do not extract archive paths.
            filename = Path(entry.filename).name
            match = FILE_PATTERN.fullmatch(filename)
            if not match or entry.is_dir():
                continue
            lesson_id = match.group(1)
            if lesson_id in names:
                findings.append(f"Duplicate RPH ID {lesson_id}")
                continue
            names[lesson_id] = filename
            try:
                data = archive.read(entry)
                if len(data) > 2_000_000:
                    raise ValueError("Unexpectedly large DOCX")
                doc = Document(io.BytesIO(data))
            except Exception as error:
                findings.append(f"Unreadable Word file {filename}: {type(error).__name__}")
                continue
            counts["documents"] += 1
            lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            body = "\n".join(lines)
            lower = body.casefold()
            if "pra-ready" in lower:
                counts["preready_marked"] += 1
            else:
                findings.append(f"Missing review status in {filename}")
            if "rpt 2026" in lower or "rpt matematik tahun 4 2026" in lower:
                counts["rpt2026_mentioned"] += 1
            if "2027" in lower and any(x in lower for x in ("belum disahkan", "belum diluluskan", "belum dijadualkan")):
                counts["rpt2027_pending"] += 1
            if "buku aktiviti belum disahkan" in lower:
                counts["activity_book_pending"] += 1
            if all(section in lower for section in REQUIRED_SECTIONS):
                counts["required_sections"] += 1
            else:
                findings.append(f"Incomplete core RPH sections: {filename}")
            if doc.sections:
                sec = doc.sections[0]
                width_mm, height_mm = sec.page_width.mm, sec.page_height.mm
                if abs(width_mm - A4_MM[0]) <= 2 and abs(height_mm - A4_MM[1]) <= 2:
                    counts["a4"] += 1
                else:
                    findings.append(f"Not A4: {filename}")
            else:
                findings.append(f"No page section: {filename}")
    missing = sorted(EXPECTED_IDS - set(names))
    unexpected = sorted(set(names) - EXPECTED_IDS)
    if missing:
        findings.append(f"Missing RPH IDs: {', '.join(missing)}")
    if unexpected:
        findings.append(f"Unexpected RPH IDs: {', '.join(unexpected)}")
    if counts["documents"] != 83:
        findings.append(f"Found {counts['documents']} readable RPH; expected 83")
    if counts["preready_marked"]:
        findings.append(f"{counts['preready_marked']} RPH marked PRA-READY, not approved")
    if counts["rpt2027_pending"]:
        findings.append(f"{counts['rpt2027_pending']} RPH have outstanding 2027 mapping/approval notes")
    if counts["activity_book_pending"]:
        findings.append(f"{counts['activity_book_pending']} RPH have unverified activity-book notes")
    return {
        "subject": "Matematik",
        "year": 4,
        "expected_ids": 83,
        "counts": counts,
        "findings": findings,
        "release_allowed": not findings,
        "production_mutations": False,
    }


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Usage: python tools/check_matematik_t4_package.py package.zip", file=sys.stderr)
        return 64
    try:
        result = audit_zip(args[0])
    except (FileNotFoundError, OSError, zipfile.BadZipFile, ValueError) as error:
        print(json.dumps({"release_allowed": False, "error": str(error)}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["release_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())